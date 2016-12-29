# -*- coding: utf-8 -*-

from datetime import datetime, timedelta

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

from s3 import FS, S3CustomController, S3FilterForm, S3DateFilter, S3LocationFilter, S3OptionsFilter, s3_str

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
                              # @ToDo: Make the filter update timestamp on refresh in the client side
                              "filter"    : "~.info.expires__gt=%s&~.external__ne=True" % request.utcnow,
                              # We activate in callback after ensuring URL is updated for current filter status
                              "active"    : False,
                              }]

        _map = current.gis.show_map(callback='''S3.search.s3map()''',
                                    catalogue_layers=True,
                                    collapsed=True,
                                    feature_resources=feature_resources,
                                    save=False,
                                    search=True,
                                    toolbar=True,
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
        resource.add_filter(FS("info.expires") >= request.utcnow)
        # Only show locally generated Alerts
        resource.add_filter(FS("external") != True)
        # Change representation
        resource.table.status.represent = None
        list_id = "cap_alert_datalist"
        list_fields = ["msg_type",
                       "info.headline",
                       "area.name",
                       #"info.description",
                       "info.sender_name",
                       "info.priority",
                       "status",
                       "scope",
                       "info.event_type_id",
                       "info.severity",
                       "info.certainty",
                       "info.urgency",
                       "sent",
                       ]
        # Order with most recent Alert first
        orderby = "cap_alert.sent desc"
        datalist, numrows, ids = resource.datalist(fields = list_fields,
                                                   #start = None,
                                                   limit = None,
                                                   list_id = list_id,
                                                   orderby = orderby,
                                                   layout = s3db.cap_alert_list_layout
                                                   )
        if numrows == 0:
            current.response.s3.crud_strings["cap_alert"].msg_no_match = T("No Current Alerts match these filters.")

        ajax_url = URL(c="cap", f=fn, args="datalist.dl",
                       vars={"list_id": list_id,
                             "info.expires__gt": request.utcnow,
                             "~.approved_by__ne": None,
                             "~.external__ne": True})
        #@ToDo: Implement pagination properly
        output[list_id] = datalist.html(ajaxurl = ajax_url,
                                        pagesize = 0,
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
        # Truncate body
        #from s3 import s3_trunk8
        #s3_trunk8(lines=8)

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

        # Must be logged in
        auth = current.auth
        if not auth.s3_logged_in():
            auth.permission.fail()

        has_role = auth.s3_has_role
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
                                   options = self._options("event_type_id"),
                                   widget = "multiselect",
                                   multiple = False,
                                   resource = "cap_info",
                                   _name = "event-filter",
                                   ),
                   S3OptionsFilter("priority",
                                   label = T("Priority"),
                                   options = self._options("priority"),
                                   widget = "multiselect",
                                   resource = "cap_info",
                                   _name = "priority-filter",
                                   ),
                   #S3LocationFilter("location_id",
                   #                 label = T("Location(s)"),
                   #                 resource = "cap_area_location",
                   #                 options = self._options("location_id"),
                   #                 _name = "location-filter",
                   #                 ),
                   ]
        cap_languages = current.deployment_settings.get_cap_languages()
        if len(cap_languages) > 1:
            language_filters = S3OptionsFilter("language",
                                               label = T("Language"),
                                               options = cap_languages,
                                               represent = "%(name)s",
                                               resource = "cap_info",
                                               _name = "language-filter",
                                               )
            filters.append(language_filters)

        if current.request.get_vars["option"] == "manage_recipient" and \
           has_role("ADMIN"):
            from s3 import S3Represent
            recipient_filters = [S3OptionsFilter("id",
                                       label = T("People"),
                                       represent = S3Represent(lookup="auth_user",
                                            fields = ["first_name", "last_name"],
                                            field_sep = " ",
                                            ),
                                       widget = "multiselect",
                                       resource = "auth_user",
                                       _name = "person-filter",
                                       ),
                                 ]
            group_filters = [S3OptionsFilter("id",
                                       label = T("Groups"),
                                       represent = S3Represent(lookup="pr_group",
                                                               fields = ["name"],
                                                               ),
                                       widget = "multiselect",
                                       resource = "pr_group",
                                       _name = "group-filter",
                                       ),
                             ]
            # Title
            title = T("Manage Recipients")
        else:
            recipient_filters = None
            group_filters = None
            # Title
            title = T("Subscriptions")

        filter_script = '''$.filterOptionsS3({
                             'trigger':'event-filter',
                             'target':'priority-filter',
                             'lookupPrefix': 'cap',
                             'lookupResource': 'warning_priority',
                             'lookupKey': 'event_type_id',
                             'showEmptyField': 'false'
                             })'''
        current.response.s3.jquery_ready.append(filter_script)

        # View
        self._view(THEME, "subscriptions.html")

        # Form
        form = self._manage_subscriptions(resources, filters, recipient_filters, group_filters)

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
    def _manage_subscriptions(self, resources, filters, recipient_filters, group_filters):
        """
            Custom form to manage subscriptions

            @param resources: available resources config
            @param filters: subscription filter widgets
            @param recipient_filters: recipient filter widgets
            @param group_filters: pr_group filter widgets
        """

        from gluon.http import redirect
        from gluon.validators import IS_IN_SET
        from s3.s3widgets import S3GroupedOptionsWidget, S3MultiSelectWidget
        from s3layouts import S3PopupLink
        # Uses Default Eden formstyle
        from s3theme import formstyle_foundation_2col as formstyle

        # L10n
        T = current.T
        db = current.db
        s3db = current.s3db
        auth = current.auth
        auth_user = auth.user
        gtable = db.auth_group
        has_role = auth.s3_has_role
        request = current.request
        response = current.response
        stable = s3db.pr_subscription
        ftable = s3db.pr_filter
        group_table = s3db.pr_group

        labels = Storage(
            #RESOURCES = T("Subscribe To"),
            #NOTIFY_ON = T("Notify On"),
            #FREQUENCY = T("Frequency"),
            NOTIFY_BY = T("Notify By"),
            #MORE = T("More Options"),
            #LESS = T("Less Options"),
            ATTACHMENT = T("Receive XML Attachment in EMAIL?"),
        )
        messages = Storage(
            ERROR = T("Error: could not update notification settings"),
            SUCCESS = T("Notification settings updated"),
        )
        # Initialize form
        form = FORM(_id="subscription-form",
                    hidden={"subscription-filters": ""})

        row = db(gtable.role == "Alert Editor").select(gtable.id,
                                                       limitby=(0, 1)).first()

        ae_id = row.id # Alert Editor role as the owned_by_group to distinguish Admin-controlled subscriptions
        if recipient_filters is not None:
            subscription_id = request.get_vars.get("subscription_id")
            if subscription_id:
                # Update form from pr_subscription
                pr_row = db(stable.id == subscription_id).select(stable.pe_id,
                                                        limitby=(0, 1)).first()
                pe_id = pr_row.pe_id
                subscription = self._get_admin_subscription(\
                                                subscription_id=subscription_id,
                                                pe_id=pe_id,
                                                )
                recipient_subscription = self._get_recipients_and_groups(\
                                                subscription_id=subscription_id,
                                                pe_id=pe_id,
                                                caller="recipients",
                                                )
                group_subscription = self._get_recipients_and_groups(\
                                                subscription_id=subscription_id,
                                                pe_id=pe_id,
                                                caller="groups",
                                                )
            else:
                # Create form
                subscription = self._get_admin_subscription()
                recipient_subscription = self._get_recipients_and_groups()
                group_subscription = self._get_recipients_and_groups()
            filter_form = S3FilterForm(filters, clear=False)
            fieldset = FIELDSET(filter_form.fields(None,
                                                   subscription["get_vars"]),
                                _id="subscription-filter-form")
            recipient_filter_form = S3FilterForm(recipient_filters, clear=False)
            recipient_fieldset = FIELDSET(recipient_filter_form.fields(None,
                                            recipient_subscription["get_vars"]),
                                          _id="recipient-filter-form")
            group_filter_form = S3FilterForm(group_filters, clear=False)
            group_fieldset = FIELDSET(group_filter_form.fields(None,
                                                group_subscription["get_vars"]),
                                      _id="group-filter-form")
            form.append(recipient_fieldset)
            form.append(group_fieldset)
            form.append(fieldset)
        else:
            subscription_id = request.get_vars.get("subscription_id")
            if subscription_id:
                # Get current subscription settings resp. form defaults
                # Normal User
                subscription = self._get_subscription(subscription_id=subscription_id)
            else:
                # Create Form
                subscription = self._get_subscription()

            # Filters
            filter_form = S3FilterForm(filters, clear=False)
            fieldset = FIELDSET(filter_form.fields(None,
                                                   subscription["get_vars"]),
                                _id="subscription-filter-form")
            form.append(fieldset)

        # Notification options
        rows = []

        selector = S3GroupedOptionsWidget(cols=1)

        methods = [("EMAIL", T("Email")),
                   ("SMS", T("SMS")),
                   ("FTP", T("FTP")),
                   ("GCM", T("Mobile App")),
                   ]

        method_options = Storage(name = "method", requires = IS_IN_SET(methods))

        rows.append(("method_selector__row",
                     "%s:" % labels.NOTIFY_BY,
                     selector(method_options,
                              subscription["method"],
                              _id="method_selector"),
                     ""))

        if not (request.get_vars["option"] == "manage_recipient" and \
           has_role("ADMIN")):
            # managing own subscriptions
            attachment_filter = S3GroupedOptionsWidget(cols=2, multiple=False)
            attachment_options = [(False, T("No")),
                                  (True, T("Yes")),
                                  ]

            rows.append(("attachment_filter__row",
                         "%s:" % labels.ATTACHMENT,
                         attachment_filter(Storage(name="attachment-filter",
                                                   requires=IS_IN_SET(attachment_options)
                                                   ),
                                           subscription["attachment"],
                                           _id="attachment_selector"),
                         ""))

            properties = subscription["comments"]
            if properties:
                properties = json.loads(properties)

            synctable = s3db.sync_repository
            query = (synctable.apitype == "ftp") & \
                    (synctable.deleted != True) & \
                    (synctable.owned_by_user == auth_user.id)

            ftp_rows = db(query).select(synctable.id,
                                        synctable.name,
                                        orderby = synctable.id)

            multiselect = S3MultiSelectWidget(header = False,
                                              multiple = False,
                                              create = {"c": "sync",
                                                        "f": "repository",
                                                        "label": "Create Repository",
                                                        },
                                              )
            if ftp_rows:
                if properties:
                    user_repository_id = properties["repository_id"]
                else:
                    user_repository_id = ftp_rows.first().id

                if auth.s3_has_permission("update", "sync_repository",
                                          record_id = user_repository_id):
                    repository_comment = S3PopupLink(c = "sync",
                                                     f = "repository",
                                                     m = "update",
                                                     args = [user_repository_id],
                                                     title = T("Update Repository"),
                                                     tooltip = T("You can edit your FTP repository here"),
                                                     )
                field = s3db.sync_task.repository_id
                ftp_ids = [(r.id, s3_str(T(r.name))) for r in ftp_rows]
                field.requires = IS_IN_SET(ftp_ids)

                rows.append(("sync_task_repository_id__row",
                             "",
                             multiselect(field,
                                         user_repository_id,
                                         _id="sync_task_repository_id"),
                             repository_comment))
            else:
                if auth.s3_has_permission("create", "sync_repository"):
                    repository_comment = S3PopupLink(c = "sync",
                                                     f = "repository",
                                                     title = T("Add FTP Directory and Authentication Details"),
                                                     tooltip = T("Click on the link to begin creating your FTP repository and setting authentication details"),
                                                     )
                rows.append(("sync_task_repository_id__row",
                             "",
                             "",
                             repository_comment))

        parent = FIELDSET()

        for row in rows:
            parent.append(formstyle(form, [row]))

        # Deactivated Toggle
        #parent.insert(0,
        #              DIV(SPAN([I(_class="icon-reorder"), labels.MORE],
        #                       _class="toggle-text",
        #                       _style="display:none"),
        #                  SPAN([I(_class="icon-reorder"), labels.LESS],
        #                       _class="toggle-text"),
        #                  _id="notification-options",
        #                  _class="control-group"))
        form.append(parent)

        # Submit button
        submit_fieldset = FIELDSET(DIV("",
                                       INPUT(_type="submit",
                                             _value="Update Settings",
                                             _class="button small"),
                                       _id = "submit__row"))

        form.append(submit_fieldset)

        # Script (to extract filters on submit and toggle options visibility)
        script = URL(c="static", f="scripts", args=["S3", "s3.subscriptions.js"])
        response.s3.scripts.append(script)

        # Script to show/hide the ftp repo row for FTP checkbox on/off
        repository_script = '''
if($('#method_selector option[value=FTP]').is(':selected')){
    $('#sync_task_repository_id__row').show();
} else {
    $('#sync_task_repository_id__row').hide();
}

$('#method_selector').change(function(){
    if($(this).val().indexOf('FTP') != -1){
        $('#sync_task_repository_id__row').show();
    } else {
        $('#sync_task_repository_id__row').hide();
    }
})
'''
        response.s3.jquery_ready.append(repository_script)

        # Accept form
        if form.accepts(request.post_vars,
                        current.session,
                        formname="subscription",
                        keepvalues=True):

            formvars = form.vars

            #listify = lambda x: None if not x else x if type(x) is list else [x]

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
            # Fixed method
            subscription["method"] = formvars.method
            # Fixed Notify On and Frequency
            subscription["notify_on"] = ["upd"]
            subscription["frequency"] = "immediately"
            # Alternatively, with notify and frequency selector
            #subscription["notify_on"] = listify(formvars.notify_on)
            #subscription["frequency"] = formvars.frequency
            # Group IDs
            group_ids = formvars["group-filter"]
            # Recipient IDs
            user_ids = formvars["person-filter"]
            # Attachment
            attachment = False
            if formvars["attachment-filter"] == "True":
                attachment = True

            from collections import Counter

            get_event_type_priorities = self._get_event_type_priorities
            bulk_user_pe_id = auth.s3_bulk_user_pe_id
            get_group_pe_id = self._get_group_pe_id
            pr_group_table = s3db.pr_group
            define_resource = s3db.resource
            base_query = (stable.deleted != True)
            if user_ids is not None:
                # Admin Subscriptions
                # @ToDo: check super-set and/or sub-set for priorities and locations
                # of same event_type
                update_admin_subscription = self._update_admin_subscription
                if group_ids is None:
                    group_ids = []
                if group_ids or user_ids:
                    user_pe_ids = None
                    group_pe_ids = None
                    if user_ids:
                        user_pe_ids = bulk_user_pe_id(user_ids) # Current Selection
                    if group_ids:
                        group_pe_ids = get_group_pe_id(group_ids)
                    event_type_id, priorities = \
                        get_event_type_priorities(subscription["filters"]) # Current filters
                    subscription_id = request.get_vars.get("subscription_id")
                    if subscription_id:
                        query = base_query & \
                                (stable.id == subscription_id) & \
                                (stable.filter_id == ftable.id)
                        row = db(query).select(stable.pe_id,
                                               stable.filter_id,
                                               stable.comments,
                                               ftable.query,
                                               limitby=(0, 1)).first()
                        pr_subscription = row.pr_subscription
                        pe_id = row.pr_subscription.pe_id
                        if group_pe_ids and (pe_id in group_pe_ids.keys()):
                                event_type_id_s, priorities_s = \
                                    get_event_type_priorities(row.pr_filter.query)
                                if event_type_id_s == event_type_id and \
                                   Counter(priorities_s) == Counter(priorities):
                                    # Update
                                    comments = json.loads(pr_subscription.comments)
                                    success_subscription = update_admin_subscription(\
                                            subscription,
                                            pe_id,
                                            ae_id,
                                            group_id=comments["pr_group.id"],
                                            filter_id=pr_subscription.filter_id,
                                            subscription_id=subscription_id,
                                            )
                        elif user_pe_ids and (pe_id in user_pe_ids.values()):
                                event_type_id_s, priorities_s = \
                                    get_event_type_priorities(row.pr_filter.query)
                                if event_type_id_s == event_type_id and \
                                   Counter(priorities_s) == Counter(priorities):
                                    # Update
                                    user_id = [key for key, value in user_pe_ids.items()
                                               if value == pe_id][0]
                                    success_subscription = update_admin_subscription(\
                                            subscription,
                                            pe_id,
                                            ae_id,
                                            user_id=int(user_id),
                                            filter_id=pr_subscription.filter_id,
                                            subscription_id=subscription_id,
                                            )
                        else:
                            # Removed from subscriptions
                            define_resource("pr_subscription",
                                            id=subscription_id).delete()
                            define_resource("pr_filter",
                                            id=row.pr_subscription.filter_id).delete()
                    base_query = base_query & \
                                 (stable.owned_by_group != None) & \
                                 (stable.filter_id == ftable.id)
                    # Groups
                    if group_pe_ids:
                        for pe_id in group_pe_ids:
                            group_id = group_pe_ids[pe_id]
                            query = base_query & \
                                    (stable.pe_id == pe_id)
                            rows = db(query).select(stable.id,
                                                    stable.filter_id,
                                                    ftable.query)
                            if not rows:
                                # Create
                                success_subscription = update_admin_subscription(\
                                                            subscription,
                                                            pe_id,
                                                            ae_id,
                                                            group_id=int(group_id),
                                                            )
                            else:
                                for row in rows:
                                    event_type_id_s, priorities_s = \
                                        get_event_type_priorities(row.pr_filter.query)
                                    if event_type_id_s == event_type_id and \
                                       Counter(priorities_s) == Counter(priorities):
                                        # Update
                                        success_subscription = update_admin_subscription(\
                                            subscription,
                                            pe_id,
                                            ae_id,
                                            group_id=int(group_id),
                                            filter_id=row.pr_subscription.filter_id,
                                            subscription_id=row.pr_subscription.id,
                                            )
                                        break
                                else:
                                    # Create
                                    success_subscription = update_admin_subscription(\
                                                            subscription,
                                                            pe_id,
                                                            ae_id,
                                                            group_id=int(group_id),
                                                            )
                    # People
                    if user_pe_ids:
                        for user_id in user_pe_ids:
                            pe_id = int(user_pe_ids[user_id])
                            query = base_query & \
                                    (stable.pe_id == pe_id)
                            rows = db(query).select(stable.id,
                                                    stable.filter_id,
                                                    ftable.query)
                            if not rows:
                                # Create
                                success_subscription = update_admin_subscription(\
                                                                subscription,
                                                                pe_id,
                                                                ae_id,
                                                                user_id=int(user_id),
                                                                )
                            else:
                                for row in rows:
                                    event_type_id_s, priorities_s = \
                                        get_event_type_priorities(row.pr_filter.query)
                                    if event_type_id_s == event_type_id and \
                                       Counter(priorities_s) == Counter(priorities):
                                        # Update
                                        success_subscription = update_admin_subscription(\
                                                subscription,
                                                pe_id,
                                                ae_id,
                                                user_id=int(user_id),
                                                filter_id=row.pr_subscription.filter_id,
                                                subscription_id=row.pr_subscription.id,
                                                )
                                        break
                                else:
                                    # Create
                                    success_subscription = update_admin_subscription(\
                                                            subscription,
                                                            pe_id,
                                                            ae_id,
                                                            user_id=int(user_id),
                                                            )
                else:
                    # Removed from subscription
                    subscription_id = request.get_vars.get("subscription_id")
                    if subscription_id:
                        row = db(stable.id == subscription_id).select(\
                                                        stable.filter_id,
                                                        limitby=(0, 1)).first()
                        define_resource("pr_subscription",
                                        id=subscription_id).delete()
                        define_resource("pr_filter",
                                        id=row.filter_id).delete()
                redirect(URL(c="pr", f="subscription",
                             vars={"option": "manage_recipient"})
                         )
            else:
                # managing own subscription
                # @ToDo: check super-set and/or sub-set for priorities and locations
                # of same event_type
                update_subscription = self._update_subscription
                pe_id = auth_user.pe_id
                user_id = auth_user.id
                event_type_id, priorities = \
                    get_event_type_priorities(subscription["filters"]) # Current filters
                subscription_id = request.get_vars.get("subscription_id")
                if subscription_id:
                    query = base_query & \
                            (stable.id == subscription_id) & \
                            (stable.filter_id == ftable.id)
                    row = db(query).select(stable.filter_id,
                                           ftable.query,
                                           limitby=(0, 1)).first()
                    if row.pr_filter.query == subscription["filters"]:
                        # Update
                        success_subscription = update_subscription(\
                                        subscription,
                                        pe_id,
                                        filter_id=row.pr_subscription.filter_id,
                                        subscription_id=subscription_id,
                                        attachment=attachment,
                                        )
                    else:
                        # Remove
                        define_resource("pr_subscription",
                                        id=subscription_id).delete()
                        define_resource("pr_filter",
                                        id=row.pr_subscription.filter_id).delete()

                query = base_query & \
                        (stable.owned_by_group == None) & \
                        (stable.owned_by_user == user_id) & \
                        (stable.pe_id == pe_id) & \
                        (stable.filter_id == ftable.id)
                rows = db(query).select(stable.id,
                                        stable.filter_id,
                                        ftable.query)
                if rows:
                    for row in rows:
                        event_type_id_s, priorities_s = \
                            get_event_type_priorities(row.pr_filter.query)
                        if event_type_id_s == event_type_id and \
                           Counter(priorities_s) == Counter(priorities):
                            # Update
                            success_subscription = update_subscription(\
                                        subscription,
                                        pe_id,
                                        filter_id=row.pr_subscription.filter_id,
                                        subscription_id=row.pr_subscription.id,
                                        attachment=attachment,
                                        )
                            break
                    else:
                        # Create
                        success_subscription = update_subscription(subscription,
                                                                   pe_id,
                                                                   attachment=attachment)
                else:
                    # Create
                    success_subscription = update_subscription(subscription,
                                                               pe_id,
                                                               attachment=attachment)

                # Process Sync FTP Subscription
                if "FTP" in subscription["method"] and formvars.repository_id:
                    properties = self._update_sync(subscription["subscribe"][0]['resource'],
                                                   subscription.get("filters"),
                                                   int(formvars.repository_id),
                                                   properties)
                    properties = json.dumps(properties)
                    query = base_query & \
                            (stable.pe_id == pe_id) & \
                            (stable.owned_by_group == None) & \
                            (stable.owned_by_user == user_id)
                    db(query).update(comments=properties)
                else:
                    self._remove_sync(properties)
                    query = base_query & \
                            (stable.pe_id == pe_id) & \
                            (stable.owned_by_group == None) & \
                            (stable.owned_by_user == user_id)
                    db(query).update(comments=None)

                redirect(URL(c="pr", f="subscription"))

            if success_subscription:
                response.confirmation = messages.SUCCESS
            else:
                response.error = messages.ERROR

        return form

    # -------------------------------------------------------------------------
    def _get_subscription(self, subscription_id = None):
        """ Get current subscription settings """

        db = current.db
        s3db = current.s3db

        pe_id = current.auth.user.pe_id

        stable = s3db.pr_subscription
        if subscription_id is not None:
            ftable = s3db.pr_filter
            rows = db(stable).select()
            query = (stable.deleted != True) & \
                    (stable.id == subscription_id) & \
                    (stable.pe_id == pe_id) & \
                    (stable.owned_by_group == None) & \
                    (stable.owned_by_user == current.auth.user.id)

            left = ftable.on(ftable.id == stable.filter_id)
            row = db(query).select(stable.id,
                                   #stable.notify_on,
                                   #stable.frequency,
                                   stable.method,
                                   stable.comments,
                                   stable.attachment,
                                   ftable.id,
                                   ftable.query,
                                   left=left,
                                   limitby=(0, 1)).first()
        else:
            row = None

        output = {"pe_id": pe_id}

        get_vars = {}
        if subscription_id is None:
            # Create form
            cap_languages = current.deployment_settings.get_cap_languages()
            if len(cap_languages) > 1:
                default_option_language = None
                default_user_language = current.auth.user.language
                if default_user_language:
                    if default_user_language == "en":
                        default_user_language = "en-US"
                    if default_user_language in cap_languages:
                        default_option_language = default_user_language
                if default_option_language is not None:
                    get_vars = {"language__belongs": default_option_language}

        if row and row is not None:
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
                           "notify_on": ["new"],#s.notify_on
                           "frequency": "immediately",#s.frequency
                           "method": s.method,
                           "comments": s.comments,
                           "attachment": s.attachment,
                           })

        else:
            # Form defaults
            output.update({"id": None,
                           "filter_id": None,
                           "get_vars" : get_vars,
                           "resources": None,
                           "notify_on": ["new"],#stable.notify_on.default,
                           "frequency": "immediately",#stable.frequency.default,
                           "method": stable.method.default,
                           "comments": None,
                           "attachment": False,
                           })
        return output

    # -------------------------------------------------------------------------
    def _get_admin_subscription(self, subscription_id=None, pe_id=None):
        """ Get current admin subscription settings """

        s3db = current.s3db
        stable = s3db.pr_subscription
        ftable = s3db.pr_filter
        output = {}
        get_vars = {}
        if pe_id and subscription_id:
            query = (stable.id == subscription_id) & \
                    (stable.deleted != True) & \
                    (stable.pe_id == pe_id)
            left = ftable.on(ftable.id == stable.filter_id)
            row = current.db(query).select(stable.method,
                                           ftable.query,
                                           left=left,
                                           limitby=(0, 1)).first()

            if row:
                s = getattr(row, "pr_subscription")
                f = getattr(row, "pr_filter")

                if f.query:
                    filters = json.loads(f.query)
                    for k, v in filters:
                        if v is None:
                            continue
                        if k == "info.language__belongs":
                            k = "language__belongs"
                        if k == "info.priority__belongs":
                            k = "priority__belongs"
                        if k in get_vars:
                            if type(get_vars[k]) is list:
                                get_vars[k].append(v)
                            else:
                                get_vars[k] = [get_vars[k], v]
                        else:
                            get_vars[k] = v
                output.update({"get_vars": get_vars,
                               "method": s.method,
                               })
        else:
            # Form defaults
            output.update({"get_vars": get_vars,
                           "method": stable.method.default,
                           })

        return output

    # -------------------------------------------------------------------------
    def _get_recipients_and_groups(self, subscription_id=None, pe_id=None, caller=None):
        """ Get current recipient and the current group settings"""

        stable = current.s3db.pr_subscription
        get_vars = {}
        if pe_id is not None and subscription_id is not None:
            query = (stable.id == subscription_id) & \
                    (stable.deleted != True) & \
                    (stable.pe_id == pe_id)
            row = current.db(query).select(stable.comments,
                                           limitby=(0, 1)).first()
            comments = json.loads(row.comments)
            if row is not None and comments is not None:
                if caller == "recipients" and "auth_user.id" in comments:
                    filters = [["id__belongs", "%s" % str(comments["auth_user.id"])]]
                elif caller == "groups" and "pr_group.id" in comments:
                    filters = [["id__belongs", "%s" % str(comments["pr_group.id"])]]
                else:
                    filters = None
                if filters is not None:
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

        output = {"get_vars": get_vars}
        return output

    # -------------------------------------------------------------------------
    def _update_subscription(self,
                             subscription,
                             pe_id,
                             filter_id=None,
                             subscription_id=None,
                             attachment=False,
                             ):
        """ Update subscription settings """

        db = current.db
        s3db = current.s3db
        ftable = s3db.pr_filter

        # Save filters
        # Filter Public and Restricted alert
        # Private alert are not sent through subscription
        filters = subscription.get("filters")
        filters = json.loads(filters)
        for filter in filters:
            if filter[0] == "language__belongs":
                filter[0] = "info.language__belongs"
            if filter[0] == "priority__belongs":
                filter[0] = "info.priority__belongs"
        scope_filter = ["scope__belongs", "Public,Restricted"]
        system_alert_filter = ["external__ne", "True"]
        filters.append(scope_filter)
        filters.append(system_alert_filter)
        filters = json.dumps(filters)

        if not filter_id:
            success = ftable.insert(pe_id=pe_id, query=filters)
            filter_id = success
        else:
            success = db(ftable.id == filter_id).update(query=filters)
        if not success:
            return None

        # Save subscription settings
        stable = s3db.pr_subscription
        frequency = subscription["frequency"]
        if not subscription_id:
            success = stable.insert(pe_id=pe_id,
                                    filter_id=filter_id,
                                    notify_on=subscription["notify_on"],
                                    frequency=frequency,
                                    method=subscription["method"],
                                    attachment=attachment)
            subscription_id = success
        else:
            success = db(stable.id == subscription_id).update(
                            pe_id=pe_id,
                            filter_id=filter_id,
                            notify_on=subscription["notify_on"],
                            frequency=frequency,
                            method=subscription["method"],
                            attachment=attachment)
        if not success:
            return None

        # Save subscriptions
        rtable = s3db.pr_subscription_resource
        subscribe = subscription.get("subscribe")
        if subscribe:
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
                                    "url": url,
                                    }
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

    # -------------------------------------------------------------------------
    def _update_admin_subscription(self,
                                   subscription,
                                   pe_id,
                                   alert_editor_id,
                                   user_id=None,
                                   group_id=None,
                                   filter_id=None,
                                   subscription_id=None,
                                   ):
        """ Update Admin subscription """

        db = current.db
        s3db = current.s3db
        stable = s3db.pr_subscription
        # Save filters
        # Filter Public and Restricted alert
        # Private alert are not sent through subscription
        filters = subscription.get("filters")

        if user_id is not None:
            comment_filter = {"auth_user.id": str(user_id)}
        elif group_id is not None:
            comment_filter = {"pr_group.id": str(group_id)}
        else:
            comment_filter = None

        ftable = s3db.pr_filter

        filters = subscription.get("filters")
        filters = json.loads(filters)
        for filter in filters:
            if filter[0] == "language__belongs":
                filter[0] = "info.language__belongs"
            if filter[0] == "priority__belongs":
                filter[0] = "info.priority__belongs"
        scope_filter = ["scope__belongs", "Public,Restricted"]
        system_alert_filter = ["external__ne", "True"]
        filters.append(scope_filter)
        filters.append(system_alert_filter)

        filters_ = [filter for filter in filters
                    if filter[0] != "id__belongs"]
        filters_ = json.dumps(filters_)
        if filter_id is None:
            success = ftable.insert(pe_id=pe_id, query=filters_)
            filter_id = success
        else:
            success = db(ftable.id == filter_id).update(query=filters_)
        if not success:
            return None
        # Save subscription settings
        frequency = subscription["frequency"]
        if subscription_id is None:
            if comment_filter is not None:
                comment_filter = json.dumps(comment_filter)
                success = stable.insert(pe_id=pe_id,
                                        filter_id=filter_id,
                                        notify_on=subscription["notify_on"],
                                        frequency=frequency,
                                        method=subscription["method"],
                                        comments=comment_filter,
                                        owned_by_group=alert_editor_id,
                                        )
            else:
                success = stable.insert(pe_id=pe_id,
                                        filter_id=filter_id,
                                        notify_on=subscription["notify_on"],
                                        frequency=frequency,
                                        method=subscription["method"],
                                        owned_by_group=alert_editor_id,
                                        )
            subscription_id = success
        else:
            if comment_filter is not None:
                comment_filter = json.dumps(comment_filter)
                success = db(stable.id == subscription_id).update(pe_id=pe_id,
                                            filter_id=filter_id,
                                            notify_on=subscription["notify_on"],
                                            frequency=frequency,
                                            method=subscription["method"],
                                            comments=comment_filter,
                                            owned_by_group=alert_editor_id,
                                            )
            else:
                success = db(stable.id == subscription_id).update(pe_id=pe_id,
                                            filter_id=filter_id,
                                            notify_on=subscription["notify_on"],
                                            frequency=frequency,
                                            method=subscription["method"],
                                            owned_by_group=alert_editor_id,
                                            )
        if not success:
            return None

        # Save subscription
        rtable = s3db.pr_subscription_resource
        subscribe = subscription.get("subscribe")
        if subscribe:
            subscribed = {}
            timestamps = {}
            intervals = s3db.pr_subscription_check_intervals
            interval = timedelta(minutes=intervals.get(frequency, 0))
            now = datetime.utcnow()
            row = db(rtable.subscription_id == subscription_id).select(\
                                                        limitby=(0,1)).first()
            if row:
                subscribed[(row.resource, row.url)] = row.id
                timestamps[row.id] = (row.last_check_time,
                                      row.next_check_time)

            fk = '''{"subscription_id": %s}''' % subscription_id
            for new in subscribe:
                resource, url = new["resource"], new["url"]
                if (resource, url) not in subscribed:
                    # Restore subscription if previously unsubscribed, else
                    # insert new record
                    unsubscribed = {"deleted": True,
                                    "deleted_fk": fk,
                                    "resource": resource,
                                    "url": url,
                                    }

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

        # Update subscription
        subscription["id"] = subscription_id
        subscription["filter_id"] = filter_id
        return subscription

    # -------------------------------------------------------------------------
    def _update_sync(self, resource, filters, selected_repository_id, properties):
        """
            Update synchronization settings

            @param resource: available resources config
            @param filters: filter applied on the resource
            @param selected_repository_id: repository that is under current selection
            @param properties: comment field of the pr_subscription; used to
                               store the ids of FTP Sync

        """

        db = current.db
        s3db = current.s3db
        auth = current.auth
        user_id = auth.user.id
        utcnow = current.request.utcnow

        if properties:
            old_repository_id = properties["repository_id"]
            if old_repository_id != selected_repository_id:
                # Update
                properties["repository_id"] = selected_repository_id
        else:
            # First Run
            properties = {"repository_id": selected_repository_id}
            old_repository_id = selected_repository_id

        # Sync Task
        sync_task_table = s3db.sync_task

        # Check if task already exists
        query = (sync_task_table.deleted != True) & \
                (sync_task_table.owned_by_user == user_id) & \
                (sync_task_table.repository_id == old_repository_id)

        row = db(query).select(sync_task_table.id,
                               sync_task_table.repository_id,
                               limitby=(0, 1)).first()
        if row:
            old_sync_id = properties["sync_task_id"]
            # Check if update?
            if row.repository_id != selected_repository_id:
                # Update
                db(sync_task_table.repository_id == old_repository_id).\
                                update(repository_id = selected_repository_id)
            sync_task_id = properties["sync_task_id"] = row.id
        else:
            # First Run
            sync_task_data = {"repository_id": selected_repository_id,
                              "resource_name": resource,
                              "mode": 2, #Push
                              "strategy": ["create"], # Alert updates are done
                                                      # as extra info elements
                              "representation": "cap",
                              "multiple_file": True,
                              "last_push": utcnow, # since used for notifications,
                                                   # so don't send old alerts
                              }
            sync_task_id = sync_task_table.insert(**sync_task_data)
            auth.s3_set_record_owner(sync_task_table, sync_task_id)
            old_sync_id = properties["sync_task_id"] = sync_task_id

        # Sync Resource Filter

        # Remove Old Filter and create new
        query = (FS("task_id") == old_sync_id)
        s3db.resource("sync_resource_filter", filter=query).delete()

        # Normally a filter looks like this
        # [["priority__belongs","24,3"],[u'location_id$L0__belongs', u'Nepal'],
        # [u'location_id$L1__belongs', u'Central']]
        # Get only those that have value and ignore null one
        filters = json.loads(filters)
        filters = [filter_ for filter_ in filters if filter_[1] is not None]

        sync_resource_filter_table = s3db.sync_resource_filter
        if len(filters) > 0:
            for filter_ in filters:
                # Get the prefix
                prefix = str(filter_[0]).strip("[]")
                # Get the value for prefix
                values = str(filter_[1])
                # Set the Components
                if prefix in ["event_type_id__belongs",
                              "priority__belongs",
                              "language__belongs"]:
                    component = "info"
                else:
                    component = "area_location"

                filter_string = "%s.%s=%s" % (component, prefix, values)
                resource_filter_data = {"task_id": sync_task_id,
                                        "tablename": resource,
                                        "filter_string": filter_string,
                                        "modified_on": utcnow,
                                        }
                resource_filter_id = sync_resource_filter_table. \
                                        insert(**resource_filter_data)
                row = db(sync_resource_filter_table.id == resource_filter_id).\
                                                select(limitby=(0, 1)).first()
                auth.s3_set_record_owner(sync_resource_filter_table,
                                         resource_filter_id)
                s3db.onaccept(sync_resource_filter_table, row)

        return properties

    # -------------------------------------------------------------------------
    def _remove_sync(self, properties):
        """ Remove synchronization settings """

        if properties:
            current.s3db.resource("sync_repository",
                                  id=properties["repository_id"]).delete()

    # -------------------------------------------------------------------------
    def _get_event_type_priorities(self, filters):
        """ Returns the event type and list of priorities for the filters """

        event_types = []
        priorities = []

        filters_ = json.loads(filters)
        filters_ = [filter_ for filter_ in filters_ if filter_[1] is not None]
        if len(filters_) > 0:
            for filter_ in filters_:
                # Get the prefix
                prefix = s3_str(filter_[0]).strip("[]")
                # Get the value for prefix
                values = filter_[1].split(",")
                if prefix == "event_type_id__belongs":
                    event_types = [int(s3_str(values[0]))]
                elif prefix == "priority__belongs":
                    priorities = [int(s3_str(value)) for value in values]

        return (event_types, priorities)

    # -------------------------------------------------------------------------
    def _get_group_pe_id(self, group_ids):
        """
            Get the PE-ID for list of group_ids

            @param group_ids: the list of group_ids

            @return: dictionary of pe_id and group_id
        """

        if group_ids:
            gtable = current.s3db.pr_group
            rows = current.db(gtable.id.belongs(group_ids)).select(gtable.id,
                                                                   gtable.pe_id)
            if rows:
                return {row.pe_id: row.id for row in rows}
        return None

# =============================================================================
class user_info(S3CustomController):
    """
        User Info API, used by Mobile Client
    """

    def __call__(self):

        auth = current.auth

        # Enforce non-interactive response
        auth.permission.format = "json"

        user = auth.user
        if not user:
            auth.permission.fail()
        else:
            s3db = current.s3db
            gtable = s3db.auth_group
            mtable = s3db.auth_membership
            query = (mtable.deleted != True) & \
                    (mtable.group_id == gtable.id) & \
                    (mtable.user_id == user["id"])
            rows = current.db(query).select(gtable.uuid)
            # Find the roles
            roles = []
            for row in rows:
                if row.uuid == "ALERT_EDITOR":
                    roles.append("e")
                elif row.uuid == "ALERT_APPROVER":
                    roles.append("a")

            response = {"r": roles,
                        "uid": user.id,
                        "pid": auth.s3_logged_in_person(),
                        "o": current.deployment_settings.get_cap_expire_offset(),
                        }
            current.response.headers["Content-Type"] = "application/json"
            return json.dumps(response)

# =============================================================================
class alert_hub_cop(S3CustomController):
    """ Secondary (home) page for the Alert Hub """

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

        time_filter = request.utcnow + timedelta(-15)

        map_filter = "~.external=True&~.status=Actual&~.info.expires__gt=%s" % time_filter

        feature_resources = [{"name"      : T("Alerts"),
                              "id"        : "search_results",
                              "layer_id"  : layer_id,
                              "filter"    : map_filter,
                              # We activate in callback after ensuring URL is updated for current filter status
                              "active"    : False,
                              }]

        _map = current.gis.show_map(callback='''S3.search.s3map()''',
                                    catalogue_layers=True,
                                    collapsed=True,
                                    feature_resources=feature_resources,
                                    save=False,
                                    search=True,
                                    toolbar=True,
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
        # Only show Alerts from the past 30 days
        resource.add_filter(FS("info.expires") >= time_filter)
        # Show External Alerts
        resource.add_filter(FS("external") == True)
        # Show only Actual alert
        resource.add_filter(FS("status") == "Actual")
        # Change representation
        resource.table.status.represent = None
        list_id = "cap_alert_datalist"
        list_fields = ["msg_type",
                       "info.headline",
                       "area.name",
                       #"info.description",
                       "info.sender_name",
                       "info.priority",
                       "status",
                       "scope",
                       "info.event_type_id",
                       "info.severity",
                       "info.certainty",
                       "info.urgency",
                       "sent",
                       ]
        # Order with most recent Alert first
        orderby = "cap_alert.sent desc"
        datalist, numrows, ids = resource.datalist(fields = list_fields,
                                                   #start = None,
                                                   limit = None,
                                                   list_id = list_id,
                                                   orderby = orderby,
                                                   layout = s3db.cap_alert_list_layout
                                                   )
        if numrows == 0:
            current.response.s3.crud_strings["cap_alert"].msg_no_match = T("No Current Alerts match these filters.")

        ajax_url = URL(c="cap", f=fn, args="datalist.dl",
                       vars={"list_id": list_id,
                             "info.expires__gt": time_filter,
                             "~.external": True,
                             "~.status": "Actual"})
        #@ToDo: Implement pagination properly
        output[list_id] = datalist.html(ajaxurl = ajax_url,
                                        pagesize = 0,
                                        )

        # @ToDo: Options are currently built from the full-set rather than the filtered set
        filter_widgets = [#S3LocationFilter("location.location_id",
                          #                 label=T("Location"),
                          #                 levels=("L0",),
                          #                 widget="multiselect",
                          #                 ),
                          S3OptionsFilter("info.event_type_id",
                                          #label=T("Event Type"),
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

        # Title and view
        output["title"] = s3_str(current.deployment_settings.get_cap_alert_hub_title())

        # Button to view datalist from map
        datalist_btn = A(T("View Datalist"),
                         _href = URL(c="cap",
                                     f=fn,
                                     vars = {"~.external": True}
                                     ),
                         _class = "action-btn button tiny",
                         )
        output["datalist_btn"] = datalist_btn

        self._view(THEME, "alert_hub.html")

        s3 = current.response.s3
        # Custom CSS
        s3.stylesheets.append("../themes/SAMBRO/style.css")

        # Custom JS
        s3.scripts.append("/%s/static/themes/SAMBRO/js/homepage.js" % request.application)

        return output

# END =========================================================================
