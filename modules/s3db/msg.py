# -*- coding: utf-8 -*-

""" Sahana Eden Messaging Model

    @copyright: 2009-2013 (c) Sahana Software Foundation
    @license: MIT

    Permission is hereby granted, free of charge, to any person
    obtaining a copy of this software and associated documentation
    files (the "Software"), to deal in the Software without
    restriction, including without limitation the rights to use,
    copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the
    Software is furnished to do so, subject to the following
    conditions:

    The above copyright notice and this permission notice shall be
    included in all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
    EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
    OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
    NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
    HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
    WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
    OTHER DEALINGS IN THE SOFTWARE.
"""

__all__ = ["S3ChannelModel",
           "S3MessageModel",
           "S3EmailModel",
           "S3MCommonsModel",
           "S3ParsingModel",
           "S3RSSModel",
           "S3SMSModel",
           "S3SMSOutboundModel",
           "S3SubscriptionModel",
           "S3TropoModel",
           "S3TwilioModel",
           "S3TwitterModel",
           "S3TwitterSearchModel",
           "S3XFormsModel",
           "S3BaseStationModel",
           "msg_search_subscription_notifications",
           ]

from gluon import *
from gluon.storage import Storage
from ..s3 import *

# =============================================================================
class S3ChannelModel(S3Model):
    """
        Messaging Channels
        - all Inbound & Outbound channels for messages are instances of this
          super-entity
    """

    names = ["msg_channel",
             "msg_channel_limit",
             "msg_channel_status",
             "msg_channel_id",
             "msg_channel_enable",
             "msg_channel_disable",
             "msg_channel_enable_interactive",
             "msg_channel_disable_interactive",
             "msg_channel_onaccept",
             ]

    def model(self):

        T = current.T

        define_table = self.define_table

        #----------------------------------------------------------------------
        # Super entity: msg_channel
        #
        channel_types = Storage(msg_email_channel = T("Email (Inbound)"),
                                # @ToDo:
                                #msg_facebook_channel = T("Facebook"),
                                msg_mcommons_channel = T("Mobile Commons (Inbound)"),
                                msg_sms_modem_channel = T("SMS Modem"),
                                msg_sms_webapi_channel = T("SMS WebAPI (Outbound)"),
                                msg_sms_smtp_channel = T("SMS via SMTP (Outbound)"),
                                msg_tropo_channel = T("Tropo"),
                                msg_twilio_channel = T("Twilio (Inbound)"),
                                msg_twitter_channel = T("Twitter"),
                                )

        tablename = "msg_channel"
        table = self.super_entity(tablename, "channel_id",
                                  channel_types,
                                  Field("name",
                                        #label = T("Name"),
                                        ),
                                  Field("description",
                                        #label = T("Description"),
                                        ),
                                  Field("enabled", "boolean",
                                        #label = T("Enabled?")
                                        #represent = s3_yes_no_represent,
                                        ),
                                  # @ToDo: Indicate whether channel can be used for Inbound or Outbound
                                  #Field("inbound", "boolean",
                                  #      label = T("Inbound?")),
                                  #Field("outbound", "boolean",
                                  #      label = T("Outbound?")),
                                  )

        table.instance_type.readable = True

        # Reusable Field
        channel_id = S3ReusableField("channel_id", table,
                                     requires = IS_NULL_OR(
                                        IS_ONE_OF_EMPTY(db, "msg_channel.id")),
                                     represent = S3Represent(lookup=tablename),
                                     ondelete = "SET NULL")

        # ---------------------------------------------------------------------
        # Channel Limit
        #  Used to limit the number of emails sent from the system
        #  - works by simply recording an entry for the timestamp to be checked against
        #
        # - currently just used by msg.send_email()
        #
        tablename = "msg_channel_limit"
        table = define_table(tablename,
                             # @ToDo: Make it per-channel
                             #channel_id(),
                             *s3_timestamp())

        # ---------------------------------------------------------------------
        # Channel Status
        #  Used to record errors encountered in the Channel
        #
        tablename = "msg_channel_status"
        table = define_table(tablename,
                             channel_id(),
                             Field("status",
                                   #label = T("Status")
                                   #represent = s3_yes_no_represent,
                                   ),
                             *s3_meta_fields())

        # ---------------------------------------------------------------------
        return dict(msg_channel_id = channel_id,
                    msg_channel_enable = self.channel_enable,
                    msg_channel_disable = self.channel_disable,
                    msg_channel_enable_interactive = self.channel_enable_interactive,
                    msg_channel_disable_interactive = self.channel_disable_interactive,
                    msg_channel_onaccept = self.channel_onaccept,
                    msg_channel_poll = self.channel_poll,
                    )

    # -----------------------------------------------------------------------------
    @staticmethod
    def channel_enable(tablename, channel_id):
        """
            Enable a Channel
            - Schedule a Poll for new messages

            CLI API for shell scripts & to be called by S3Method
        """

        db = current.db
        s3db = current.s3db
        table = s3db.table(tablename)
        record = db(table.channel_id == channel_id).select(table.id, # needed for update_record
                                                           table.enabled,
                                                           limitby=(0, 1),
                                                           ).first()
        if not record.enabled:
            # Flag it as enabled
            # Update Instance
            record.update_record(enabled = True)
            # Update Super
            s3db.update_super(table, record)

        # Do we have an existing Task?
        ttable = db.scheduler_task
        args = '["%s", %s]' % (tablename, channel_id)
        query = ((ttable.function_name == "msg_poll") & \
                 (ttable.args == args) & \
                 (ttable.status.belongs(["RUNNING", "QUEUED", "ALLOCATED"])))
        exists = db(query).select(ttable.id,
                                  limitby=(0, 1)).first()
        if exists:
            return "Channel already enabled"
        else:
            current.s3task.schedule_task("msg_poll",
                                         args=[tablename, channel_id],
                                         period=300,  # seconds
                                         timeout=300, # seconds
                                         repeats=0    # unlimited
                                         )
            return "Channel enabled"

    # -----------------------------------------------------------------------------
    @staticmethod
    def channel_enable_interactive(r, **attr):
        """
            Enable a Channel
            - Schedule a Poll for new messages

            S3Method for interactive requests
        """

        tablename = r.tablename
        result = current.s3db.msg_channel_enable(tablename, r.record.channel_id)
        current.session.confirmation = result
        fn = tablename.split("_", 1)[1]
        redirect(URL(f=fn))

    # -----------------------------------------------------------------------------
    @staticmethod
    def channel_disable(tablename, channel_id):
        """
            Disable a Channel
            - Remove schedule for Polling for new messages

            CLI API for shell scripts & to be called by S3Method
        """
    
        db = current.db
        s3db = current.s3db
        table = s3db.table(tablename)
        record = db(table.channel_id == channel_id).select(table.id, # needed for update_record
                                                           table.enabled,
                                                           limitby=(0, 1),
                                                           ).first()
        if record.enabled:
            # Flag it as disabled
            # Update Instance
            record.update_record(enabled = False)
            # Update Super
            s3db.update_super(table, record)

        # Do we have an existing Task?
        ttable = db.scheduler_task
        args = '["%s", %s]' % (tablename, channel_id)
        query = ((ttable.function_name == "msg_poll") & \
                 (ttable.args == args) & \
                 (ttable.status.belongs(["RUNNING", "QUEUED", "ALLOCATED"])))
        exists = db(query).select(ttable.id,
                                  limitby=(0, 1)).first()
        if exists:
            # Disable all
            db(query).update(status="STOPPED")
            return "Channel disabled"
        else:
            return "Channel already disabled"

    # -----------------------------------------------------------------------------
    @staticmethod
    def channel_disable_interactive(r, **attr):
        """
            Disable a Channel
            - Remove schedule for Polling for new messages

            S3Method for interactive requests
        """

        tablename = r.tablename
        result = current.s3db.msg_channel_disable(tablename, r.record.channel_id)
        current.session.confirmation = result
        fn = tablename.split("_", 1)[1]
        redirect(URL(f=fn))

    # -------------------------------------------------------------------------
    @staticmethod
    def channel_onaccept(form):
        """
            Process the Enabled Flag
        """

        if form.record:
            # Update form
            # process of changed
            if form.record.enabled and not form.vars.enabled:
                current.s3db.msg_channel_disable(form.table._tablename,
                                                 form.vars.channel_id)
            elif form.vars.enabled and not form.record.enabled:
                current.s3db.msg_channel_enable(form.table._tablename,
                                                form.vars.channel_id)
        else:
            # Create form
            # Process only if enabled
            if form.vars.enabled:
                current.s3db.msg_channel_enable(form.table._tablename,
                                                form.vars.channel_id)

    # -----------------------------------------------------------------------------
    @staticmethod
    def channel_poll(r, **attr):
        """
            Poll a Channel for new messages

            S3Method for interactive requests
        """

        tablename = r.tablename
        current.s3task.async("msg_poll", args=[tablename, r.record.channel_id])
        current.session.confirmation = \
            current.T("The poll request has been submitted, so new messages should appear shortly - refresh to see them")
        if tablename == "msg_email_channel":
            fn = "email_inbox"
        elif tablename == "msg_mcommons_channel":
            fn = "sms_inbox"
        elif tablename == "msg_rss_channel":
            fn = "rss"
        elif tablename == "msg_twilio_channel":
            fn = "sms_inbox"
        elif tablename == "msg_twitter_channel":
            fn = "twitter_inbox"
        else:
            return "Unsupported channel: %s" % tablename

        redirect(URL(f=fn))

# =============================================================================
class S3MessageModel(S3Model):
    """
        Messages
    """

    names = ["msg_message",
             "msg_message_id",
             "msg_message_represent",
             "msg_outbox",
             ]

    def model(self):

        T = current.T
        db = current.db

        UNKNOWN_OPT = current.messages.UNKNOWN_OPT

        configure = self.configure
        define_table = self.define_table

        # Message priority
        msg_priority_opts = {3 : T("High"),
                             2 : T("Medium"),
                             1 : T("Low"),
                             }

        # ---------------------------------------------------------------------
        # Message Super Entity - all Inbound & Outbound Messages
        #

        message_types = Storage(msg_email = T("Email"),
                                msg_rss = T("RSS"),
                                msg_sms = T("SMS"),
                                msg_twitter = T("Twitter"),
                                msg_twitter_result = T("Twitter Search Results"),
                                )

        tablename = "msg_message"
        table = self.super_entity(tablename, "message_id",
                                  message_types,
                                  # Knowing which Channel Incoming Messages
                                  # came in on allows correlation to Outbound
                                  # messages (campaign_message, deployment_alert, etc)
                                  self.msg_channel_id(),
                                  Field("body", "text",
                                        label = T("Message"),
                                        ),
                                  Field("from_address",
                                        label = T("From"),
                                        ),
                                  Field("to_address",
                                        label = T("To"),
                                        ),
                                  Field("inbound", "boolean",
                                        default = False,
                                        represent = lambda direction: \
                                        (direction and [T("In")] or \
                                                       [T("Out")])[0],
                                        label = T("Direction")),
                                  )

        table.instance_type.readable = True
        table.instance_type.writable = True

        configure(tablename,
                  list_fields=["instance_type",
                               "from_address",
                               "to_address",
                               "body",
                               "inbound",
                               ])

        # Reusable Field
        message_represent = S3Represent(lookup=tablename, fields=["body"])
        message_id = S3ReusableField("message_id", table,
                                     requires = IS_NULL_OR(
                                        IS_ONE_OF_EMPTY(db, "msg_message.id")),
                                     represent = message_represent,
                                     ondelete = "RESTRICT")

        # ---------------------------------------------------------------------
        # Outbound Messages
        # ---------------------------------------------------------------------
        # Show only the supported messaging methods
        MSG_CONTACT_OPTS = current.msg.MSG_CONTACT_OPTS

        # Maximum number of retries to send a message
        MAX_SEND_RETRIES = current.deployment_settings.get_msg_max_send_retries()

        # Valid message outbox statuses
        MSG_STATUS_OPTS = {1 : T("Unsent"),
                           2 : T("Sent"),
                           3 : T("Draft"),
                           4 : T("Invalid"),
                           5 : T("Failed"),
                           }

        opt_msg_status = S3ReusableField("status", "integer",
                                         notnull=True,
                                         requires = IS_IN_SET(MSG_STATUS_OPTS,
                                                              zero=None),
                                         default = 1,
                                         label = T("Status"),
                                         represent = lambda opt: \
                                                     MSG_STATUS_OPTS.get(opt,
                                                                 UNKNOWN_OPT))

        # Outbox - needs to be separate to Message since a single message
        # sent needs different outbox entries for each recipient
        tablename = "msg_outbox"
        table = define_table(tablename,
                             # FK not instance
                             message_id(),
                             # Person/Group to send the message out to:
                             self.super_link("pe_id", "pr_pentity"),
                             # If set used instead of picking up from pe_id:
                             Field("address"),
                             Field("pr_message_method", length=32,
                                   requires = IS_IN_SET(MSG_CONTACT_OPTS,
                                                        zero=None),
                                   default = "EMAIL",
                                   label = T("Contact Method"),
                                   represent = lambda opt: \
                                               MSG_CONTACT_OPTS.get(opt,
                                                            UNKNOWN_OPT)),
                             opt_msg_status(),
                             # Used to loop through a PE to get it's members
                             Field("system_generated", "boolean",
                                   default=False),
                             # Give up if we can't send after MAX_RETRIES
                             Field("retries", "integer",
                                   default=MAX_SEND_RETRIES,
                                   readable=False,
                                   writable=False),
                             *s3_meta_fields())

        configure(tablename,
                  orderby = ~table.created_on,
                  list_fields=["id",
                               "message_id",
                               "pe_id",
                               "status",
                               ])

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        return dict(msg_message_id = message_id,
                    msg_message_represent = message_represent,
                    )

# =============================================================================
class S3EmailModel(S3ChannelModel):
    """
        Email
            InBound Channels
                Outbound Email is currently handled via deployment_settings
            InBox/OutBox
    """

    names = ["msg_email_channel",
             "msg_email",
             ]

    def model(self):

        T = current.T

        configure = self.configure
        define_table = self.define_table
        set_method = self.set_method
        super_link = self.super_link

        # ---------------------------------------------------------------------
        # Email Inbound Channels
        #
        tablename = "msg_email_channel"
        table = define_table(tablename,
                             # Instance
                             super_link("channel_id", "msg_channel"),
                             Field("name"),
                             Field("description"),
                             Field("enabled", "boolean",
                                   label = T("Enabled?"),
                                   represent = s3_yes_no_represent,
                                   ),
                             Field("server"),
                             Field("protocol",
                                   requires = IS_IN_SET(["imap", "pop3"],
                                                        zero=None)),
                             Field("use_ssl", "boolean"),
                             Field("port", "integer"),
                             Field("username"),
                             Field("password", "password", length=64,
                                   readable = False,
                                   requires=IS_NOT_EMPTY()),
                             # Set true to delete messages from the remote
                             # inbox after fetching them.
                             Field("delete_from_server", "boolean"),
                             *s3_meta_fields())

        configure(tablename,
                  super_entity = "msg_channel",
                  onaccept = self.msg_channel_onaccept,
                  )

        set_method("msg", "email_channel",
                   method="enable",
                   action=self.msg_channel_enable_interactive)

        set_method("msg", "email_channel",
                   method="disable",
                   action=self.msg_channel_disable_interactive)

        set_method("msg", "email_channel",
                   method="poll",
                   action=self.msg_channel_poll)

        # ---------------------------------------------------------------------
        # Email Messages: InBox & Outbox
        #
        sender = current.deployment_settings.get_mail_sender()

        tablename = "msg_email"
        table = define_table(tablename,
                             # Instance
                             super_link("message_id", "msg_message"),
                             self.msg_channel_id(),
                             Field("subject", length=78,    # RFC 2822
                                   label = T("Subject")
                                   ),
                             Field("body", "text",
                                   label = T("Message")
                                   ),
                             Field("from_address", #notnull=True,
                                   default = sender,
                                   label = T("Sender"),
                                   requires = IS_EMAIL()
                                   ),
                             Field("to_address",
                                   label = T("To"),
                                   requires = IS_EMAIL()
                                   ),
                             Field("raw", "text",
                                   label = T("Message Source")
                                   ),
                             Field("inbound", "boolean",
                                   default = False,
                                   represent = lambda direction: \
                                       (direction and [T("In")] or \
                                                      [T("Out")])[0],
                                   label = T("Direction")
                                   ),
                             *s3_meta_fields())

        configure(tablename,
                  super_entity = "msg_message",
                  )

        # ---------------------------------------------------------------------
        return dict()
        
# =============================================================================
class S3MCommonsModel(S3ChannelModel):
    """
        Mobile Commons Inbound SMS Settings
        - Outbound can use Web API
    """

    names = ["msg_mcommons_channel",
             ]

    def model(self):

        #T = current.T

        define_table = self.define_table
        set_method = self.set_method

        # ---------------------------------------------------------------------
        tablename = "msg_mcommons_channel"
        table = define_table(tablename,
                             self.super_link("channel_id", "msg_channel"),
                             Field("name"),
                             Field("description"),
                             Field("enabled", "boolean",
                                   #label = T("Enabled?"),
                                   represent = s3_yes_no_represent,
                                   ),
                             Field("campaign_id", length=128, unique=True,
                                   requires=IS_NOT_EMPTY()),
                             Field("url",
                                   default = \
                                   "https://secure.mcommons.com/api/messages",
                                   requires = IS_URL()
                                   ),
                             Field("username",
                                   requires=IS_NOT_EMPTY()),
                             Field("password", "password",
                                   readable = False,
                                   requires=IS_NOT_EMPTY()),
                             Field("query"),
                             Field("timestmp", "datetime",
                                   writable=False),
                             *s3_meta_fields())

        self.configure(tablename,
                       super_entity = "msg_channel",
                       onaccept = self.msg_channel_onaccept,
                       )

        set_method("msg", "mcommons_channel",
                   method="enable",
                   action=self.msg_channel_enable_interactive)

        set_method("msg", "mcommons_channel",
                   method="disable",
                   action=self.msg_channel_disable_interactive)

        set_method("msg", "mcommons_channel",
                   method="poll",
                   action=self.msg_channel_poll)

        # ---------------------------------------------------------------------
        return dict()

# =============================================================================
class S3ParsingModel(S3Model):
    """
        Message Parsing Model
    """

    names = ["msg_parser",
             "msg_parsing_status",
             "msg_session",
             "msg_keyword",
             "msg_sender",
             "msg_parser_enabled",
             "msg_parser_enable",
             "msg_parser_disable",
             "msg_parser_enable_interactive",
             "msg_parser_disable_interactive",
             ]

    def model(self):

        T = current.T

        define_table = self.define_table
        set_method = self.set_method

        channel_id = self.msg_channel_id
        message_id = self.msg_message_id

        # ---------------------------------------------------------------------
        # Link between Message Channels and Parsers in parser.py
        #
        tablename = "msg_parser"
        table = define_table(tablename,
                             # Source
                             channel_id(ondelete = "CASCADE"),
                             Field("function_name",
                                   label = T("Parser")),
                             Field("enabled", "boolean",
                                   label = T("Enabled?"),
                                   represent = s3_yes_no_represent,
                                   ),
                             *s3_meta_fields())

        self.configure(tablename,
                       onaccept = self.msg_parser_onaccept,
                       )

        set_method("msg", "parser",
                   method="enable",
                   action=self.parser_enable_interactive)

        set_method("msg", "parser",
                   method="disable",
                   action=self.parser_disable_interactive)

        set_method("msg", "parser",
                   method="parse",
                   action=self.parser_parse)

        # ---------------------------------------------------------------------
        # Message parsing status
        # - component to core msg_message table
        #
        tablename = "msg_parsing_status"
        table = define_table(tablename,
                             # Component, not Instance
                             message_id(ondelete = "CASCADE"),
                             # Source
                             channel_id(ondelete = "CASCADE"),
                             Field("is_parsed", "boolean",
                                   default = False,
                                   represent = lambda parsed: \
                                       (parsed and [T("Parsed")] or \
                                                      [T("Not Parsed")])[0],
                                   label = T("Parsing Status")),
                             message_id("reply_id",
                                        label = T("Reply"),
                                        ondelete = "CASCADE",
                                        ),
                             *s3_meta_fields())

        # ---------------------------------------------------------------------
        # Login sessions for Message Parsing
        # - links a from_address with a login until expiry
        #
        tablename = "msg_session"
        table = define_table(tablename,
                             Field("from_address"),
                             Field("email"),
                             Field("created_datetime", "datetime",
                                   default = current.request.utcnow),
                             Field("expiration_time", "integer"),
                             Field("is_expired", "boolean",
                                   default = False),
                             *s3_meta_fields())

        # ---------------------------------------------------------------------
        # Keywords for Message Parsing
        #
        tablename = "msg_keyword"
        table = define_table(tablename,
                             Field("keyword",
                                   label=T("Keyword")),
                             # @ToDo: Move this to a link table
                             self.event_incident_type_id(),
                             *s3_meta_fields())

        # ---------------------------------------------------------------------
        # Senders for Message Parsing
        # - whitelist / blacklist / prioritise
        #
        tablename = "msg_sender"
        table = define_table(tablename,
                             Field("sender",
                                   label=T("Sender")),
                             # @ToDo: Make pe_id work for this
                             #self.super_link("pe_id", "pr_pentity"),
                             Field("priority", "integer",
                                   label=T("Priority")),
                             *s3_meta_fields())

        # ---------------------------------------------------------------------
        return dict(msg_parser_enabled = self.parser_enabled,
                    msg_parser_enable = self.parser_enable,
                    msg_parser_disable = self.parser_disable,
                    )

    # -----------------------------------------------------------------------------
    @staticmethod
    def parser_parse(r, **attr):
        """
            Parse unparsed messages

            S3Method for interactive requests
        """

        record = r.record
        current.s3task.async("msg_parse", args=[record.channel_id, record.function_name])
        current.session.confirmation = \
            current.T("The parse request has been submitted")
        redirect(URL(f="parser"))

    # -------------------------------------------------------------------------
    @staticmethod
    def parser_enabled(channel_id):
        """
            Helper function to see if there is a Parser connected to a Channel
            - used to determine whether to populate the msg_parsing_status table
        """

        table = current.s3db.msg_parser
        record = current.db(table.channel_id == channel_id).select(table.enabled,
                                                                   limitby=(0, 1),
                                                                   ).first()
        if record and record.enabled:
            return True
        else:
            return False

    # -------------------------------------------------------------------------
    @staticmethod
    def parser_enable(id):
        """
            Enable a Parser
            - Connect a Parser to a Channel

            CLI API for shell scripts & to be called by S3Method

            @ToDo: Ensure only 1 Parser is connected to any Channel at a time
        """

        db = current.db
        s3db = current.s3db
        table = s3db.msg_parser
        record = db(table.id == id).select(table.id, # needed for update_record
                                           table.enabled,
                                           table.channel_id,
                                           table.function_name,
                                           limitby=(0, 1),
                                           ).first()
        if not record.enabled:
            # Flag it as enabled
            record.update_record(enabled = True)

        channel_id = record.channel_id
        function_name = record.function_name

        # Do we have an existing Task?
        ttable = db.scheduler_task
        args = '[%s, "%s"]' % (channel_id, function_name)
        query = ((ttable.function_name == "msg_parse") & \
                 (ttable.args == args) & \
                 (ttable.status.belongs(["RUNNING", "QUEUED", "ALLOCATED"])))
        exists = db(query).select(ttable.id,
                                  limitby=(0, 1)).first()
        if exists:
            return "Parser already enabled"
        else:
            current.s3task.schedule_task("msg_parse",
                                         args=[channel_id, function_name],
                                         period=300,  # seconds
                                         timeout=300, # seconds
                                         repeats=0    # unlimited
                                         )
            return "Parser enabled"

    # -------------------------------------------------------------------------
    @staticmethod
    def parser_enable_interactive(r, **attr):
        """
            Enable a Parser
            - Connect a Parser to a Channel

            S3Method for interactive requests
        """

        result = current.s3db.msg_parser_enable(r.id)
        current.session.confirmation = result
        redirect(URL(f="parser"))

    # -------------------------------------------------------------------------
    @staticmethod
    def parser_disable(id):
        """
            Disable a Parser
            - Disconnect a Parser from a Channel

            CLI API for shell scripts & to be called by S3Method
        """
    
        db = current.db
        s3db = current.s3db
        table = s3db.msg_parser
        record = db(table.id == id).select(table.id, # needed for update_record
                                           table.enabled,
                                           table.channel_id,
                                           table.function_name,
                                           limitby=(0, 1),
                                           ).first()
        if record.enabled:
            # Flag it as disabled
            record.update_record(enabled = False)

        # Do we have an existing Task?
        ttable = db.scheduler_task
        args = '[%s, "%s"]' % (record.channel_id, record.function_name)
        query = ((ttable.function_name == "msg_parse") & \
                 (ttable.args == args) & \
                 (ttable.status.belongs(["RUNNING", "QUEUED", "ALLOCATED"])))
        exists = db(query).select(ttable.id,
                                  limitby=(0, 1)).first()
        if exists:
            # Disable all
            db(query).update(status="STOPPED")
            return "Parser disabled"
        else:
            return "Parser already disabled"

    # -------------------------------------------------------------------------
    @staticmethod
    def parser_disable_interactive(r, **attr):
        """
            Disable a Parser
            - Disconnect a Parser from a Channel

            S3Method for interactive requests
        """

        result = current.s3db.msg_parser_disable(r.id)
        current.session.confirmation = result
        redirect(URL(f="parser"))

    # -------------------------------------------------------------------------
    @staticmethod
    def msg_parser_onaccept(form):
        """
            Process the Enabled Flag
        """

        if form.record:
            # Update form
            # process of changed
            if form.record.enabled and not form.vars.enabled:
                current.s3db.msg_parser_disable(form.vars.id)
            elif form.vars.enabled and not form.record.enabled:
                current.s3db.msg_parser_enable(form.vars.id)
        else:
            # Create form
            # Process only if enabled
            if form.vars.enabled:
                current.s3db.msg_parser_enable(form.vars.id)

# =============================================================================
class S3RSSModel(S3ChannelModel):
    """
        RSS channel
    """

    names = ["msg_rss_channel",
             "msg_rss"
             ]

    def model(self):

        T = current.T

        define_table = self.define_table
        set_method = self.set_method

        # ---------------------------------------------------------------------
        # RSS Settings for an account
        #
        tablename = "msg_rss_channel"
        table = define_table(tablename,
                             self.super_link("channel_id", "msg_channel"),
                             Field("name",
                                   length = 255,
                                   unique = True),
                             Field("description"),
                             Field("enabled", "boolean",
                                   label = T("Enabled?"),
                                   represent = s3_yes_no_represent,
                                   ),
                             Field("url"),
                             *s3_meta_fields())

        self.configure(tablename,
                       super_entity = "msg_channel",
                       onaccept = self.msg_channel_onaccept,
                       )

        set_method("msg", "rss_channel",
                   method="enable",
                   action=self.msg_channel_enable_interactive)

        set_method("msg", "rss_channel",
                   method="disable",
                   action=self.msg_channel_disable_interactive)

        set_method("msg", "rss_channel",
                   method="poll",
                   action=self.msg_channel_poll)

        # ---------------------------------------------------------------------
        # RSS Feed Posts
        #
        tablename = "msg_rss"
        table = define_table(tablename,
                             self.super_link("message_id", "msg_message"),
                             Field("title"), # Subject?
                             Field("body", "text",
                                   label = T("Description")),
                             Field("from_address",
                                   label = T("Link")),
                             # Just present for Super Entity
                             Field("inbound", "boolean",
                                   default = True,
                                   readable = False,
                                   writable = False,
                                   ),
                             *s3_meta_fields())

        table.created_on.readable = True
        table.created_on.label = T("Tweeted on")
        table.created_on.represent = lambda dt: \
            S3DateTime.datetime_represent(dt, utc=True)

        self.configure(tablename,
                       super_entity = current.s3db.msg_message,
                       list_fields = ["title",
                                      "from_address",
                                      "created_on",
                                      "body"
                                      ],
                       )

        # ---------------------------------------------------------------------
        return dict()

# =============================================================================
class S3SMSModel(S3Model):
    """
        SMS: Short Message Service

        These can be received through a number of different gateways
        - MCommons
        - Modem (@ToDo: Restore this)
        - Tropo
        - Twilio
    """

    names = ["msg_sms",
             ]

    def model(self):

        #T = current.T

        # ---------------------------------------------------------------------
        # SMS Messages: InBox & Outbox
        #
        tablename = "msg_sms"
        table = self.define_table(tablename,
                                  # Instance
                                  self.super_link("message_id", "msg_message"),
                                  self.msg_channel_id(),
                                  Field("body", "text",
                                        #label = T("Message"),
                                        ),
                                  Field("from_address",
                                        #label = T("Sender"),
                                        ),
                                  Field("to_address",
                                        #label = T("To"),
                                        ),
                                  Field("inbound", "boolean",
                                        default = False,
                                        #represent = lambda direction: \
                                        # (direction and [T("In")] or \
                                        #                [T("Out")])[0],
                                        #label = T("Direction")),
                                        ),
                                  *s3_meta_fields())

        self.configure(tablename,
                       super_entity = "msg_message",
                       )

        # ---------------------------------------------------------------------
        return dict()

# =============================================================================
class S3SMSOutboundModel(S3Model):
    """
        SMS: Short Message Service
        - Outbound Channels

        These can be sent through a number of different gateways
        - Modem
        - SMTP
        - Tropo
        - Web API (inc Clickatell, MCommons, mVaayoo)
    """

    names = ["msg_sms_outbound_gateway",
             "msg_sms_modem_channel",
             "msg_sms_webapi_channel",
             "msg_sms_smtp_channel",
             ]

    def model(self):

        #T = current.T

        configure = self.configure
        define_table = self.define_table

        # ---------------------------------------------------------------------
        # SMS Outbound Gateway
        # - select which gateway is in active use
        #
        tablename = "msg_sms_outbound_gateway"
        table = define_table(tablename,
                             Field("outgoing_sms_handler", length=32,
                                   requires = IS_IN_SET(current.msg.GATEWAY_OPTS,
                                                        zero=None)),
                             # @ToDo: Allow selection of different gateways based on Organisation/Branch
                             #self.org_organisation_id(),
                             # @ToDo: Allow addition of relevant country code (currently in deployment_settings)
                             #Field("default_country_code", "integer",
                             #      default=44),
                             *s3_meta_fields())

        # ---------------------------------------------------------------------
        # SMS Modem Channel
        #
        tablename = "msg_sms_modem_channel"
        table = define_table(tablename,
                             self.super_link("channel_id", "msg_channel"),
                             Field("name"),
                             Field("description"),
                             # Nametag to remember account - To be used later
                             #Field("account_name"),
                             Field("modem_port"),
                             Field("modem_baud", "integer",
                                   default = 115200,
                                   ),
                             Field("enabled", "boolean",
                                   default = True,
                                   ),
                             # To be used later
                             #Field("preference", "integer", default = 5),
                             *s3_meta_fields())

        configure(tablename,
                  super_entity = "msg_channel",
                  )

        # ---------------------------------------------------------------------
        # Settings for Web API services
        #
        # @ToDo: Simplified dropdown of services which prepopulates entries & provides nice prompts for the config options
        #        + Advanced mode for raw access to real fields
        #
        tablename = "msg_sms_webapi_channel"
        table = define_table(tablename,
                             self.super_link("channel_id", "msg_channel"),
                             Field("name"),
                             Field("description"),
                             Field("url",
                                   requires = IS_URL(),
                                   default = "https://api.clickatell.com/http/sendmsg" # Clickatell
                                   #default = "https://secure.mcommons.com/api/send_message" # Mobile Commons
                                   ),
                             Field("parameters",
                                   default="user=yourusername&password=yourpassword&api_id=yourapiid" # Clickatell
                                   #default = "campaign_id=yourid" # Mobile Commons
                                   ),
                             Field("message_variable", "string",
                                   requires = IS_NOT_EMPTY(),
                                   default = "text" # Clickatell
                                   #default = "body" # Mobile Commons
                                   ),
                             Field("to_variable", "string",
                                   requires = IS_NOT_EMPTY(),
                                   default = "to" # Clickatell
                                   #default = "phone_number" # Mobile Commons
                                   ),
                             # If using HTTP Auth (e.g. Mobile Commons)
                             Field("username"),
                             Field("password"),
                             Field("enabled", "boolean",
                                   default = True),
                             # To be used later
                             #Field("preference", "integer", default = 5),
                             *s3_meta_fields())

        configure(tablename,
                  super_entity = "msg_channel",
                  )

        # ---------------------------------------------------------------------
        # SMS via SMTP Channel
        #
        tablename = "msg_sms_smtp_channel"
        table = define_table(tablename,
                             self.super_link("channel_id", "msg_channel"),
                             Field("name"),
                             Field("description"),
                             Field("address", length=64,
                                   requires=IS_NOT_EMPTY()),
                             Field("subject", length=64),
                             Field("enabled", "boolean",
                                   default = True),
                             # To be used later
                             #Field("preference", "integer", default = 5),
                             *s3_meta_fields())

        configure(tablename,
                  super_entity = "msg_channel",
                  )

        # ---------------------------------------------------------------------
        return dict()

# =============================================================================
class S3SubscriptionModel(S3Model):
    """
        Handle Subscription
        - currently this is just for Saved Searches

        @ToDo: Deprecate (replaced by s3notify)
    """

    names = ["msg_subscription"]

    def model(self):

        T = current.T
        auth = current.auth

        # @ToDo: Use msg.CONTACT_OPTS
        msg_subscription_mode_opts = {1:T("Email"),
                                      #2:T("SMS"),
                                      #3:T("Email and SMS")
                                      }
        # @ToDo: Move this to being a component of the Saved Search
        #        (so that each search can have it's own subscription options)
        # @ToDo: Make Conditional
        # @ToDo: CRUD Strings
        tablename = "msg_subscription"
        table = self.define_table(tablename,
                                  Field("user_id", "integer",
                                        default = auth.user_id,
                                        requires = IS_NOT_IN_DB(current.db,
                                                                "msg_subscription.user_id"),
                                        readable = False,
                                        writable = False
                                        ),
                                  Field("subscribe_mode", "integer",
                                        default = 1,
                                        represent = lambda opt: \
                                            msg_subscription_mode_opts.get(opt, None),
                                        readable = False,
                                        requires = IS_IN_SET(msg_subscription_mode_opts,
                                                             zero=None)
                                        ),
                                  Field("subscription_frequency",
                                        requires = IS_IN_SET(["daily",
                                                              "weekly",
                                                              "monthly"]),
                                        default = "daily",
                                        ),
                                  self.pr_person_id(label = T("Person"),
                                                    default = auth.s3_logged_in_person()),
                                  *s3_meta_fields())

        self.configure("msg_subscription",
                       list_fields=["subscribe_mode",
                                    "subscription_frequency"])

        # ---------------------------------------------------------------------
        return dict()

# =============================================================================
class S3TropoModel(S3Model):
    """
        Tropo can be used to send & receive SMS, Twitter & XMPP

        https://www.tropo.com
    """

    names = ["msg_tropo_channel",
             "msg_tropo_scratch",
             ]

    def model(self):

        #T = current.T

        define_table = self.define_table
        set_method = self.set_method

        # ---------------------------------------------------------------------
        # Tropo Channels
        #
        tablename = "msg_tropo_channel"
        table = define_table(tablename,
                             self.super_link("channel_id", "msg_channel"),
                             Field("name"),
                             Field("description"),
                             Field("enabled", "boolean",
                                   #label = T("Enabled?"),
                                   represent = s3_yes_no_represent,
                                   ),
                             Field("token_messaging"),
                             #Field("token_voice"),
                             *s3_meta_fields())

        self.configure(tablename,
                       super_entity = "msg_channel",
                       )

        set_method("msg", "tropo_channel",
                   method="enable",
                   action=self.msg_channel_enable_interactive)

        set_method("msg", "tropo_channel",
                   method="disable",
                   action=self.msg_channel_disable_interactive)

        set_method("msg", "tropo_channel",
                   method="poll",
                   action=self.msg_channel_poll)

        # ---------------------------------------------------------------------
        # Tropo Scratch pad for outbound messaging
        #
        tablename = "msg_tropo_scratch"
        table = define_table(tablename,
                             Field("row_id", "integer"),
                             Field("message_id", "integer"),
                             Field("recipient"),
                             Field("message"),
                             Field("network")
                             )

        # ---------------------------------------------------------------------
        return dict()

# =============================================================================
class S3TwilioModel(S3ChannelModel):
    """
        Twilio Inbound SMS channel
    """

    names = ["msg_twilio_channel",
             "msg_twilio_sid",
             ]

    def model(self):

        #T = current.T

        define_table = self.define_table
        set_method = self.set_method

        # ---------------------------------------------------------------------
        # Twilio Channels
        #
        tablename = "msg_twilio_channel"
        table = define_table(tablename,
                             # Instance
                             self.super_link("channel_id", "msg_channel"),
                             Field("name"),
                             Field("description"),
                             Field("enabled", "boolean",
                                   #label = T("Enabled?"),
                                   represent = s3_yes_no_represent,
                                   ),
                             Field("account_name", length=255, unique=True),
                             Field("url",
                                   default = \
                                   "https://api.twilio.com/2010-04-01/Accounts"
                                   ),
                             Field("account_sid", length=64,
                                   requires = IS_NOT_EMPTY()),
                             Field("auth_token", "password", length=64,
                                   readable = False,
                                   requires = IS_NOT_EMPTY()),
                             *s3_meta_fields())

        self.configure(tablename,
                       super_entity = "msg_channel",
                       onaccept = self.msg_channel_onaccept,
                       )

        set_method("msg", "twilio_channel",
                   method="enable",
                   action=self.msg_channel_enable_interactive)

        set_method("msg", "twilio_channel",
                   method="disable",
                   action=self.msg_channel_disable_interactive)

        set_method("msg", "twilio_channel",
                   method="poll",
                   action=self.msg_channel_poll)

        # ---------------------------------------------------------------------
        # Twilio Message extensions
        # - store message sid to know which ones we've already downloaded
        #
        tablename = "msg_twilio_sid"
        table = define_table(tablename,
                             # Component not Instance
                             self.msg_message_id(ondelete = "CASCADE"),
                             Field("sid"),
                             *s3_meta_fields())

        # ---------------------------------------------------------------------
        return dict()

# =============================================================================
class S3TwitterModel(S3Model):

    names = ["msg_twitter_channel",
             "msg_twitter",
             ]

    def model(self):

        T = current.T
        db = current.db

        configure = self.configure
        define_table = self.define_table
        set_method = self.set_method

        # ---------------------------------------------------------------------
        # Twitter Channel
        #
        tablename = "msg_twitter_channel"
        table = define_table(tablename,
                             #Instance
                             self.super_link("channel_id", "msg_channel"),
                             Field("name"),
                             Field("description"),
                             Field("enabled", "boolean",
                                   label = T("Enabled?"),
                                   represent = s3_yes_no_represent,
                                   ),
                             Field("twitter_account"),
                             Field("consumer_key", "password"),
                             Field("consumer_secret", "password"),
                             Field("access_token", "password"),
                             Field("access_token_secret", "password"),
                             *s3_meta_fields())

        configure(tablename,
                  super_entity = "msg_channel",
                  onaccept = self.msg_channel_onaccept,
                  #onvalidation = self.twitter_channel_onvalidation
                  )

        set_method("msg", "twitter_channel",
                   method="enable",
                   action=self.msg_channel_enable_interactive)

        set_method("msg", "twitter_channel",
                   method="disable",
                   action=self.msg_channel_disable_interactive)

        set_method("msg", "twitter_channel",
                   method="poll",
                   action=self.msg_channel_poll)

        # ---------------------------------------------------------------------
        # Twitter Messages: InBox & Outbox
        #
        tablename = "msg_twitter"
        table = define_table(tablename,
                             # Instance
                             self.super_link("message_id", "msg_message"),
                             Field("body", length=140,
                                   label = T("Message"),
                                   ),
                             Field("from_address", #notnull=True,
                                   label = T("From"),
                                   requires = IS_NOT_EMPTY(),
                                   represent = self.twitter_represent,
                                   ),
                             Field("to_address",
                                   label = T("To"),
                                   represent = self.twitter_represent,
                                   ),
                             Field("inbound", "boolean",
                                   default = False,
                                   represent = lambda direction: \
                                       (direction and [T("In")] or \
                                                      [T("Out")])[0],
                                   label = T("Direction"),
                                   ),
                             *s3_meta_fields())

        table.created_on.readable = True
        table.created_on.label = T("Posted on")
        table.created_on.represent = lambda dt: \
            S3DateTime.datetime_represent(dt, utc=True)

        configure(tablename,
                  super_entity = "msg_message",
                  #orderby=~table.priority,
                  list_fields=["id",
                               #"priority",
                               #"category",
                               #"location_id",
                               "body",
                               "from_address",
                               "created_on",
                               ],
                  )

        # ---------------------------------------------------------------------
        return dict()

    # -------------------------------------------------------------------------
    @staticmethod
    def twitter_represent(nickname, show_link=True):
        """
            Represent a Twitter account
        """

        if not nickname:
            return current.messages["NONE"]

        db = current.db
        s3db = current.s3db
        table = s3db.pr_contact
        query = (table.contact_method == "TWITTER") & \
                (table.value == nickname)
        row = db(query).select(table.pe_id,
                               limitby=(0, 1)).first()
        if row:
            repr = s3db.pr_pentity_represent(row.pe_id)
            if show_link:
                # Assume person
                ptable = s3db.pr_person
                row = db(ptable.pe_id == row.pe_id).select(ptable.id,
                                                           limitby=(0, 1))
                if row:
                    link = URL(c="pr", f="person", args=[row.id])
                    return A(repr, _href=link)
            return repr
        else:
            return nickname

    # -------------------------------------------------------------------------
    @staticmethod
    def twitter_channel_onvalidation(form):
        """
            Complete oauth: take tokens from session + pin from form,
            and do the 2nd API call to Twitter
        """

        T = current.T
        session = current.session
        settings = current.deployment_settings.msg
        s3 = session.s3
        vars = form.vars

        if vars.pin and s3.twitter_request_key and s3.twitter_request_secret:
            try:
                import tweepy
            except:
                raise HTTP(501, body=T("Can't import tweepy"))

            oauth = tweepy.OAuthHandler(settings.twitter_oauth_consumer_key,
                                        settings.twitter_oauth_consumer_secret)
            oauth.set_request_token(s3.twitter_request_key,
                                    s3.twitter_request_secret)
            try:
                oauth.get_access_token(vars.pin)
                vars.oauth_key = oauth.access_token.key
                vars.oauth_secret = oauth.access_token.secret
                twitter = tweepy.API(oauth)
                vars.twitter_account = twitter.me().screen_name
                vars.pin = "" # we won't need it anymore
                return
            except tweepy.TweepError:
                session.error = T("Settings were reset because authenticating with Twitter failed")
        # Either user asked to reset, or error - clear everything
        for k in ["oauth_key", "oauth_secret", "twitter_account"]:
            vars[k] = None
        for k in ["twitter_request_key", "twitter_request_secret"]:
            s3[k] = ""

# =============================================================================
class S3TwitterSearchModel(S3ChannelModel):
    """
        Twitter Searches
         - results can be fed to KeyGraph
    """

    names = ["msg_twitter_search",
             "msg_twitter_result",
             ]

    def model(self):

        T = current.T

        configure = self.configure
        define_table = self.define_table
        set_method = self.set_method

        # ---------------------------------------------------------------------
        # Twitter Search Query
        #
        tablename = "msg_twitter_search"
        table = define_table(tablename,
                             Field("keywords", "text",
                                   label = T("Keywords"),
                                   ),
                             Field("lang",
                                   # Set in controller
                                   #default = current.response.s3.language,
                                   label = T("Language"),
                                   ),
                             Field("count", "integer",
                                   default = 100,
                                   label = T("# Results per query"),
                                   ),
                             Field("include_entities", "boolean",
                                   default = False,
                                   label = T("Include Entity Information?"),
                                   represent = s3_yes_no_represent,
                                   comment = DIV(_class="tooltip",
                                                 _title="%s|%s" % (T("Entity Information"),
                                                                   T("This is required if analyzing with KeyGraph."))),
                                   ),
                             # @ToDo: Rename or even move to Component Table
                             Field("is_processed", "boolean",
                                   default = False,
                                   label = T("Processed with KeyGraph?"),
                                   represent = s3_yes_no_represent,
                                   ),
                             Field("is_searched", "boolean",
                                   default = False,
                                   label = T("Searched?"),
                                   represent = s3_yes_no_represent,
                                   ),
                             *s3_meta_fields())

        configure(tablename,
                  list_fields = ["keywords",
                                 "lang",
                                 "count",
                                 #"include_entities",
                                 ],
                  )

        # Reusable Query ID
        represent = S3Represent(lookup=tablename, fields=["keywords"])
        search_id = S3ReusableField("search_id", table,
                    label = T("Search Query"),
                    requires = IS_NULL_OR(
                                IS_ONE_OF_EMPTY(db, "msg_twitter_search.id")
                                ),
                    represent = represent,
                    ondelete = "CASCADE")

        set_method("msg", "twitter_search",
                   method="poll",
                   action=self.twitter_search_poll)

        set_method("msg", "twitter_search",
                   method="keygraph",
                   action=self.twitter_keygraph)

        # ---------------------------------------------------------------------
        # Twitter Search Results
        #
        # @ToDo: Store the places mentioned in the Tweet as linked Locations
        #
        tablename = "msg_twitter_result"
        table = define_table(tablename,
                             self.super_link("message_id", "msg_message"),
                             search_id(),
                             Field("tweet_id",
                                   label = T("Tweet ID")),
                             Field("lang",
                                   label = T("Language")),
                             Field("from_address",
                                   label = T("Tweeted by")),
                             Field("body",
                                   label = T("Tweet")),
                             # @ToDo: Populate from Parser
                             #Field("category",
                             #      writable = False,
                             #      label = T("Category"),
                             #      ),
                             #Field("priority", "integer",
                             #      writable = False,
                             #      label = T("Priority"),
                             #      ),
                             # @ToDo: Replace lat/lon with a mappable gis_location_id
                             #self.gis_location_id(),
                             Field("lat", "double",
                                   label = T("Latitude"),
                                   requires = IS_NULL_OR(IS_LAT())),
                             Field("lon", "double",
                                   label = T("Longitude"),
                                   requires = IS_NULL_OR(IS_LON()),
                                   ),
                             # Just present for Super Entity
                             Field("inbound", "boolean",
                                   default = True,
                                   readable = False,
                                   writable = False,
                                   ),
                             *s3_meta_fields())

        table.created_on.readable = True
        table.created_on.label = T("Tweeted on")
        table.created_on.represent = lambda dt: \
            S3DateTime.datetime_represent(dt, utc=True)

        configure(tablename,
                  super_entity = "msg_message",
                  #orderby=~table.priority,
                  list_fields = ["from_address",
                                 #"lang",
                                 "created_on",
                                 "body",
                                 #"category",
                                 #"priority",
                                 #"location_id",
                                 #"lat",
                                 #"lon",
                                 ],
                  )

        # ---------------------------------------------------------------------
        return dict()

    # -----------------------------------------------------------------------------
    @staticmethod
    def twitter_search_poll(r, **attr):
        """
            Perform a Search of Twitter

            S3Method for interactive requests
        """

        tablename = r.tablename
        current.s3task.async("msg_twitter_search", args=[r.id])
        current.session.confirmation = \
            current.T("The search request has been submitted, so new messages should appear shortly - refresh to see them")
        # @ToDo: Filter to this Search
        redirect(URL(f="twitter_result"))

    # -----------------------------------------------------------------------------
    @staticmethod
    def twitter_keygraph(r, **attr):
        """
            Prcoess Search Results with KeyGraph

            S3Method for interactive requests
        """

        tablename = r.tablename
        current.s3task.async("msg_process_keygraph", args=[r.id])
        current.session.confirmation = \
            current.T("The search results are now being processed with KeyGraph")
        # @ToDo: Link to results
        redirect(URL(f="twitter_result"))

# =============================================================================
class S3XFormsModel(S3Model):
    """
        XForms are used by the ODK Collect mobile client

        http://eden.sahanafoundation.org/wiki/BluePrint/Mobile#Android
    """

    names = ["msg_xforms_store"]

    def model(self):

        #T = current.T

        # ---------------------------------------------------------------------
        # SMS store for persistence and scratch pad for combining incoming xform chunks
        tablename = "msg_xforms_store"
        table = self.define_table(tablename,
                                  Field("sender", length=20),
                                  Field("fileno", "integer"),
                                  Field("totalno", "integer"),
                                  Field("partno", "integer"),
                                  Field("message", length=160)
                                  )

        # ---------------------------------------------------------------------
        return dict()

# =============================================================================
class S3BaseStationModel(S3Model):
    """
        Base Stations (Cell Towers) are a type of Site

        @ToDo: Calculate Coverage from Antenna Height, Radio Power and Terrain
               - see RadioMobile
    """

    names = ["msg_basestation"]

    def model(self):

        T = current.T

        define_table = self.define_table

        # ---------------------------------------------------------------------
        # Base Stations (Cell Towers)
        #
        tablename = "msg_basestation"
        table = define_table(tablename,
                             self.super_link("site_id", "org_site"),
                             Field("name", notnull=True,
                                   length=64, # Mayon Compatibility
                                   label=T("Name")),
                             Field("code", length=10, # Mayon compatibility
                                   label=T("Code"),
                                   # Deployments that don't wants site codes can hide them
                                   #readable=False,
                                   #writable=False,
                                   # @ToDo: Deployment Setting to add validator to make these unique
                                   ),
                             self.org_organisation_id(
                                 label = T("Operator"),
                                 #widget=S3OrganisationAutocompleteWidget(default_from_profile=True),
                                 requires = self.org_organisation_requires(required=True,
                                                                           updateable=True),
                                 ),
                             self.gis_location_id(),
                             s3_comments(),
                             *s3_meta_fields())

        # CRUD strings
        ADD_BASE = T("Add New Base Station")
        current.response.s3.crud_strings[tablename] = Storage(
            title_create=T("Add Base Station"),
            title_display=T("Base Station Details"),
            title_list=T("Base Stations"),
            title_update=T("Edit Base Station"),
            title_search=T("Search Base Stations"),
            title_upload=T("Import Base Stations"),
            title_map=T("Map of Base Stations"),
            subtitle_create=ADD_BASE,
            label_list_button=T("List Base Stations"),
            label_create_button=ADD_BASE,
            label_delete_button=T("Delete Base Station"),
            msg_record_created=T("Base Station added"),
            msg_record_modified=T("Base Station updated"),
            msg_record_deleted=T("Base Station deleted"),
            msg_list_empty=T("No Base Stations currently registered"))

        self.configure(tablename,
                       super_entity = "org_site",
                       deduplicate = self.msg_basestation_duplicate,
                       )

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return dict()

    # ---------------------------------------------------------------------
    @staticmethod
    def msg_basestation_duplicate(item):
        """
            Import item deduplication, match by name
                (Adding location_id doesn't seem to be a good idea)

            @param item: the S3ImportItem instance
        """

        if item.tablename == "msg_basestation":
            table = item.table
            name = "name" in item.data and item.data.name
            query = (table.name.lower() == name.lower())
            #location_id = None
            # if "location_id" in item.data:
                # location_id = item.data.location_id
                ## This doesn't find deleted records:
                # query = query & (table.location_id == location_id)
            duplicate = current.db(query).select(table.id,
                                                 limitby=(0, 1)).first()
            # if duplicate is None and location_id:
                ## Search for deleted basestations with this name
                # query = (table.name.lower() == name.lower()) & \
                        # (table.deleted == True)
                # row = db(query).select(table.id, table.deleted_fk,
                                       # limitby=(0, 1)).first()
                # if row:
                    # fkeys = json.loads(row.deleted_fk)
                    # if "location_id" in fkeys and \
                       # str(fkeys["location_id"]) == str(location_id):
                        # duplicate = row
            if duplicate:
                item.id = duplicate.id
                item.method = item.METHOD.UPDATE

# =============================================================================
def msg_search_subscription_notifications(frequency):
    """
        Send Notifications for all Subscriptions
        - run by Scheduler (models/tasks.py)

        @ToDo: Deprecate - replaced by Notifications
    """

    s3db = current.s3db
    table = s3db.pr_saved_search

    if frequency not in dict(table.notification_frequency.requires.options()):
        return

    db = current.db
    searches = db(table.notification_frequency == frequency).select()
    if not searches:
        return

    import urlparse
    from urllib import urlencode
    from uuid import uuid4

    try:
        import json # try stdlib (Python 2.6)
    except ImportError:
        try:
            import simplejson as json # try external module
        except:
            import gluon.contrib.simplejson as json # fallback to pure-Python module
    loads = json.loads

    from gluon.tools import fetch

    msg = current.msg
    settings = current.deployment_settings
    public_url = settings.get_base_public_url()
    system_name_short = settings.get_system_name_short()

    def send(search, message):
        if not message:
            return
        # Send the email
        msg.send_by_pe_id(search.pe_id,
                          subject="%s Search Notification %s" % \
                            (system_name_short, search.name),
                          message=message)

    for search in searches:
        # Fetch the latest records from the search

        # search.url has no host
        search_url = "%s%s" % (public_url, search.url)

        # Create a temporary token for this search
        # that will be used when impersonating users
        auth_token = uuid4()
        search.update_record(auth_token=auth_token)
        # Commit so that when we request via http, then we'll see the change
        db.commit()

        # Parsed URL, break up the URL into its components
        purl = list(urlparse.urlparse(search_url))

        if search.notification_batch:
            # Send all records in a single notification

            # query string parameters to be added to the search URL
            page_qs_parms = {
                "search_subscription": auth_token,
                "%s.modified_on__ge" % (search.resource_name): search.last_checked,
                "format": "email",
            }

            # Turn the parameter list into a URL query string
            page_qs = urlencode(page_qs_parms)

            # Put the URL back together
            page_url = urlparse.urlunparse(
                [
                    purl[0], # scheme
                    purl[1], # netloc
                    purl[2], # path
                    purl[3], # params
                    "&".join([purl[4], page_qs]), # query
                    purl[5], # fragment
                ]
            )
            message = fetch(page_url)

            # Send the email
            send(search, message)

        else:
            # Not batch

            # query string parameters to be added to the search URL
            page_qs_parms = {
                "search_subscription": auth_token,
                "%s.modified_on__ge" % (search.resource_name): search.last_checked,
                "format": "json",
            }

            # Turn the parameter list into a URL query string
            page_qs = urlencode(page_qs_parms)

            # Put the URL back together
            page_url = urlparse.urlunparse(
                [
                    purl[0], # scheme
                    purl[1], # netloc
                    purl[2], # path
                    purl[3], # params
                    "&".join([purl[4], page_qs]), # query
                    purl[5], # fragment
                ]
            )
            # Fetch the record list as json
            json_string = fetch(page_url)

            if json_string:
                records = loads(json_string)

                for record in records:
                    email_qs = urlencode(
                        {
                            "search_subscription": auth_token,
                            "format": "email",
                            "%s.id__eq" % search.resource_name: record["id"],
                        }
                    )
                    email_url = urlparse.urlunparse(
                        [
                            purl[0], # scheme
                            purl[1], # netloc
                            purl[2], # path
                            purl[3], # params
                            email_qs, # query
                            purl[5], # fragment
                        ]
                    )

                    message = fetch(email_url)

                    # Send the email
                    send(search, message)

    # Update the saved searches to indicate they've just been checked
    # & revoke the temporary token
    query = (table.notification_frequency == frequency) & \
            (table.deleted != True)
    db(query).update(last_checked=datetime.datetime.utcnow(),
                     auth_token=None,
                     )
    # Explictly commit
    db.commit()

# END =========================================================================
