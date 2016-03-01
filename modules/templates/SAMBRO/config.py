# -*- coding: utf-8 -*-

try:
    # Python 2.7
    from collections import OrderedDict
except:
    # Python 2.6
    from gluon.contrib.simplejson.ordered_dict import OrderedDict

try:
    import json # try stdlib (Python 2.6)
except ImportError:
    try:
        import simplejson as json # try external module
    except:
        import gluon.contrib.simplejson as json # fallback to pure-Python module

from gluon import current
from gluon.storage import Storage

def config(settings):
    """
        Template settings for CAP: Common Alerting Protocol
    """

    T = current.T

    settings.base.system_name = T("Sahana Alerting and Messaging Broker")
    settings.base.system_name_short = T("SAMBRO")

    # Pre-Populate
    settings.base.prepopulate += ("SAMBRO", "SAMBRO/Demo", "default/users")

    # Theme (folder to use for views/layout.html)
    #settings.base.theme = "SAMBRO"

    # The Registration functionality shouldn't be visible to the Public
    settings.security.registration_visible = False

    # Link Users to Organisations
    settings.auth.registration_requests_organisation = True

    # GeoNames username
    settings.gis.geonames_username = "eden_test"

    # =========================================================================
    # System Settings
    # -------------------------------------------------------------------------
    # Security Policy
    # http://eden.sahanafoundation.org/wiki/S3/S3AAA#System-widePolicy
    # 1: Simple (default): Global as Reader, Authenticated as Editor
    # 2: Editor role required for Update/Delete, unless record owned by session
    # 3: Apply Controller ACLs
    # 4: Apply both Controller & Function ACLs
    # 5: Apply Controller, Function & Table ACLs
    # 6: Apply Controller, Function, Table ACLs and Entity Realm
    # 7: Apply Controller, Function, Table ACLs and Entity Realm + Hierarchy
    # 8: Apply Controller, Function, Table ACLs, Entity Realm + Hierarchy and Delegations
    settings.security.policy = 4 # Controller-Function ACLs

    # Record Approval
    settings.auth.record_approval = True
    # cap_alert record requires approval before sending
    settings.auth.record_approval_required_for = ("cap_alert",)
    # Don't auto-approve so that can save draft
    settings.auth.record_approval_manual = ("cap_alert",)

    # =========================================================================
    # Module Settings
    # -------------------------------------------------------------------------
    # CAP Settings
    # Uncomment this according to country profile
    #settings.cap.restrict_fields = True

    # -------------------------------------------------------------------------
    # Notifications

    # Template for the subject line in update notifications
    settings.msg.notify_subject = "$S %s" % T("Alert Notification")

    # Filename for FTP
    # Characters not allowed are [\ / : * ? " < > | % .]
    # https://en.wikipedia.org/wiki/Filename
    # http://docs.attachmate.com/reflection/ftp/15.6/guide/en/index.htm?toc.htm?6503.htm
    settings.sync.upload_filename = "$s-%s" % ("recent_alert")
    
    # Whether to tweet alerts
    settings.cap.post_to_twitter = True

    # -------------------------------------------------------------------------
    # L10n (Localization) settings
    languages = OrderedDict([
        #("ar", "العربية"),
        ("dv", "ދިވެހި"), # Divehi (Maldives)
        ("en-US", "English"),
        #("es", "Español"),
        #("fr", "Français"),
        #("km", "ភាសាខ្មែរ"),        # Khmer
        #("mn", "Монгол хэл"),  # Mongolian
        ("my", "မြန်မာစာ"),        # Burmese
        #("ne", "नेपाली"),          # Nepali
        #("prs", "دری"),        # Dari
        #("ps", "پښتو"),        # Pashto
        #("tet", "Tetum"),
        #("th", "ภาษาไทย"),        # Thai
        ("tl", "Tagalog"), # Filipino
        #("vi", "Tiếng Việt"),   # Vietnamese
        #("zh-cn", "中文 (简体)"),
    ])
    settings.L10n.languages = languages
    settings.cap.languages = languages
    # Translate the cap_area name
    settings.L10n.translate_cap_area = True

    # -------------------------------------------------------------------------
    # Messaging
    # Parser
    settings.msg.parser = "SAMBRO"

    # -------------------------------------------------------------------------
    # Organisations
    # Enable the use of Organisation Branches
    settings.org.branches = True
    # Show branches as tree rather than as table
    settings.org.branches_tree_view = True

    # -------------------------------------------------------------------------
    def customise_msg_rss_channel_resource(r, tablename):

        # @ToDo: We won't be able to automate this as we have 2 sorts, so will need the user to select manually
        # Can we add a component for the parser for S3CSV imports?

        # UX: separate menu items distinguished via get_var
        # @ToDo: Add menu entries for "Create RSS Feed for CAP" & "Create RSS Feed for CMS"
        type = current.request.get_vars.get("type", None)
        if type == "cap":
            fn = "parse_rss_2_cap"
        else:
            fn = "parse_rss_2_cms"

        s3db = current.s3db
        def onaccept(form):
            # Normal onaccept
            s3db.msg_channel_onaccept(form)
            _id = form.vars.id
            db = current.db
            table = db.msg_rss_channel
            channel_id = db(table.id == _id).select(table.channel_id,
                                                    limitby=(0, 1)).first().channel_id
            # Link to Parser
            table = s3db.msg_parser
            _id = table.insert(channel_id=channel_id, function_name=fn, enabled=True)
            s3db.msg_parser_enable(_id)

            async = current.s3task.async
            # Poll
            async("msg_poll", args=["msg_rss_channel", channel_id])

            # Parse
            async("msg_parse", args=[channel_id, fn])

        s3db.configure(tablename,
                       create_onaccept = onaccept,
                       )

    settings.customise_msg_rss_channel_resource = customise_msg_rss_channel_resource

    # -------------------------------------------------------------------------
    def customise_msg_twitter_channel_resource(r, tablename):

        s3db = current.s3db
        def onaccept(form):
            # Normal onaccept
            s3db.msg_channel_onaccept(form)
            _id = form.vars.id
            db = current.db
            table = db.msg_twitter_channel
            channel_id = db(table.id == _id).select(table.channel_id,
                                                    limitby=(0, 1)).first().channel_id
            # Link to Parser
            table = s3db.msg_parser
            _id = table.insert(channel_id=channel_id, function_name="parse_tweet", enabled=True)
            s3db.msg_parser_enable(_id)

            async = current.s3task.async
            # Poll
            async("msg_poll", args=["msg_twitter_channel", channel_id])

            # Parse
            async("msg_parse", args=[channel_id, "parse_tweet"])

        s3db.configure(tablename,
                       create_onaccept = onaccept,
                       )

    settings.customise_msg_twitter_channel_resource = customise_msg_twitter_channel_resource

    # -------------------------------------------------------------------------
    def customise_org_organisation_resource(r, tablename):

        from s3 import S3SQLCustomForm, S3SQLInlineComponent, S3SQLInlineLink
        crud_form = S3SQLCustomForm("name",
                                    "acronym",
                                    S3SQLInlineLink("organisation_type",
                                                    field = "organisation_type_id",
                                                    label = T("Type"),
                                                    multiple = False,
                                                    #widget = "hierarchy",
                                                    ),
                                    S3SQLInlineComponent(
                                        "tag",
                                        label = T("CAP OID"),
                                        multiple = False,
                                        fields = [("", "value")],
                                        filterby = dict(field = "tag",
                                                        options = "cap_oid",
                                                        ),
                                        ),
                                    "website",
                                    "comments",
                                    )

        current.s3db.configure("org_organisation",
                               crud_form = crud_form,
                               )

    settings.customise_org_organisation_resource = customise_org_organisation_resource

    # -------------------------------------------------------------------------
    def customise_cap_alert_resource(r, tablename):

        from s3 import s3_str
        s3db = current.s3db
        def onapprove(record):
            # Normal onapprove
            s3db.cap_alert_approve(record)

            # Sync FTP Repository
            current.s3task.async("cap_ftp_sync")

            # Twitter Post
            if settings.get_cap_post_to_twitter():
                try:
                    import tweepy
                except ImportError:
                    current.log.debug("tweepy module needed for sending tweets")
                else:
                    T = current.T
                    db = current.db
                    alert_id = int(record["id"])
                    atable = s3db.cap_alert
                    itable = s3db.cap_info
        
                    arow = db(atable.id == alert_id).select(atable.status,
                                                            atable.sender,
                                                            atable.sent,
                                                            limitby=(0, 1)).first()
                    query = (itable.alert_id == alert_id) & \
                            (itable.deleted != True)
                    irows = db(query).select(itable.headline,
                                             itable.web)
                    # @ToDo: shorten url
                    # @ToDo: Handle the multi-message nicely?
                    # @ToDo: Send resource url with tweet
                    for irow in irows:
                        twitter_text = \
("""%(Status)s: %(Headline)s
%(SENDER)s: %(SenderName)s
%(WEBSITE)s: %(Website)s""") % dict(Status = arow.status,
                                    Headline = s3_str(irow.headline),
                                    SENDER = T("Sender"),
                                    SenderName = s3_str(arow.sender),
                                    WEBSITE = T("Website"),
                                    Website = irow.web)
                        try:
                            current.msg.send_tweet(text=twitter_text)
                        except tweepy.error.TweepError, e:
                            current.log.debug("Sending tweets failed: %s" % e)

        s3db.configure(tablename,
                       onapprove = onapprove,
                       )

    settings.customise_cap_alert_resource = customise_cap_alert_resource

    # -------------------------------------------------------------------------
    def customise_sync_repository_controller(**attr):

        s3 = current.response.s3

        # Custom prep
        standard_prep = s3.prep
        def custom_prep(r):
            # Call standard prep
            if callable(standard_prep):
                result = standard_prep(r)
            else:
                result = True

            if r.representation == "popup":
                table = r.table
                table.apitype.default = "ftp"
                table.apitype.readable = table.apitype.writable = False
                table.accept_push.readable = table.accept_push.writable = False
                table.synchronise_uuids.readable = \
                                        table.synchronise_uuids.writable = False
                table.uuid.readable = table.uuid.writable = False

            return result
        s3.prep = custom_prep

        return attr

    settings.customise_sync_repository_controller = customise_sync_repository_controller

    # -------------------------------------------------------------------------
    def customise_pr_subscription_controller(**attr):

        from gluon.html import URL, A
        from s3 import S3CRUD
        s3 = current.response.s3
        s3db = current.s3db
        auth = current.auth
        request = current.request
        stable = s3db.pr_subscription
        has_role = auth.s3_has_role

        list_fields = [(T("Filters"), "filter_id"),
                       (T("Methods"), "method"),
                       ]

        if request.get_vars["option"] == "manage_recipient" and \
           (has_role("ALERT_EDITOR") or has_role("ALERT_APPROVER")):
                # Admin based subscription
                s3.filter = (stable.deleted != True) & \
                            (stable.owned_by_group != None)
                list_fields.insert(0, (T("People/Groups"), "pe_id"))
                s3.crud_strings["pr_subscription"].title_list = T("Admin Controlled Subscriptions")
        else:
            # Self Subscription
            s3.filter = (stable.deleted != True) & \
                        (stable.owned_by_group == None) & \
                        (stable.owned_by_user == auth.user.id)
            s3.crud_strings["pr_subscription"].title_list = T("Your Subscriptions")

        # Custom prep
        standard_prep = s3.prep
        def custom_prep(r):
            from s3 import S3Represent
            table = r.table
            # Call standard prep
            if callable(standard_prep):
                result = standard_prep(r)
            else:
                result = True
            MSG_CONTACT_OPTS = {"EMAIL": T("EMAIL"),
                                "SMS"  : T("SMS"),
                                "FTP"  : T("FTP"),
                                }
            table.method.represent = S3Represent(options=MSG_CONTACT_OPTS,
                                                 multiple=True,
                                                 ),
            if r.representation == "html":
                table.filter_id.represent = S3Represent(\
                                    options=pr_subscription_filter_row_options())
                s3db.configure("pr_subscription",
                               list_fields = list_fields,
                               list_orderby = "pe_id desc",
                               orderby = "pr_subscription.pe_id desc",
                               )

            return result
        s3.prep = custom_prep

        # Custom postp
        standard_postp = s3.postp
        def custom_postp(r, output):
            # Call standard postp
            if callable(standard_postp):
                output = standard_postp(r, output)

            if r.interactive and isinstance(output, dict):
                # Modify Open Button
                if request.get_vars["option"] == "manage_recipient" and \
                   (has_role("ALERT_EDITOR") or has_role("ALERT_APPROVER")):
                    # Admin based subscription
                    S3CRUD.action_buttons(r,
                                          update_url=URL(c="default", f="index",
                                                         args=["subscriptions"],
                                                         vars={"option": "manage_recipient",
                                                               "subscription_id": "[id]"}
                                                         ),
                                          delete_url=URL(c="pr", f="subscription",
                                                         args=["[id]", "delete"],
                                                         vars={"option": "manage_recipient"}
                                                         )
                                          )
                else:
                    # self subscription
                    S3CRUD.action_buttons(r, update_url=URL(c="default", f="index",
                                                            args=["subscriptions"],
                                                            vars={"subscription_id": "[id]"}
                                                            )
                                          )

                if "form" in output:
                    # Modify Add Button
                    if request.get_vars["option"] == "manage_recipient" and \
                       (has_role("ALERT_EDITOR") or has_role("ALERT_APPROVER")):
                        # Admin based subscription
                        add_btn = A(T("Create Subscription"),
                                    _class="action-btn",
                                    _href=URL(c="default", f="index",
                                              args=["subscriptions"],
                                              vars={"option": "manage_recipient"}
                                              )
                                    )
                    else:
                        # self subscription
                        add_btn = A(T("Create Subscription"),
                                    _class="action-btn",
                                    _href=URL(c="default", f="index", args=["subscriptions"])
                                    )
                    output["showadd_btn"] = add_btn

            return output
        s3.postp = custom_postp

        return attr

    settings.customise_pr_subscription_controller = customise_pr_subscription_controller

    # -------------------------------------------------------------------------
    # Comment/uncomment modules here to disable/enable them
    # @ToDo: Have the system automatically enable migrate if a module is enabled
    # Modules menu is defined in modules/eden/menu.py
    settings.modules = OrderedDict([
        # Core modules which shouldn't be disabled
        ("default", Storage(
            name_nice = T("Home"),
            restricted = False, # Use ACLs to control access to this module
            access = None,      # All Users (inc Anonymous) can see this module in the default menu & access the controller
            module_type = None  # This item is not shown in the menu
        )),
        ("admin", Storage(
            name_nice = T("Administration"),
            #description = "Site Administration",
            restricted = True,
            access = "|1|",     # Only Administrators can see this module in the default menu & access the controller
            module_type = None  # This item is handled separately for the menu
        )),
        ("appadmin", Storage(
            name_nice = T("Administration"),
            #description = "Site Administration",
            restricted = True,
            module_type = None  # No Menu
        )),
        ("errors", Storage(
            name_nice = T("Ticket Viewer"),
            #description = "Needed for Breadcrumbs",
            restricted = False,
            module_type = None  # No Menu
        )),
        ("sync", Storage(
            name_nice = T("Synchronization"),
            #description = "Synchronization",
            restricted = True,
            access = "|1|",     # Only Administrators can see this module in the default menu & access the controller
            module_type = None  # This item is handled separately for the menu
        )),
        #("tour", Storage(
        #    name_nice = T("Guided Tour Functionality"),
        #    module_type = None,
        #)),
        ("translate", Storage(
            name_nice = T("Translation Functionality"),
            #description = "Selective translation of strings based on module.",
            module_type = None,
        )),
        ("gis", Storage(
            name_nice = T("Mapping"),
            #description = "Situation Awareness & Geospatial Analysis",
            restricted = True,
            module_type = 6,     # 6th item in the menu
        )),
        ("pr", Storage(
            name_nice = T("Person Registry"),
            #description = "Central point to record details on People",
            restricted = True,
            access = "|1|",     # Only Administrators can see this module in the default menu (access to controller is possible to all still)
            module_type = 10
        )),
        ("org", Storage(
            name_nice = T("Organizations"),
            #description = 'Lists "who is doing what & where". Allows relief agencies to coordinate their activities',
            restricted = True,
            module_type = 10
        )),
        # All modules below here should be possible to disable safely
        #("hrm", Storage(
        #    name_nice = T("Staff"),
        #    #description = "Human Resources Management",
        #    restricted = True,
        #    module_type = 2,
        #)),
        ("cap", Storage(
            name_nice = T("Alerting"),
            #description = "Create & broadcast CAP alerts",
            restricted = True,
            module_type = 1,
        )),
        ("cms", Storage(
          name_nice = T("Content Management"),
          #description = "Content Management System",
          restricted = True,
          module_type = 10,
        )),
        ("doc", Storage(
            name_nice = T("Documents"),
            #description = "A library of digital resources, such as photos, documents and reports",
            restricted = True,
            module_type = 10,
        )),
        ("msg", Storage(
            name_nice = T("Messaging"),
            #description = "Sends & Receives Alerts via Email & SMS",
            restricted = True,
            # The user-visible functionality of this module isn't normally required. Rather it's main purpose is to be accessed from other modules.
            module_type = None,
        )),
        ("event", Storage(
            name_nice = T("Events"),
            #description = "Activate Events (e.g. from Scenario templates) for allocation of appropriate Resources (Human, Assets & Facilities).",
            restricted = True,
            module_type = 10,
        )),
    ])

    # -------------------------------------------------------------------------
    # Functions which are local to this Template
    # -------------------------------------------------------------------------
    def pr_subscription_filter_row_options():
        """
            Build the options for the pr_subscription filter datatable from query
            @ToDo complete this for locations
        """

        db = current.db
        s3db = current.s3db
        auth = current.auth
        has_role = auth.s3_has_role
        stable = s3db.pr_subscription
        ftable = s3db.pr_filter

        if current.request.get_vars["option"] == "manage_recipient" and \
           (has_role("ALERT_EDITOR") or has_role("ALERT_APPROVER")):
                # Admin based subscription
                query = (stable.deleted != True) & \
                        (stable.owned_by_group != None)
        else:
            # Self Subscription
            query = (stable.deleted != True) & \
                    (stable.owned_by_group == None) & \
                    (stable.owned_by_user == auth.user.id)

        left = ftable.on(ftable.id == stable.filter_id)
        rows = db(query).select(stable.filter_id,
                                ftable.query,
                                left=left)
        if len(rows) > 0:
            from s3 import s3_str
            T = current.T
            etable = s3db.event_event_type
            ptable = s3db.cap_warning_priority
            filter_options = {}
            for row in rows:
                event_type_id = []
                priorities_id = []
                languages = []

                filters = json.loads(row.pr_filter.query)
                filters = [filter for filter in filters if filter[1] is not None]
                if len(filters) > 0:
                    for filter in filters:
                        # Get the prefix
                        prefix = s3_str(filter[0]).strip("[]")
                        # Get the value for prefix
                        values = filter[1].split(",")
                        if prefix == "event_type_id__belongs":
                            event_type_id = int(s3_str(values[0]))
                            row_ = db(etable.id==event_type_id).select(\
                                                        etable.name,
                                                        limitby=(0, 1)).first()
                            event_type = row_.name
                        elif prefix == "priority__belongs":
                            priorities_id = [int(s3_str(value)) for value in values]
                            rows_ = db(ptable.id.belongs(priorities_id)).select(ptable.name)
                            priorities = [row_.name for row_ in rows_]
                        elif prefix == "language__belongs":
                            languages = [s3_str(value) for value in values]

                    display_text = "<b>%s:</b> %s" % (T("Event Type"), event_type)
                    if len(priorities_id) > 0:
                        display_text = "%s<br/><b>%s</b>: %s" % (display_text, T("Priorities"), priorities)
                    else:
                        display_text = "%s<br/><b>%s</b>" % (display_text, T("Priorities: None"))
                    if len(languages) > 0:
                        display_text = "%s<br/><b>%s</b>:%s" % (display_text, T("Languages"), languages)
                    else:
                        display_text = "%s<br/><b>%s</b>" % (display_text, T("Languages: None"))
                    filter_options[row["pr_subscription.filter_id"]] = display_text
                else:
                    filter_options[row["pr_subscription.filter_id"]] = T("No filters")

            return filter_options

# END =========================================================================
