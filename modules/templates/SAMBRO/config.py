# -*- coding: utf-8 -*-

import json
import os

from collections import OrderedDict

from gluon import current
from gluon.html import *
from gluon.storage import Storage
from gluon.languages import lazyT

from s3 import FS, s3_str, s3_truncate, s3_utc

def config(settings):
    """
        Template settings for CAP: Common Alerting Protocol
    """

    T = current.T

## Deprecated because such edits to the title should happen in the 000_config.py file
## specific to the demo deployment and not here because if you change here it affect any
## developments and commits to git etc - nuwan at sahanafoundation dot org
    #settings.base.system_name = T("Sahana Alerting and Messaging Broker")
    #settings.base.system_name_short = T("SAMBRO")
##
    # Pre-Populate
    settings.base.prepopulate += ("SAMBRO",)
    settings.base.prepopulate_demo += ("SAMBRO/Demo",)

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
    #settings.msg.notify_subject = "%s $s %s" % (T("SAHANA"), T("Alert Notification"))

    # Notifications format
    settings.msg.notify_email_format = "html"

    # Filename for FTP
    # Characters not allowed are [\ / : * ? " < > | % .]
    # https://en.wikipedia.org/wiki/Filename
    # http://docs.attachmate.com/reflection/ftp/15.6/guide/en/index.htm?toc.htm?6503.htm
    settings.sync.upload_filename = "$s-%s" % ("recent_alert")

    # Whether to tweet alerts
    settings.cap.post_to_twitter = True

    # Whether to post alerts in facebook?
    settings.cap.post_to_facebook = True

    # ALlow RSS to use links of entry if link fails
    settings.cap.rss_use_links = True

    # SAMBRO supports ack workflow
    settings.cap.use_ack = True

    # -------------------------------------------------------------------------
    # L10n (Localization) settings
    languages = OrderedDict([
        #("ar", "Arabic"),
        ("dv", "Divehi"), # Maldives
        ("en-US", "English"),
        #("es", "Spanish"),
        #("fr", "French"),
        ("fj", "Fijian"),
        ("hi", "Hindi"),
        #("km", "Khmer"), # Cambodia
        #("mn", "Mongolian"),
        ("my", "Burmese"), # Myanmar
        ("ne", "Nepali"),
        ("th", "Thai"),
        ("tl", "Tagalog"), # Philippines
    ])
    settings.cap.languages = languages
    settings.L10n.languages = languages
    # Translate the cap_area name
    settings.L10n.translate_cap_area = True

    # Date Format
    #settings.L10n.date_format = "%a, %d %B %Y"

    # Time Format
    settings.L10n.time_format = "%H:%M:%S"

    # -------------------------------------------------------------------------
    # Messaging
    # Parser
    settings.msg.parser = "SAMBRO"

    # -------------------------------------------------------------------------
    # Organisations
    # Enable the use of Organisation Branches
    settings.org.branches = True

    # -------------------------------------------------------------------------
    def customise_msg_rss_channel_resource(r, tablename):

        # @ToDo: We won't be able to automate this as we have 2 sorts, so will need the user to select manually
        # Can we add a component for the parser for S3CSV imports?

        s3db = current.s3db
        def onaccept(form):
            # Normal onaccept
            s3db.msg_channel_onaccept(form)
            db = current.db
            table = db.msg_rss_channel
            form_vars = form.vars
            record_id = form_vars.get("id", None)
            form_type = form_vars.get("type", None)
            type = current.request.get_vars.get("type", None)
            query = (table.id == record_id)
            if type == "cap" or form_type == "cap":
                fn = "parse_rss_2_cap"
                db(query).update(type = "cap")
            else:
                fn = "parse_rss_2_cms"
                db(query).update(type = "cms")
            channel_id = db(query).select(table.channel_id,
                                          limitby=(0, 1)).first().channel_id
            # Link to Parser
            table = s3db.msg_parser
            parser_id = table.insert(channel_id=channel_id, function_name=fn, enabled=True)
            s3db.msg_parser_enable(parser_id)

            run_async = current.s3task.run_async
            # Poll
            run_async("msg_poll", args=["msg_rss_channel", channel_id])

            # Parse
            run_async("msg_parse", args=[channel_id, fn])

        s3db.configure(tablename,
                       create_onaccept = onaccept,
                       )

    settings.customise_msg_rss_channel_resource = customise_msg_rss_channel_resource

    # -------------------------------------------------------------------------
    def customise_msg_rss_channel_controller(**attr):

        s3 = current.response.s3
        channel_type = current.request.get_vars.get("type", None)
        if channel_type == "cap":
            # CAP RSS Channel
            s3.filter = (FS("type") == "cap")
            s3.crud_strings["msg_rss_channel"] = Storage(
                label_create = T("Add CAP Feed"),
                title_display = T("CAP Feed"),
                title_list = T("CAP Feeds"),
                title_update = T("Edit CAP Feed"),
                label_list_button = T("List CAP Feeds"),
                label_delete_button = T("Delete CAP Feed"),
                msg_record_created = T("CAP Feed created"),
                msg_record_modified = T("CAP Feed modified"),
                msg_record_deleted = T("CAP Feed deleted"),
                msg_list_empty = T("No CAP Feed to show"))
        else:
            # CMS RSS Channel
            s3.filter = (FS("type") == "cms")

        # Custom postp
        standard_postp = s3.postp
        def custom_postp(r, output):
            # Call standard postp
            if callable(standard_postp):
                output = standard_postp(r, output)

            if r.interactive and isinstance(output, dict):
                # Modify Open Button
                if channel_type == "cap":
                    # CAP RSS Channel
                    table = r.table
                    query = (table.deleted == False)
                    rows = current.db(query).select(table.id,
                                                    table.enabled,
                                                    )
                    restrict_e = [str(row.id) for row in rows if not row.enabled]
                    restrict_d = [str(row.id) for row in rows if row.enabled]

                    s3.actions = [{"label": s3_str(T("Open")),
                                   "_class": "action-btn edit",
                                   "url": URL(args = ["[id]", "update"],
                                              vars = {"type": "cap"},
                                              ),
                                   },
                                  {"label": s3_str(T("Delete")),
                                   "_class": "delete-btn",
                                   "url": URL(args = ["[id]", "delete"],
                                              vars = {"type": "cap"},
                                              ),
                                   },
                                  {"label": s3_str(T("Subscribe")),
                                   "_class": "action-btn",
                                   "url": URL(args = ["[id]", "enable"],
                                              vars = {"type": "cap"},
                                              ),
                                   "restrict": restrict_e,
                                   },
                                  {"label": s3_str(T("Unsubscribe")),
                                   "_class": "action-btn",
                                   "url": URL(args = ["[id]", "disable"],
                                              vars = {"type": "cap"},
                                              ),
                                   "restrict": restrict_d
                                   },
                                  ]

                    if not current.s3task._is_alive():
                        # No Scheduler Running
                        s3.actions.append({"label": s3_str(T("Poll")),
                                           "_class": "action-btn",
                                           "url": URL(args = ["[id]", "poll"],
                                                      vars = {"type": "cap"},
                                                      ),
                                           "restrict": restrict_d,
                                           })

                    if "form" in output and current.auth.s3_has_role("ADMIN"):
                        # Modify Add Button
                        add_btn = A(T("Add CAP Feed"),
                                    _class = "action-btn",
                                    _href = URL(args = ["create"],
                                                vars = {"type": "cap"},
                                                ),
                                    )
                        output["showadd_btn"] = add_btn

            return output
        s3.postp = custom_postp

        return attr

    settings.customise_msg_rss_channel_controller = customise_msg_rss_channel_controller

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

            run_async = current.s3task.run_async
            # Poll
            run_async("msg_poll", args=["msg_twitter_channel", channel_id])

            # Parse
            run_async("msg_parse", args=[channel_id, "parse_tweet"])

        s3db.configure(tablename,
                       create_onaccept = onaccept,
                       )

    settings.customise_msg_twitter_channel_resource = customise_msg_twitter_channel_resource

    # -------------------------------------------------------------------------
    def customise_org_organisation_resource(r, tablename):

        s3 = current.response.s3

        crud_strings_branch = Storage(
            label_create = T("Add Branch"),
            title_display = T("Branch Details"),
            title_list = T("Branches"),
            title_update = T("Edit Branch"),
            title_upload = T("Import Branches"),
            label_list_button = T("List Branches"),
            label_delete_button = T("Delete Branch"),
            msg_record_created = T("Branch added"),
            msg_record_modified = T("Branch updated"),
            msg_record_deleted = T("Branch deleted"),
            msg_list_empty = T("No Branches currently registered"))

        if r.component_name == "branch":
            # Make sure branch uses same form as organisation because we need CAP OID
            r.component.actuate = "replace"
            s3.crud_strings[tablename] = crud_strings_branch

        if r.method == "hierarchy":
            s3.crud_strings[tablename] = crud_strings_branch

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
    def customise_pr_person_resource(r, tablename):

        # On-delete option
        current.s3db.pr_person_id.attr.ondelete = "SET NULL"

    settings.customise_pr_person_resource = customise_pr_person_resource

    # -------------------------------------------------------------------------
    def customise_pr_contact_controller(**attr):

        s3 = current.response.s3

        # Custom prep
        standard_prep = s3.prep
        def custom_prep(r):
            # Call standard prep
            if callable(standard_prep):
                result = standard_prep(r)
            else:
                result = True

            table = r.table
            table.priority.writable = False
            table.priority.readable = False
            table.comments.writable = False
            table.comments.readable = False

            return result
        s3.prep = custom_prep

        return attr

    settings.customise_pr_contact_controller = customise_pr_contact_controller

    # -------------------------------------------------------------------------
    def customise_cap_alert_resource(r, tablename):

        T = current.T
        db = current.db
        s3db = current.s3db
        def onapprove(record):
            # Normal onapprove
            s3db.cap_alert_onapprove(record)

            run_async = current.s3task.run_async

            # Sync FTP Repository
            run_async("cap_ftp_sync")

            # @ToDo: Check for LEFT join when required
            # this is ok for now since every Alert should have an Info & an Area
            alert_id = int(record["id"])
            table = s3db.cap_alert
            itable = s3db.cap_info
            atable = s3db.cap_area
            query = (table.id == alert_id) & \
                    (table.deleted != True) & \
                    (itable.alert_id == table.id) & \
                    (itable.deleted != True) & \
                    (atable.alert_id == table.id) & \
                    (atable.deleted != True)
            resource = s3db.resource("cap_alert", filter=query)
            # Fields to extract
            fields = resource.list_fields(key="notify_fields")
            # Extract the data
            data = resource.select(fields,
                                   raw_data=True)
            # Single row as we are filtering for particular alert_id
            arow = data["rows"][0]

            # Create attachment
            cap_document_id = _get_or_create_attachment(alert_id)

            if record["scope"] != "Private" and data["numrows"] > 0:
                # Google Cloud Messaging
                stable = s3db.pr_subscription
                ctable = s3db.pr_contact

                query = (stable.pe_id == ctable.pe_id) & \
                        (ctable.contact_method == "GCM") & \
                        (ctable.value != None) & \
                        (ctable.deleted != True) & \
                        (stable.deleted != True) & \
                        (stable.method.like("%GCM%"))
                rows = db(query).select(ctable.value)
                if len(rows):
                    registration_ids = [s3_str(row.value) for row in rows]
                    title = get_email_subject(arow, system=False)
                    run_async("msg_gcm", args=[title,
                                               "%s/%s" % (s3_str(arow["cap_info.web"]), "profile"),
                                               s3_str(get_formatted_value(arow["cap_info.headline"],
                                                                          system=False)),
                                               json.dumps(registration_ids),
                                               ])
                # Twitter Post
                if settings.get_cap_post_to_twitter():
                    try:
                        import tweepy
                    except ImportError:
                        current.log.debug("tweepy module needed for sending tweets")
                    else:
                        url = "%s/%s" % (arow["cap_info.web"], "profile")
                        try:
                            from pyshorteners import Shortener
                        except ImportError:
                            pass
                        else:
                            try:
                                url = Shortener('Tinyurl', timeout=3).short(url)
                            except:
                                pass
                        twitter_text = \
("""%(status)s Alert: %(headline)s
%(sender)s: %(sender_name)s
%(website)s: %(Website)s""") % {"status": s3_str(T(arow["cap_alert.status"])),
                                           "headline": s3_str(get_formatted_value(arow["cap_info.headline"],
                                                                                  system=False)),
                                           "sender": s3_str(T("Sender")),
                                           "sender_name": s3_str(get_formatted_value(arow["cap_info.sender_name"],
                                                                                     system=False)),
                                           "website": s3_str(T("Website")),
                                           "Website": s3_str(url),
                                           }
                        try:
                            # @ToDo: Handle the multi-message nicely?
                            # @ToDo: Send resource url with tweet
                            current.msg.send_tweet(text=s3_str(twitter_text),
                                                   alert_id=alert_id,
                                                   )
                        except tweepy.error.TweepError as e:
                            current.log.debug("Sending tweets failed: %s" % e)

                # Facebook Post
                if settings.get_cap_post_to_facebook():
                    # @ToDo: post resources too?
                    content = get_facebook_content(arow)
                    try:
                        current.msg.post_to_facebook(text=content,
                                                     alert_id=alert_id,
                                                     )
                    except Exception as e:
                        current.log.debug("Posting Alert to Facebook failed: %s" % e)

            addresses = record["addresses"]
            if len(addresses):
                # First Responders
                gtable = s3db.pr_group
                mtable = s3db.pr_group_membership
                ptable = s3db.pr_person
                send_by_pe_id = current.msg.send_by_pe_id
                get_user_id = current.auth.s3_get_user_id
                query_ = (gtable.id == mtable.group_id) & \
                         (mtable.person_id == ptable.id) & \
                         (gtable.deleted != True) & \
                         (mtable.deleted != True) & \
                         (ptable.deleted != True)
                count = len(addresses)
                if count == 1:
                    query = query_ & (gtable.id == addresses[0])
                else:
                    query = query_ & (gtable.id.belongs(addresses))
                rows = db(query).select(ptable.pe_id)
                subject = get_email_subject(arow, system=False)
                if settings.get_cap_use_ack():
                    for row in rows:
                        ack_id = create_ack(alert_id, get_user_id(pe_id=row.pe_id))
                        email_content = "%s%s%s" % ("<html>",
                                                    XML(get_html_email_content(arow,
                                                                    ack_id=ack_id,
                                                                    system=False)),
                                                    "</html>")
                        sms_content = get_sms_content(arow, ack_id=ack_id, system=False)
                        send_by_pe_id(row.pe_id,
                                      subject,
                                      email_content,
                                      document_ids=cap_document_id,
                                      alert_id=alert_id,
                                      )
                        try:
                            send_by_pe_id(row.pe_id,
                                          subject,
                                          sms_content,
                                          contact_method="SMS",
                                          alert_id=alert_id,
                                          )
                        except ValueError:
                            current.log.error("No SMS Handler defined!")
                else:
                    html_content = get_html_email_content(arow, system=False)
                    email_content = "%s%s%s" % ("<html>",
                                                XML(html_content),
                                                "</html>")
                    sms_content = get_sms_content(arow, system=False)
                    for row in rows:
                        send_by_pe_id(row.pe_id,
                                      subject,
                                      email_content,
                                      document_ids=cap_document_id,
                                      alert_id=alert_id,
                                      )
                        try:
                            send_by_pe_id(row.pe_id,
                                          subject,
                                          sms_content,
                                          contact_method="SMS",
                                          alert_id=alert_id,
                                          )
                        except ValueError:
                            current.log.error("No SMS Handler defined!")

        s3db.configure(tablename,
                       onapprove = onapprove,
                       )

    settings.customise_cap_alert_resource = customise_cap_alert_resource

    # -------------------------------------------------------------------------
    def customise_cap_alert_controller(**attr):

        s3 = current.response.s3
        auth = current.auth
        if not auth.user:
            # For notifications for group
            r = current.request
            if not r.function == "public":
                if r.get_vars.format == "msg":
                    # This is called by notification
                    # The request from web looks like r.extension
                    s3.filter = (FS("scope") != "Private")
                else:
                    auth.permission.fail()

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
        role_check = has_role("ADMIN")

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
                    url = URL(c="default", f="index",
                              args=["subscriptions"],
                              vars={"subscription_id": "[id]"})
                    S3CRUD.action_buttons(r, update_url=url, read_url=url)

                if "form" in output:
                    # Modify Add Button
                    if manage_recipient and role_check:
                        # Admin based subscription
                        add_btn = A(T("Add Recipient to List"),
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

        notify_on = meta_data["notify_on"]
        last_check_time = meta_data["last_check_time"]
        rows = data["rows"]
        output = {}
        upd = [] # upd as the created alerts might be approved after some time, check is also done

        db = current.db
        atable = current.s3db.cap_alert
        if format == "text":
            # For SMS
            append_record = upd.append
            for row in rows:
                row_ = db(atable.id == row["cap_alert.id"]).select(atable.approved_on,
                                                                   limitby=(0, 1)).first()
                if row_ and row_.approved_on is not None:
                    if s3_utc(row_.approved_on) >= last_check_time:
                        sms_content = get_sms_content(row)
                        append_record(sms_content)

            if "upd" in notify_on and len(upd):
                output["upd"] = len(upd)
                output["upd_records"] = upd
            else:
                output["upd"] = None
        else:
            # HTML emails
            elements = []
            append = elements.append
            append_record = upd.append

            for row in rows:
                row_ = db(atable.id == row["cap_alert.id"]).select(atable.approved_on,
                                                                   limitby=(0, 1)).first()
                if row_ and row_.approved_on is not None:
                    if s3_utc(row_.approved_on) >= last_check_time:
                        content = get_html_email_content(row)
                        container = DIV(DIV(content))
                        append(container)
                        append(BR())
                        append_record(container)
            if "upd" in notify_on and len(upd):
                output["upd"] = len(upd)
                output["upd_records"] = DIV(*elements)
            else:
                output["upd"] = None

        output.update(meta_data)
        return output

    settings.msg.notify_renderer = custom_msg_render

    # -----------------------------------------------------------------------------
    def custom_msg_notify_subject(resource, data, meta_data):
        """
            Custom Method to subject for the email
            @param resource: the S3Resource
            @param data: the data returned from S3Resource.select
            @param meta_data: the meta data for the notification
        """

        rows = data["rows"]
        subject = "%s %s" % (settings.get_system_name_short(),
                             T("Alert Notification"))
        if len(rows) == 1:
            # Since if there are more than one row, the single email has content
            # for all rows
            atable = current.s3db.cap_alert
            row_ = current.db(atable.id == rows[0]["cap_alert.id"]).select(atable.approved_on,
                                                                           limitby=(0, 1)
                                                                           ).first()
            if row_ and row_.approved_on is not None:
                if s3_utc(row_.approved_on) >= meta_data["last_check_time"]:
                    subject = get_email_subject(rows[0])

        return subject

    settings.msg.notify_subject = custom_msg_notify_subject

    # -----------------------------------------------------------------------------
    def custom_msg_notify_attachment(resource, data, meta_data):
        """
            Custom Method to get the document_ids to be sent as attachment
            @param resource: the S3Resource
            @param data: the data returned from S3Resource.select
            @param meta_data: the meta data for the notification
        """

        rows = data["rows"]
        document_ids = []
        dappend = document_ids.append
        for row in rows:
            alert_id = row["cap_alert.id"]
            document_id = _get_or_create_attachment(alert_id)
            dappend(document_id)

        return document_ids

    settings.msg.notify_attachment = custom_msg_notify_attachment

    # -----------------------------------------------------------------------------
    def custom_msg_notify_send_data(resource, data, meta_data):
        """
            Custom Method to send data containing alert_id to the s3msg.send_by_pe_id
            @param resource: the S3Resource
            @param data: the data returned from S3Resource.select
            @param meta_data: the meta data for the notification
        """

        rows = data.rows
        data = {}
        if len(rows) == 1:
            row = rows[0]
            if "cap_alert.id" in row:
                try:
                    alert_id = int(row["cap_alert.id"])
                    data["alert_id"] = alert_id
                except ValueError:
                    pass

        return data

    settings.msg.notify_send_data = custom_msg_notify_send_data

    # -----------------------------------------------------------------------------
    def msg_send_postprocess(message_id, **data):
        """
            Custom function that links alert_id in cap module to message_id in
            message module
        """

        alert_id = data.get("alert_id", None)
        if alert_id and message_id:
            current.s3db.cap_alert_message.insert(alert_id = alert_id,
                                                  message_id = message_id)

    settings.msg.send_postprocess = msg_send_postprocess

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

        filter_options = {}

        if len(rows) > 0:
            T = current.T
            etable = s3db.event_event_type
            ptable = s3db.cap_warning_priority
            from s3 import IS_ISO639_2_LANGUAGE_CODE
            languages_dict = dict(IS_ISO639_2_LANGUAGE_CODE.language_codes())
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
                        elif prefix == "info.priority__belongs":
                            priorities_id = [int(s3_str(value)) for value in values]
                            rows_ = db(ptable.id.belongs(priorities_id)).select(ptable.name)
                            priorities = [row_.name for row_ in rows_]
                        elif prefix == "info.language__belongs":
                            languages = [s3_str(languages_dict[value]) for value in values]
                    if event_type is not None:
                        display_text = "<b>%s:</b> %s" % (T("Event Type"), event_type)
                    else:
                        display_text = "<b>%s:</b> %s" % (T("Event Type"), T("No filter"))
                    if len(priorities_id) > 0:
                        display_text = "%s<br/><b>%s</b>: %s" % (display_text, T("Priorities"), ", ".join(priorities))
                    else:
                        display_text = "%s<br/><b>%s:</b> %s" % (display_text, T("Priorities"), T("No filter"))
                    if len(languages) > 0:
                        display_text = "%s<br/><b>%s:</b> %s" % (display_text, T("Languages"), ", ".join(languages))
                    else:
                        display_text = "%s<br/><b>%s:</b> %s" % (display_text, T("Languages"), T("No filter"))
                    filter_options[row["pr_subscription.filter_id"]] = display_text
                else:
                    filter_options[row["pr_subscription.filter_id"]] = T("No filters")

        return filter_options

    # -------------------------------------------------------------------------
    def get_html_email_content(row, ack_id=None, system=True):
        """
            prepare the content for html email

            @param row: the row from which the email will be constructed
            @param ack_id: cap_alert_ack.id for including the acknowledgement link
            @param system: is this system notification email or email for first responders
        """

        itable = current.s3db.cap_info
        event_type_id = row["cap_info.event_type_id"]
        priority_id = row["cap_info.priority"]
        response_type = row["_row"]["cap_info.response_type"] if system else row["cap_info.response_type"]
        instruction = row["_row"]["cap_info.instruction"] if system else row["cap_info.instruction"]
        description = row["_row"]["cap_info.description"] if system else row["cap_info.description"]
        status = row["cap_alert.status"]
        msg_type = row["cap_alert.msg_type"]
        url = "%s/%s" % (row["cap_info.web"], "profile")
        try:
            from pyshorteners import Shortener
        except ImportError:
            pass
        else:
            try:
                url = Shortener('Tinyurl', timeout=3).short(url)
            except:
                pass

        if event_type_id and event_type_id != current.messages["NONE"]:
            if not isinstance(event_type_id, lazyT) and \
               not isinstance(event_type_id, DIV):
                event_type = itable.event_type_id.represent(event_type_id)
            else:
                event_type = event_type_id
        else:
            event_type = T("None")

        if priority_id and priority_id != current.messages["NONE"]:
            if not isinstance(priority_id, lazyT) and \
               not isinstance(priority_id, DIV):
                priority = itable.priority.represent(priority_id)
            else:
                priority = priority_id
        else:
            priority = T("Alert")

        email_content = TAG[""](HR(), BR(),
                         B(s3_str("%s %s %s" % (T(status.upper()),
                                                T(status.upper()),
                                                T(status.upper()))))
                         if status != "Actual" else "",
                         BR() if status != "Actual" else "",
                         BR() if status != "Actual" else "",
                         A(T("VIEW ALERT ON THE WEB"), _href = s3_str(url)),
                         BR(), BR(),
                         B(s3_str("%s %s %s %s" % (T(row["cap_alert.scope"]),
                                                   T(status),
                                                   T("Alert") if msg_type != "Alert" else "",
                                                   s3_str(msg_type)
                                                   ))),
                         H2(T(s3_str(get_formatted_value(row["cap_info.headline"],
                                                         system=system)))),
                         BR(),
                         XML("%(label)s: %(identifier)s" %
                         {"label": B(T("ID")),
                          "identifier": s3_str(row["cap_alert.identifier"])
                          }),
                         BR(), BR(),
                         T("""%(priority)s message %(message_type)s in effect for %(area_description)s""") % \
                         {"priority": s3_str(priority),
                          "message_type": s3_str(msg_type),
                          "area_description": s3_str(get_formatted_value(row["cap_area.name"],
                                                                         system=system)),
                         },
                         BR(), BR(),
                         T("This %(severity)s %(event_type)s is %(urgency)s and is %(certainty)s") %\
                         {"severity": s3_str(row["cap_info.severity"]),
                          "event_type": s3_str(event_type),
                          "urgency": s3_str(row["cap_info.urgency"]),
                          "certainty": s3_str(row["cap_info.certainty"]),
                          },
                         BR(), BR(),
                         T("""Message %(identifier)s: %(event_type)s (%(category)s) issued by %(sender_name)s sent at %(date)s from %(source)s""") % \
                         {"identifier": s3_str(row["cap_alert.identifier"]),
                          "event_type": s3_str(event_type),
                          "category": s3_str(get_formatted_value(row["cap_info.category"],
                                                                 represent = itable.category.represent,
                                                                 system=system)),
                          "sender_name": s3_str(get_formatted_value(row["cap_info.sender_name"],
                                                                    system=system)),
                          "date": s3_str(get_formatted_value(row["cap_alert.sent"],
                                                             represent = current.s3db.cap_alert.sent.represent,
                                                             system=system)),
                          "source": s3_str(row["cap_alert.source"]),
                          },
                         BR(),
                         BR() if description else "",
                         XML("%(label)s: %(alert_description)s" %
                         {"label": B(T("Alert Description")),
                          "alert_description": s3_str(get_formatted_value(description,
                                                                          system=False,
                                                                          ul=True)),
                          })
                         if description else "",
                         BR() if not isinstance(description, list) else "",
                         BR() if response_type else "",
                         XML(T("%(label)s: %(response_type)s") %
                         {"label": B(T("Expected Response")),
                          "response_type": s3_str(get_formatted_value(response_type,
                                                                      represent = itable.response_type.represent,
                                                                      system=False,
                                                                      ul=True)),
                          })
                         if response_type else "",
                         BR() if not isinstance(response_type, list) else "",
                         BR() if instruction else "",
                         XML(T("%(label)s: %(instruction)s") %
                         {"label": B(T("Instructions")),
                          "instruction": s3_str(get_formatted_value(instruction,
                                                                    system=False,
                                                                    ul=True)),
                          })
                         if instruction else "",
                         BR() if not isinstance(instruction, list) else "",
                         BR(),
                         T("Alert is effective from %(effective)s and expires on %(expires)s") % \
                         {"effective": s3_str(get_formatted_value(row["cap_info.effective"],
                                                                  represent = itable.effective.represent,
                                                                  system=system)),
                          "expires": s3_str(get_formatted_value(row["cap_info.expires"],
                                                                represent = itable.expires.represent,
                                                                system=system)),
                          },
                         BR(), BR(),
                         T("For more details visit %(url)s or contact %(contact)s") % \
                         {"url": s3_str(url),
                          "contact": s3_str(get_formatted_value(row["cap_info.contact"],
                                                                system=system)),
                          },
                         BR(), BR(),
                         T("To acknowledge the alert, use the following link: %(ack_link)s") % \
                         {"ack_link": "%s%s" % (current.deployment_settings.get_base_public_url(),
                                                URL(c="cap", f="alert_ack", args=[ack_id, "update"])),
                          } if ack_id else "",
                         BR() if ack_id else "",
                         BR() if ack_id else "",
                         B(s3_str("%s %s %s" % (T(status.upper()),
                                                T(status.upper()),
                                                T(status.upper()))))
                         if status != "Actual" else "",
                         )

        return email_content

    # -------------------------------------------------------------------------
    def get_email_subject(row, system=True):
        """
            Prepare the subject for Email
        """

        itable = current.s3db.cap_info
        event_type_id = row["cap_info.event_type_id"]
        msg_type = T(row["cap_alert.msg_type"])

        if event_type_id and event_type_id != current.messages["NONE"]:
            if not isinstance(event_type_id, lazyT) and \
               not isinstance(event_type_id, DIV):
                event_type = itable.event_type_id.represent(event_type_id)
            else:
                event_type = event_type_id
        else:
            event_type = T("None")

        subject = "[%s] %s %s" % (get_formatted_value(row["cap_info.sender_name"],
                                                      system=system),
                                  event_type,
                                  msg_type)
        # RFC 2822
        return s3_str(s3_truncate(subject, length=78))

    # -------------------------------------------------------------------------
    def get_sms_content(row, ack_id=None, system=True):
        """
            Prepare the content for SMS

            @param row: the row from which the sms will be constructed
            @param ack_id: cap_alert_ack.id for including the acknowledgement link
            @param system: is this system notification email or email for first responders
        """

        itable = current.s3db.cap_info
        event_type_id = row["cap_info.event_type_id"]
        priority_id = row["cap_info.priority"]
        url = "%s/%s" % (row["cap_info.web"], "profile")
        try:
            from pyshorteners import Shortener
        except ImportError:
            pass
        else:
            try:
                url = Shortener('Tinyurl', timeout=3).short(url)
            except:
                pass

        if not isinstance(event_type_id, lazyT) and \
           not isinstance(event_type_id, DIV):
            event_type = itable.event_type_id.represent(event_type_id)
        else:
            event_type = event_type_id

        if priority_id and priority_id != current.messages["NONE"]:
            if not isinstance(priority_id, lazyT) and \
               not isinstance(priority_id, DIV):
                priority = itable.priority.represent(priority_id)
            else:
                priority = priority_id
        else:
            priority = T("Unknown")

        if ack_id:
            sms_body = \
T("""%(status)s %(message_type)s for %(area_description)s with %(priority)s priority %(event_type)s issued by %(sender_name)s at %(date)s (ID:%(identifier)s) \nTo acknowledge the alert, click: %(ack_link)s \n\n""") % \
                {"status": s3_str(row["cap_alert.status"]),
                 "message_type": s3_str(row["cap_alert.msg_type"]),
                 "area_description": s3_str(get_formatted_value(row["cap_area.name"],
                                                                system=system)),
                 "priority": s3_str(priority),
                 "event_type": s3_str(event_type),
                 "sender_name": s3_str(get_formatted_value(row["cap_info.sender_name"],
                                                           system=system)),
                 "date": s3_str(row["cap_alert.sent"]),
                 "identifier": s3_str(row["cap_alert.identifier"]),
                 "ack_link": "%s%s" % (current.deployment_settings.get_base_public_url(),
                                       URL(c="cap", f="alert_ack", args=[ack_id, "update"])),
                 }
        else:
            sms_body = \
T("""%(status)s %(message_type)s for %(area_description)s with %(priority)s priority %(event_type)s issued by %(sender_name)s at %(date)s (ID:%(identifier)s).  \nView Alert in web at %(profile)s \n\n""") % \
                {"status": s3_str(row["cap_alert.status"]),
                 "message_type": s3_str(row["cap_alert.msg_type"]),
                 "area_description": s3_str(get_formatted_value(row["cap_area.name"],
                                                                system=system)),
                 "priority": s3_str(priority),
                 "event_type": s3_str(event_type),
                 "sender_name": s3_str(get_formatted_value(row["cap_info.sender_name"],
                                                           system=system)),
                 "date": s3_str(row["cap_alert.sent"]),
                 "identifier": s3_str(row["cap_alert.identifier"]),
                 "profile": s3_str(url),
                 }

        return s3_str(sms_body)

    # -------------------------------------------------------------------------
    def get_facebook_content(row, system=False):
        """
            prepare the content for facebook post
        """

        itable = current.s3db.cap_info
        event_type_id = row["cap_info.event_type_id"]
        priority_id = row["cap_info.priority"]
        response_type = row["cap_info.response_type"]
        instruction = row["cap_info.instruction"]
        description = row["cap_info.description"]
        url = "%s/%s" % (row["cap_info.web"], "profile")
        try:
            from pyshorteners import Shortener
            try:
                url = Shortener('Tinyurl', timeout=3).short(url)
            except:
                pass
        except ImportError:
            pass

        if event_type_id and event_type_id != current.messages["NONE"]:
            if not isinstance(event_type_id, lazyT):
                event_type = itable.event_type_id.represent(event_type_id)
            else:
                event_type = event_type_id
        else:
            event_type = T("None")

        if priority_id and priority_id != current.messages["NONE"]:
            if not isinstance(priority_id, lazyT):
                priority = itable.priority.represent(priority_id)
            else:
                priority = priority_id
        else:
            priority = T("Alert")

        facebook_content = [
                T("%(scope)s %(status)s Alert") % \
                {"scope": s3_str(row["cap_alert.scope"]),
                 "status": s3_str(row["cap_alert.status"]),
                 },
                T((s3_str(get_formatted_value(row["cap_info.headline"],
                                              system=system)))),
                T("ID: %(identifier)s") % {"identifier": s3_str(row["cap_alert.identifier"])},
                T("""%(priority)s message %(message_type)s in effect for %(area_description)s""") % \
                {"priority": s3_str(priority),
                 "message_type": s3_str(row["cap_alert.msg_type"]),
                 "area_description": s3_str(get_formatted_value(row["cap_area.name"],
                                                                system=system)),
                 },
                T("This %(severity)s %(event_type)s is %(urgency)s and is %(certainty)s") % \
                {"severity": s3_str(row["cap_info.severity"]),
                 "event_type": s3_str(event_type),
                 "urgency": s3_str(row["cap_info.urgency"]),
                 "certainty": s3_str(row["cap_info.certainty"]),
                 },
                T("""Message %(identifier)s: %(event_type)s (%(category)s) issued by %(sender_name)s sent at %(date)s from %(source)s""") % \
                {"identifier": s3_str(row["cap_alert.identifier"]),
                 "event_type": s3_str(event_type),
                 "category": s3_str(get_formatted_value(row["cap_info.category"],
                                                        represent = itable.category.represent,
                                                        system=system)),
                 "sender_name": s3_str(get_formatted_value(row["cap_info.sender_name"],
                                                           system=system)),
                 "date": s3_str(get_formatted_value(row["cap_alert.sent"],
                                                    represent = current.s3db.cap_alert.sent.represent,
                                                    system=system)),
                 "source": s3_str(row["cap_alert.source"]),
                 },
                T("Alert Description: %(alert_description)s") % \
                {"alert_description": s3_str(get_formatted_value(description,
                                                                 system=system)),
                 } if description else "",
                T("Expected Response: %(response_type)s") % \
                {"response_type": s3_str(get_formatted_value(response_type,
                                                             represent = itable.response_type.represent,
                                                             system=system)),
                 } if response_type else "",
                T("Instruction: %(instruction)s") % \
                {"instruction": s3_str(get_formatted_value(instruction, system=system))}
                if instruction else "",
                T("Alert is effective from %(effective)s and expires on %(expires)s") % \
                {"effective": s3_str(get_formatted_value(row["cap_info.effective"],
                                                         represent = itable.effective.represent,
                                                         system=system)),
                 "expires": s3_str(get_formatted_value(row["cap_info.expires"],
                                                       represent = itable.expires.represent,
                                                       system=system)),
                 },
                T("For more details visit %(url)s or contact %(contact)s") % \
                {"url": s3_str(url),
                 "contact": s3_str(get_formatted_value(row["cap_info.contact"], system=system)),
                 }
                if row["cap_info.contact"] else
                T("For more details visit %(url)s") % \
                {"url": s3_str(url)}
                ]

        return "\n\n".join(s3_str(item) for item in facebook_content if item!="")

    # -------------------------------------------------------------------------
    def create_ack(alert_id, user_id):
        """
            Create a specific acknowledgement
            @param alert_id: The particular alert ID for acknowledging
            @param user_id: The user ID who owns the record

            @todo: use location where the alert is targeted for
        """

        ack_data = {"alert_id": alert_id,
                    "owned_by_user": int(user_id),
                    }
        ack_table = current.s3db.cap_alert_ack
        ack_id = ack_table.insert(**ack_data)
        current.auth.s3_set_record_owner(ack_table, ack_id)
        # Uncomment this when there is onaccept hook
        #s3db.onaccept(ack_table, dict(id=ack_id))

        return ack_id

    # -------------------------------------------------------------------------
    def get_formatted_value(value,
                            represent=None,
                            system=True,
                            ul=False):
        """ For non-system notification returns the formatted represented value
        """

        if not value:
            return None
        else:
            if system:
                # For system notification value is already properly formatted for representation
                return value
            else:
                if isinstance(value, list):
                    nvalue = []
                    for value_ in value:
                        if value_:
                            if represent:
                                nvalue.append(represent(value_))
                            else:
                                nvalue.append(value_)
                    if len(nvalue):
                        if ul:
                            nvalue = UL(nvalue)
                        else:
                            nvalue = ", ".join(nvalue)
                    else:
                        return None
                else:
                    if represent:
                        nvalue = represent(value)
                    else:
                        nvalue = value

                return nvalue

    # -------------------------------------------------------------------------
    def _get_or_create_attachment(alert_id):
        """
            Retrieve the CAP attachment for the alert_id if present
            else creates CAP file as attachment to be sent with the email
            returns the document_id for the CAP file
        """

        s3db = current.s3db
        rtable = s3db.cap_resource
        dtable = s3db.doc_document
        query = (rtable.alert_id == alert_id) & \
                (rtable.mime_type == "cap") & \
                (rtable.deleted != True) & \
                (dtable.doc_id == rtable.doc_id) & \
                (dtable.deleted != True)
        row = current.db(query).select(dtable.id, limitby=(0, 1)).first()
        if row and row.id:
            return row.id

        request = current.request
        auth = current.auth
        path_join = os.path.join

        # Create the cap_resource table
        record = {"alert_id": alert_id,
                  "resource_desc": T("CAP XML File"),
                  "mime_type": "cap" # Hard coded to separate from attachment from user
                  }
        resource_id = rtable.insert(**record)
        record["id"] = resource_id
        s3db.update_super(rtable, record)
        doc_id = record["doc_id"]
        auth.s3_set_record_owner(rtable, resource_id)
        auth.s3_make_session_owner(rtable, resource_id)
        s3db.onaccept("cap_resource", record, method="create")

        resource = s3db.resource("cap_alert")
        resource.add_filter(FS("id") == alert_id)
        cap_xml = resource.export_xml(stylesheet=path_join(request.folder,
                                                           "static",
                                                           "formats",
                                                           "cap",
                                                           "export.xsl"),
                                      pretty_print=True)
        file_path = path_join(request.folder,
                              "uploads",
                              "%s_%s.xml" % ("cap_alert", str(alert_id)))
        file = open(file_path, "w+")
        file.write(cap_xml)
        file.close()

        # Create doc_document record
        dtable = s3db.doc_document
        file = open(file_path, "a+")
        document_id = dtable.insert(**{"file": file, "doc_id": doc_id})

        file.close()
        os.remove(file_path)

        return document_id

# END =========================================================================
