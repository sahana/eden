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
from gluon.html import *
from gluon.storage import Storage
from s3 import s3_str

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
    #settings.security.registration_visible = True

    settings.auth.registration_requires_approval = True

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
    settings.msg.notify_subject = "%s $s %s" % (T("SAHANA"), T("Alert Notification"))

    # Notifications format
    settings.msg.notify_email_format = "html"

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

        T = current.T
        db = current.db
        s3db = current.s3db
        def onapprove(record):
            # Normal onapprove
            s3db.cap_alert_approve(record)
            # Sync FTP Repository
            current.s3task.async("cap_ftp_sync")

            # Twitter Post
            if settings.get_cap_post_to_twitter() and \
               record["scope"] != "Private":
                try:
                    import tweepy
                except ImportError:
                    current.log.debug("tweepy module needed for sending tweets")
                else:
                    alert_id = int(record["id"])
                    atable = s3db.cap_alert
                    itable = s3db.cap_info
        
                    arow = db(atable.id == alert_id).select(atable.status,
                                                            limitby=(0, 1)).first()
                    query = (itable.alert_id == alert_id) & \
                            (itable.deleted != True)
                    irows = db(query).select(itable.headline,
                                             itable.sender_name,
                                             itable.web)
                    # @ToDo: shorten url
                    # @ToDo: Handle the multi-message nicely?
                    # @ToDo: Send resource url with tweet
                    for irow in irows:
                        twitter_text = \
("""%(Status)s: %(Headline)s
%(SENDER)s: %(SenderName)s
%(WEBSITE)s: %(Website)s%(Profile)s""") % dict(Status = arow.status,
                                               Headline = s3_str(irow.headline),
                                               SENDER = T("Sender"),
                                               SenderName = s3_str(irow.sender_name),
                                               WEBSITE = T("Website"),
                                               Website = irow.web,
                                               Profile = "/profile",
                                               )
                        try:
                            current.msg.send_tweet(text=twitter_text)
                        except tweepy.error.TweepError, e:
                            current.log.debug("Sending tweets failed: %s" % e)

            # Send out private alerts to addresses
            # @ToDo: Check for LEFT join when required
            # this is ok for now since every Alert should have an Info & an Area
            # @ToDo: Handle multi-lingual alerts when required
            if record["scope"] == "Private":
                table = s3db.cap_alert
                itable = s3db.cap_info
                atable = s3db.cap_area
                gtable = s3db.pr_group
                send_by_pe_id = current.msg.send_by_pe_id

                alert_id = record["id"]
                addresses = record["addresses"]
                query = (table.id == alert_id) & \
                        (itable.alert_id == table.id) & \
                        (itable.deleted != True) & \
                        (atable.alert_id == table.id) & \
                        (atable.deleted != True)
                row = db(query).select(table.identifier,
                                       table.msg_type,
                                       table.scope,
                                       table.sent,
                                       table.source,
                                       table.status,
                                       itable.category,
                                       itable.certainty,
                                       itable.contact,
                                       itable.effective,
                                       itable.expires,
                                       itable.event_type_id,
                                       itable.headline,
                                       itable.instruction,
                                       itable.priority,
                                       itable.response_type,
                                       itable.sender_name,
                                       itable.severity,
                                       itable.urgency,
                                       itable.web,
                                       atable.name,
                                       limitby=(0, 1)).first()
                subject = "%s %s %s" % (T("SAHANA"),
                                        settings.get_system_name_short(),
                                        T("Alert Notification"))
                email_content = "%s%s%s" % ("<html>", XML(get_html_email_content(row)), "</html>")
                sms_content = get_sms_content(row)
                count = len(addresses)
                if count == 1:
                    query = (gtable.id == addresses[0])
                else:
                    query = (gtable.id.belongs(addresses))
                rows = db(query).select(gtable.pe_id,
                                        limitby = (0, count))
                for row_ in rows:
                    send_by_pe_id(row_.pe_id, subject, email_content)
                    try:
                        send_by_pe_id(row_.pe_id, subject, sms_content, contact_method="SMS")
                    except ValueError:
                        current.log.error("No SMS Handler defined!")

        s3db.configure(tablename,
                       onapprove = onapprove,
                       )

    settings.customise_cap_alert_resource = customise_cap_alert_resource

    # -------------------------------------------------------------------------
    def customise_cap_alert_controller(**attr):

        s3 = current.response.s3
        # Custom prep
        standard_prep = s3.prep
        def custom_prep(r):
            # Call standard prep
            if callable(standard_prep):
                result = standard_prep(r)
            else:
                result = True

            if r.representation == "msg":
                # Notification
                table = r.table
                table.scope.represent = None
                table.status.represent = None
                table.msg_type.represent = None

                itable = current.s3db.cap_info
                itable.severity.represent = None
                itable.urgency.represent = None
                itable.certainty.represent = None

            return result
        s3.prep = custom_prep

        return attr

    settings.customise_cap_alert_controller = customise_cap_alert_controller

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

        from s3 import S3CRUD
        s3 = current.response.s3
        s3db = current.s3db
        auth = current.auth
        stable = s3db.pr_subscription
        has_role = auth.s3_has_role

        list_fields = [(T("Filters"), "filter_id"),
                       (T("Methods"), "method"),
                       ]
        manage_recipient = current.request.get_vars["option"] == "manage_recipient"
        role_check = has_role("ALERT_EDITOR") or has_role("ALERT_APPROVER")

        if manage_recipient and role_check:
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
                if manage_recipient and role_check:
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
                    if manage_recipient and role_check:
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

    # -----------------------------------------------------------------------------
    def custom_msg_render(resource, data, meta_data, format=None):
        """
            Custom Method to pre-render the contents for the message template

            @param resource: the S3Resource
            @param data: the data returned from S3Resource.select
            @param meta_data: the meta data for the notification
            @param format: the contents format ("text" or "html")
        """

        from s3 import s3_utc
        created_on_selector = resource.prefix_selector("created_on")
        created_on_colname = None
        notify_on = meta_data["notify_on"]
        last_check_time = meta_data["last_check_time"]
        rows = data["rows"]
        rfields = data["rfields"]
        output = {}
        new, upd = [], []
        if format == "text":
            # For SMS
            labels = []
            append = labels.append

            for rfield in rfields:
                if rfield.selector == created_on_selector:
                    created_on_colname = rfield.colname
                elif rfield.ftype != "id":
                    append((rfield.colname, rfield.label))

            for row in rows:
                append_record = upd.append
                if created_on_colname:
                    try:
                        created_on = row["_row"][created_on_colname]
                    except KeyError, AttributeError:
                        pass
                    else:
                        if s3_utc(created_on) >= last_check_time:
                            append_record = new.append

                record = []
                append_column = record.append
                for colname, label in labels:
                    append_column((label, row[colname]))
                append_record(record)

            if "new" in notify_on and len(new):
                output["new"] = len(new)
                output["new_records"] = new
            else:
                output["new"] = None
            if "upd" in notify_on and len(upd):
                output["upd"] = len(upd)
                output["upd_records"] = upd
            else:
                output["upd"] = None
        else:
            # HTML emails
            elements = []
            append = elements.append
            for rfield in rfields:
                if rfield.selector == created_on_selector:
                    created_on_colname = rfield.colname

            for row in rows:
                append_record = upd.append
                if created_on_colname:
                    try:
                        created_on = row["_row"][created_on_colname]
                    except KeyError, AttributeError:
                        pass
                    else:
                        if s3_utc(created_on) >= last_check_time:
                            append_record = new.append
                content = get_html_email_content(row)
                container = DIV(DIV(content))
                append(container)
                append(BR())
                append_record(container)
            if "new" in notify_on and len(new):
                output["new"] = len(new)
                output["new_body"] = DIV(*elements)
            else:
                output["new"] = None
            if "upd" in notify_on and len(upd):
                output["upd"] = len(upd)
                output["upd_body"] = DIV(*elements)
            else:
                output["upd"] = None

        output.update(meta_data)
        return output

    settings.msg.notify_renderer = custom_msg_render

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
            T = current.T
            etable = s3db.event_event_type
            ptable = s3db.cap_warning_priority
            filter_options = {}
            for row in rows:
                event_type = None
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
                            event_type_id = s3_str(values[0])
                            row_ = db(etable.id == event_type_id).select(\
                                                        etable.name,
                                                        limitby=(0, 1)).first()
                            event_type = row_.name
                        elif prefix == "priority__belongs":
                            priorities_id = [int(s3_str(value)) for value in values]
                            rows_ = db(ptable.id.belongs(priorities_id)).select(ptable.name)
                            priorities = [row_.name for row_ in rows_]
                        elif prefix == "language__belongs":
                            languages = [s3_str(value) for value in values]
                    if event_type is not None:
                        display_text = "<b>%s:</b> %s" % (T("Event Type"), event_type)
                    else:
                        display_text = "<b>%s</b>" % (T("Event Type: None"))
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

    # -------------------------------------------------------------------------
    def get_html_email_content(row):
        """
            prepare the content for html email
        """

        from gluon.languages import lazyT
        itable = current.s3db.cap_info
        event_type_id = row["cap_info.event_type_id"]
        priority_id = row["cap_info.priority"]

        if not isinstance(event_type_id, lazyT):
            event_type = itable.event_type_id.represent(event_type_id)
        else:
            event_type = event_type_id

        if priority_id and \
           priority_id != "-":
            if not isinstance(priority_id, lazyT):
                priority = itable.priority.represent(priority_id)
            else:
                priority = priority_id
        else:
            priority = T("None")

        category = itable.category.represent(row["cap_info.category"])

        response_type = itable.response_type.represent(row["cap_info.response_type"])

        subject = \
        T("%(Scope)s %(Status)s Alert") % \
            dict(Scope = s3_str(row["cap_alert.scope"]),
                 Status = s3_str(row["cap_alert.status"]))
        headline = H2(T((s3_str(row["cap_info.headline"]))))
        id = T("ID: %(Identifier)s") % dict(Identifier = s3_str(row["cap_alert.identifier"]))
        body1 = \
T("""%(Priority)s message %(MessageType)s 
in effect for %(AreaDescription)s""") % dict(\
                    Priority = s3_str(priority),
                    MessageType = s3_str(row["cap_alert.msg_type"]),
                    AreaDescription = s3_str(row["cap_area.name"]))
        body2 = \
        T("This %(Severity)s %(EventType)s is %(Urgency)s and is %(Certainty)s") %\
            dict(Severity = s3_str(row["cap_info.severity"]),
                 EventType = s3_str(event_type),
                 Urgency = s3_str(row["cap_info.urgency"]),
                 Certainty = s3_str(row["cap_info.certainty"]))
        body3 = \
T("""Message %(Identifier)s: %(EventType)s (%(Category)s) issued by 
%(SenderName)s sent at %(Date)s from %(Source)s""") % \
                 dict(Identifier = s3_str(row["cap_alert.identifier"]),
                      EventType = s3_str(event_type),
                      Category = s3_str(category),
                      SenderName = s3_str(row["cap_info.sender_name"]),
                      Date = s3_str(row["cap_alert.sent"]),
                      Source = s3_str(row["cap_alert.source"]))
        body4 = T("Alert Description: %(AreaDescription)s") % \
                dict(AreaDescription = s3_str(row["cap_area.name"]))
        body5 = T("Expected Response: %(ResponseType)s") % \
                dict(ResponseType = s3_str(response_type))
        body6 = T("Instructions: %(Instruction)s") % \
                dict(Instruction=s3_str(row["cap_info.instruction"]))
        body7 = \
T("Alert is effective from %(Effective)s and expires on %(Expires)s") % \
                dict(Effective = s3_str(row["cap_info.effective"]),
                     Expires = s3_str(row["cap_info.expires"]))
        body8 = T("For more details visit %(URL)s or contact %(Contact)s") % \
                dict(URL = s3_str(row["cap_info.web"]),
                     Contact = s3_str(row["cap_info.contact"]))
        body9 = A(T("VIEW ALERT ON THE WEB"),
                    _href = "%s/%s" % (s3_str(row["cap_info.web"]), "profile"))
        return TAG[""](HR(), BR(),
                       body9,
                       BR(), BR(),
                       subject, headline,
                       BR(),
                       id,
                       BR(), BR(),
                       body1,
                       BR(),
                       body2,
                       BR(), BR(),
                       body3,
                       BR(), BR(),
                       body4,
                       BR(), BR(),
                       body5,
                       BR(), BR(),
                       body6,
                       BR(), BR(),
                       body7,
                       BR(), BR(),
                       body8,                       
                       BR())

    # -------------------------------------------------------------------------
    def get_sms_content(row):
        """
            prepare the content for SMS
        """

        from gluon.languages import lazyT
        itable = current.s3db.cap_info
        event_type_id = row["cap_info.event_type_id"]
        priority_id = row["cap_info.priority"]

        if not isinstance(event_type_id, lazyT):
            event_type = itable.event_type_id.represent(event_type_id)
        else:
            event_type = event_type_id

        if priority_id and priority_id != "-":
            if not isinstance(priority_id, lazyT):
                priority = itable.priority.represent(priority_id)
            else:
                priority = priority_id
        else:
            priority = T("None")

        sms_body = \
T("""%(Status)s %(MessageType)s for %(AreaDescription)s with %(Priority)s
priority %(EventType)s issued by %(SenderName)s at %(Date)s (ID:%(Identifier)s)""") % \
            dict(Status = s3_str(row["cap_alert.status"]),
                 MessageType = s3_str(row["cap_alert.msg_type"]),
                 AreaDescription = s3_str(row["cap_area.name"]),
                 Priority = s3_str(priority),
                 EventType = s3_str(event_type),
                 SenderName = s3_str(row["cap_info.sender_name"]),
                 Date = s3_str(row["cap_alert.sent"]),
                 Identifier = s3_str(row["cap_alert.identifier"]))

        return sms_body

# END =========================================================================
