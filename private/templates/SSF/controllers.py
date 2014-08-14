# -*- coding: utf-8 -*-

try:
    import json # try stdlib (Python 2.6)
except ImportError:
    try:
        import simplejson as json # try external module
    except:
        import gluon.contrib.simplejson as json # fallback to pure-Python module

from os import path

from gluon import current, URL
from gluon.html import *
from gluon.storage import Storage

from s3 import S3FilterForm, S3CustomController, S3OptionsFilter

THEME = "SSF"

# =============================================================================
class index(S3CustomController):
    """ Custom Home Page """

    def __call__(self):

        response = current.response
        settings = current.deployment_settings
        request = current.request
        s3 = response.s3
        db = current.db
        s3db = current.s3db
        T = current.T

        output = {}
        output["title"] = response.title = current.deployment_settings.get_system_name()

        view = path.join(current.request.folder, "private", "templates",
                         THEME, "views", "index.html")
        try:
            # Pass view as file not str to work in compiled mode
            response.view = open(view, "rb")
        except IOError:
            from gluon.http import HTTP
            raise HTTP(404, "Unable to open Custom View: %s" % view)

        project_url = URL(c="project", f="location", extension="geojson")
        project_url = "%s?~.project_id$sector.name=Deployment" % project_url
        contributor_url = URL(c="pr", f="person", extension="geojson")

        # Set the marker
        mtable = s3db.gis_marker
        query = (mtable.name == "sunflower") | (mtable.name == "contributor")
        markers = db(query).select(mtable.name,
                                   mtable.image,
                                   mtable.height,
                                   mtable.width,
                                   cache=s3db.cache,
                                   limitby=(0, 2)
                                   )

        project_marker = None
        contributor_marker = None

        for marker in markers:
            if marker.name == "sunflower":
                project_marker = marker
            if marker.name == "contributor":
                contributor_marker = marker

        layers = [{"name"      : T("Deployments"),
                   "id"        : "deployments",
                   "tablename" : "project_location",
                   "url"       : project_url,
                   "active"    : True,
                   "marker"    : project_marker,
                   },
                  {"name"      : T("Contributors"),
                   "id"        : "contributors",
                   "tablename" : "pr_address",
                   "url"       : contributor_url,
                   "active"    : True,
                   "marker"    : contributor_marker,
                   },
                  ]

        output["map"] = current.gis.show_map(collapsed = True,
                                             feature_resources = layers,
                                             legend="float",
                                             )

        s3.scripts.append("http://www.google.com/jsapi?key=notsupplied-wizard")
        feed_control = "".join(('''
function LoadFeeds(){
 var feeds=[
  {title:'Tasks',
   url:\'''', settings.get_base_public_url(), '''/''', request.application, '''/project/task.rss?task.status=2,3,4,11'
  },
  {title:'Tickets',
   url:'http://eden.sahanafoundation.org/timeline?ticket=on&changeset=on&milestone=on&max=50&daysback=90&format=rss'
  },
  {title:'Wiki',
   url:'http://eden.sahanafoundation.org/timeline?changeset=on&milestone=on&wiki=on&max=50&daysback=90&format=rss'
  },
  {title:'Github',
   url:'https://github.com/flavour/eden/commits/master.atom'
  },
  {title:'Twitter',
   url:'http://www.rssitfor.me/getrss?name=@SahanaFOSS'
  },
  {title:'Blog',
   url:'http://sahanafoundation.org/feed/?cat=33,39'
  }
 ];

 var feedControl = new google.feeds.FeedControl();

 // Add feeds.
 for(i=0; i<feeds.length; i++){
  feedControl.addFeed(feeds[i].url, feeds[i].title);
 }

 feedControl.setNumEntries(5);

 feedControl.draw(document.getElementById("feed-control"),
 {
  drawMethod: 'content',
  drawMode : google.feeds.FeedControl.DRAW_MODE_TABBED
 });

 // Initialise feed-url input
 $('#feed-url').attr('href', feeds[0].url);
 $('#feed-url').attr('title', feeds[0].title);

 // Show feed-url
 $('.gfc-tabHeader').click(feeds, function(){
  activeTab = $('.gfc-tabhActive').html();
  for(i=0; i<feeds.length; i++){
   if(feeds[i].title == activeTab){
    $('#feed-url').attr('href', feeds[i].url);
    $('#feed-url').attr('title', feeds[i].title);
    break;
   }
  }
 });
}
google.load('feeds','1')
google.setOnLoadCallback(LoadFeeds)'''))
        s3.js_global.append(feed_control)

        return output

# =============================================================================
class subscriptions(S3CustomController):
    """ Custom page to manage subscriptions """

    # -------------------------------------------------------------------------
    def __call__(self):
        """ Main entry point, configuration """

        T = current.T
        s3db = current.s3db

        # Must be logged in
        auth = current.auth
        if not auth.s3_logged_in():
            auth.permission.fail()

        # Available resources
        resources = [dict(resource="project_task",
                          url="project/task",
                          label=T("Updates")),
                     ]

        # Filter widgets
        # @note: subscription manager has no resource context, so
        #        must configure fixed options or lookup resources
        #        for filter widgets which need it.

        filters = [S3OptionsFilter("task_project.project_id",
                                   label = "Project",
                                   resource = "project_project",
                                   _name = "project-filter",
                                   options = s3db.project_task_project_opts(),
                                   ),
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

            subscription["filters"] = form.request_vars \
                                      .get("subscription-filters", None)

            subscription["notify_on"] = listify(formvars.notify_on)
            subscription["frequency"] = formvars.frequency

            subscription["method"] = ["EMAIL"]

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
