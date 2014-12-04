# -*- coding: utf-8 -*-

""" Sahana Eden Messaging Model

    @copyright: 2009-2014 (c) Sahana Software Foundation
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

__all__ = ("S3ChannelModel",
           "S3MessageModel",
           "S3MessageAttachmentModel",
           "S3EmailModel",
           "S3FacebookModel",
           "S3MCommonsModel",
           "S3ParsingModel",
           "S3RSSModel",
           "S3SMSModel",
           "S3SMSOutboundModel",
           "S3TropoModel",
           "S3TwilioModel",
           "S3TwitterModel",
           "S3TwitterSearchModel",
           "S3XFormsModel",
           "S3BaseStationModel",
           )

from gluon import *
from gluon.storage import Storage
from ..s3 import *

# Compact JSON encoding
SEPARATORS = (",", ":")

# =============================================================================
class S3ChannelModel(S3Model):
    """
        Messaging Channels
        - all Inbound & Outbound channels for messages are instances of this
          super-entity
    """

    names = ("msg_channel",
             "msg_channel_limit",
             "msg_channel_status",
             "msg_channel_id",
             "msg_channel_enable",
             "msg_channel_disable",
             "msg_channel_enable_interactive",
             "msg_channel_disable_interactive",
             "msg_channel_onaccept",
             )

    def model(self):

        T = current.T
        db = current.db

        define_table = self.define_table

        #----------------------------------------------------------------------
        # Super entity: msg_channel
        #
        channel_types = Storage(msg_email_channel = T("Email (Inbound)"),
                                msg_facebook_channel = T("Facebook"),
                                msg_mcommons_channel = T("Mobile Commons (Inbound)"),
                                msg_rss_channel = T("RSS Feed"),
                                msg_sms_modem_channel = T("SMS Modem"),
                                msg_sms_webapi_channel = T("SMS WebAPI (Outbound)"),
                                msg_sms_smtp_channel = T("SMS via SMTP (Outbound)"),
                                msg_tropo_channel = T("Tropo"),
                                msg_twilio_channel = T("Twilio (Inbound)"),
                                msg_twitter_channel = T("Twitter"),
                                )

        tablename = "msg_channel"
        self.super_entity(tablename, "channel_id",
                          channel_types,
                          Field("name",
                                #label = T("Name"),
                                ),
                          Field("description",
                                #label = T("Description"),
                                ),
                          Field("enabled", "boolean",
                                default = True,
                                #label = T("Enabled?")
                                #represent = s3_yes_no_represent,
                                ),
                          # @ToDo: Indicate whether channel can be used for Inbound or Outbound
                          #Field("inbound", "boolean",
                          #      label = T("Inbound?")),
                          #Field("outbound", "boolean",
                          #      label = T("Outbound?")),
                          )

        # @todo: make lazy_table
        table = db[tablename]
        table.instance_type.readable = True

        # Reusable Field
        channel_id = S3ReusableField("channel_id", "reference %s" % tablename,
                                     label = T("Channel"),
                                     ondelete = "SET NULL",
                                     represent = S3Represent(lookup=tablename),
                                     requires = IS_EMPTY_OR(
                                        IS_ONE_OF_EMPTY(db, "msg_channel.id")),
                                     )

        self.add_components(tablename,
                            msg_channel_status = "channel_id",
                            )

        # ---------------------------------------------------------------------
        # Channel Limit
        #  Used to limit the number of emails sent from the system
        #  - works by simply recording an entry for the timestamp to be checked against
        #
        # - currently just used by msg.send_email()
        #
        tablename = "msg_channel_limit"
        define_table(tablename,
                     # @ToDo: Make it per-channel
                     #channel_id(),
                     *s3_timestamp())

        # ---------------------------------------------------------------------
        # Channel Status
        #  Used to record errors encountered in the Channel
        #
        tablename = "msg_channel_status"
        define_table(tablename,
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

    # -------------------------------------------------------------------------
    @staticmethod
    def channel_enable(tablename, channel_id):
        """
            Enable a Channel
            - Schedule a Poll for new messages
            - Enable all associated Parsers

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

        # Enable all Parser tasks on this channel
        ptable = s3db.msg_parser
        query = (ptable.channel_id == channel_id) & \
                (ptable.deleted == False)
        parsers = db(query).select(ptable.id)
        for parser in parsers:
            s3db.msg_parser_enable(parser.id)

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
                                         args = [tablename, channel_id],
                                         period = 300,  # seconds
                                         timeout = 300, # seconds
                                         repeats = 0    # unlimited
                                         )
            return "Channel enabled"

    # -------------------------------------------------------------------------
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

    # -------------------------------------------------------------------------
    @staticmethod
    def channel_disable(tablename, channel_id):
        """
            Disable a Channel
            - Remove schedule for Polling for new messages
            - Disable all associated Parsers

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

        # Disable all Parser tasks on this channel
        ptable = s3db.msg_parser
        parsers = db(ptable.channel_id == channel_id).select(ptable.id)
        for parser in parsers:
            s3db.msg_parser_disable(parser.id)

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

    # --------------------------------------------------------------------------
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

    # -------------------------------------------------------------------------
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

    names = ("msg_message",
             "msg_message_id",
             "msg_message_represent",
             "msg_outbox",
             )

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
                                msg_facebook = T("Facebook"),
                                msg_rss = T("RSS"),
                                msg_sms = T("SMS"),
                                msg_twitter = T("Twitter"),
                                msg_twitter_result = T("Twitter Search Results"),
                                )

        tablename = "msg_message"
        self.super_entity(tablename, "message_id",
                          message_types,
                          # Knowing which Channel Incoming Messages
                          # came in on allows correlation to Outbound
                          # messages (campaign_message, deployment_alert, etc)
                          self.msg_channel_id(),
                          s3_datetime(default="now"),
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
                                label = T("Direction"),
                                represent = lambda direction: \
                                            (direction and [T("In")] or \
                                                           [T("Out")])[0],
                                ),
                          )

        # @todo: make lazy_table
        table = db[tablename]
        table.instance_type.readable = True
        table.instance_type.writable = True

        configure(tablename,
                  list_fields = ["instance_type",
                                 "from_address",
                                 "to_address",
                                 "body",
                                 "inbound",
                                 ],
                  )

        # Reusable Field
        message_represent = S3Represent(lookup=tablename, fields=["body"])
        message_id = S3ReusableField("message_id", "reference %s" % tablename,
                                     ondelete = "RESTRICT",
                                     represent = message_represent,
                                     requires = IS_EMPTY_OR(
                                        IS_ONE_OF_EMPTY(db, "msg_message.id")),
                                     )

        self.add_components(tablename,
                            msg_attachment = "message_id",
                            deploy_response = "message_id",
                            )

        # ---------------------------------------------------------------------
        # Outbound Messages
        #

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
        define_table(tablename,
                     # FK not instance
                     message_id(),
                     # Person/Group to send the message out to:
                     self.super_link("pe_id", "pr_pentity"),
                     # If set used instead of picking up from pe_id:
                     Field("address"),
                     Field("contact_method", length=32,
                           default = "EMAIL",
                           label = T("Contact Method"),
                           represent = lambda opt: \
                                       MSG_CONTACT_OPTS.get(opt, UNKNOWN_OPT),
                           requires = IS_IN_SET(MSG_CONTACT_OPTS,
                                                zero=None),
                           ),
                     opt_msg_status(),
                     # Used to loop through a PE to get it's members
                     Field("system_generated", "boolean",
                           default = False,
                           ),
                     # Give up if we can't send after MAX_RETRIES
                     Field("retries", "integer",
                           default = MAX_SEND_RETRIES,
                           readable = False,
                           writable = False,
                           ),
                     *s3_meta_fields())

        configure(tablename,
                  list_fields = ["id",
                                 "message_id",
                                 "pe_id",
                                 "status",
                                 ],
                  orderby = "msg_outbox.created_on desc",
                  )

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        return dict(msg_message_id = message_id,
                    msg_message_represent = message_represent,
                    )

    # -------------------------------------------------------------------------
    @staticmethod
    def defaults():
        """
            Return safe defaults in case the model has been deactivated.
        """

        dummy = S3ReusableField("dummy_id", "integer",
                                readable = False,
                                writable = False)

        return dict(msg_message_id = lambda **attr: dummy("message_id"),
                    )

# =============================================================================
class S3MessageAttachmentModel(S3Model):
    """
        Message Attachments
        - link table between msg_message & doc_document
    """

    names = ("msg_attachment",)

    def model(self):

        # ---------------------------------------------------------------------
        #
        tablename = "msg_attachment"
        self.define_table(tablename,
                          # FK not instance
                          self.msg_message_id(ondelete="CASCADE"),
                          self.doc_document_id(),
                          *s3_meta_fields())

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        return dict()

# =============================================================================
class S3EmailModel(S3ChannelModel):
    """
        Email
            InBound Channels
                Outbound Email is currently handled via deployment_settings
            InBox/OutBox
    """

    names = ("msg_email_channel",
             "msg_email",
             )

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
        define_table(tablename,
                     # Instance
                     super_link("channel_id", "msg_channel"),
                     Field("name"),
                     Field("description"),
                     Field("enabled", "boolean",
                           default = True,
                           label = T("Enabled?"),
                           represent = s3_yes_no_represent,
                           ),
                     Field("server"),
                     Field("protocol",
                           requires = IS_IN_SET(["imap", "pop3"],
                                                zero=None),
                           ),
                     Field("use_ssl", "boolean"),
                     Field("port", "integer"),
                     Field("username"),
                     Field("password", "password", length=64,
                           readable = False,
                           requires = IS_NOT_EMPTY(),
                           ),
                     # Set true to delete messages from the remote
                     # inbox after fetching them.
                     Field("delete_from_server", "boolean"),
                     *s3_meta_fields())

        configure(tablename,
                  onaccept = self.msg_channel_onaccept,
                  super_entity = "msg_channel",
                  )

        set_method("msg", "email_channel",
                   method = "enable",
                   action = self.msg_channel_enable_interactive)

        set_method("msg", "email_channel",
                   method = "disable",
                   action = self.msg_channel_disable_interactive)

        set_method("msg", "email_channel",
                   method = "poll",
                   action = self.msg_channel_poll)

        # ---------------------------------------------------------------------
        # Email Messages: InBox & Outbox
        #
        sender = current.deployment_settings.get_mail_sender()

        tablename = "msg_email"
        define_table(tablename,
                     # Instance
                     super_link("message_id", "msg_message"),
                     self.msg_channel_id(),
                     s3_datetime(default = "now"),
                     Field("subject", length=78,    # RFC 2822
                           label = T("Subject"),
                           ),
                     Field("body", "text",
                           label = T("Message"),
                           ),
                     Field("from_address", #notnull=True,
                           default = sender,
                           label = T("Sender"),
                           requires = IS_EMAIL(),
                           ),
                     Field("to_address",
                           label = T("To"),
                           requires = IS_EMAIL(),
                           ),
                     Field("raw", "text",
                           label = T("Message Source"),
                           readable = False,
                           writable = False,
                           ),
                     Field("inbound", "boolean",
                           default = False,
                           label = T("Direction"),
                           represent = lambda direction: \
                                       (direction and [T("In")] or [T("Out")])[0],
                           ),
                     *s3_meta_fields())

        configure(tablename,
                  orderby = "msg_email.date desc",
                  super_entity = "msg_message",
                  )

        # Components
        self.add_components(tablename,
                            # Used to link to custom tab deploy_response_select_mission:
                            deploy_mission = {"name": "select",
                                              "link": "deploy_response",
                                              "joinby": "message_id",
                                              "key": "mission_id",
                                              "autodelete": False,
                                              },
                            )

        # ---------------------------------------------------------------------
        return dict()
        
# =============================================================================
class S3FacebookModel(S3ChannelModel):
    """
        Facebook
            Channels
            InBox/OutBox

        https://developers.facebook.com/docs/graph-api
    """

    names = ("msg_facebook_channel",
             "msg_facebook",
             "msg_facebook_login",
             )

    def model(self):

        T = current.T

        configure = self.configure
        define_table = self.define_table
        set_method = self.set_method
        super_link = self.super_link

        # ---------------------------------------------------------------------
        # Facebook Channels
        #
        tablename = "msg_facebook_channel"
        define_table(tablename,
                     # Instance
                     super_link("channel_id", "msg_channel"),
                     Field("name"),
                     Field("description"),
                     Field("enabled", "boolean",
                           default = True,
                           label = T("Enabled?"),
                           represent = s3_yes_no_represent,
                           ),
                     Field("login", "boolean",
                           default = False,
                           label = T("Use for Login?"),
                           represent = s3_yes_no_represent,
                           ),
                     Field("app_id", "bigint",
                           requires = IS_INT_IN_RANGE(0, +1e16)
                           ),
                     Field("app_secret", "password", length=64,
                           readable = False,
                           requires = IS_NOT_EMPTY(),
                           ),
                     # Optional
                     Field("page_id", "bigint",
                           requires = IS_INT_IN_RANGE(0, +1e16)
                           ),
                     Field("page_access_token"),
                     *s3_meta_fields())

        configure(tablename,
                  onaccept = self.msg_facebook_channel_onaccept,
                  super_entity = "msg_channel",
                  )

        set_method("msg", "facebook_channel",
                   method = "enable",
                   action = self.msg_channel_enable_interactive)

        set_method("msg", "facebook_channel",
                   method = "disable",
                   action = self.msg_channel_disable_interactive)

        #set_method("msg", "facebook_channel",
        #           method = "poll",
        #           action = self.msg_channel_poll)

        # ---------------------------------------------------------------------
        # Facebook Messages: InBox & Outbox
        #

        tablename = "msg_facebook"
        define_table(tablename,
                     # Instance
                     super_link("message_id", "msg_message"),
                     self.msg_channel_id(),
                     s3_datetime(default = "now"),
                     Field("body", "text",
                           label = T("Message"),
                           ),
                     # @ToDo: Are from_address / to_address relevant in Facebook?
                     Field("from_address", #notnull=True,
                           #default = sender,
                           label = T("Sender"),
                           ),
                     Field("to_address",
                           label = T("To"),
                           ),
                     Field("inbound", "boolean",
                           default = False,
                           label = T("Direction"),
                           represent = lambda direction: \
                                       (direction and [T("In")] or [T("Out")])[0],
                           ),
                     *s3_meta_fields())

        configure(tablename,
                  orderby = "msg_facebook.date desc",
                  super_entity = "msg_message",
                  )

        # ---------------------------------------------------------------------
        return dict(msg_facebook_login = self.msg_facebook_login,
                    )

    # -------------------------------------------------------------------------
    @staticmethod
    def defaults():
        """ Safe defaults for model-global names if module is disabled """

        return dict(msg_facebook_login = lambda: False,
                    )

    # -------------------------------------------------------------------------
    @staticmethod
    def msg_facebook_channel_onaccept(form):

        if form.vars.login:
            # Ensure only a single account used for Login
            current.db(current.s3db.msg_facebook_channel.id != form.vars.id).update(login = False)

        # Normal onaccept processing
        S3ChannelModel.channel_onaccept(form)

    # -------------------------------------------------------------------------
    @staticmethod
    def msg_facebook_login():

        table = current.s3db.msg_facebook_channel
        query = (table.login == True) & \
                (table.deleted == False)
        c = current.db(query).select(table.app_id,
                                     table.app_secret,
                                     limitby=(0, 1)
                                     ).first()
        return c

# =============================================================================
class S3MCommonsModel(S3ChannelModel):
    """
        Mobile Commons Inbound SMS Settings
        - Outbound can use Web API
    """

    names = ("msg_mcommons_channel",)

    def model(self):

        #T = current.T

        define_table = self.define_table
        set_method = self.set_method

        # ---------------------------------------------------------------------
        tablename = "msg_mcommons_channel"
        define_table(tablename,
                     self.super_link("channel_id", "msg_channel"),
                     Field("name"),
                     Field("description"),
                     Field("enabled", "boolean",
                           default = True,
                           #label = T("Enabled?"),
                           represent = s3_yes_no_represent,
                           ),
                     Field("campaign_id", length=128, unique=True,
                           requires = IS_NOT_EMPTY(),
                           ),
                     Field("url",
                           default = \
                              "https://secure.mcommons.com/api/messages",
                           requires = IS_URL()
                           ),
                     Field("username",
                           requires = IS_NOT_EMPTY(),
                           ),
                     Field("password", "password",
                           readable = False,
                           requires = IS_NOT_EMPTY(),
                           ),
                     Field("query"),
                     Field("timestmp", "datetime",
                           writable = False,
                           ),
                     *s3_meta_fields())

        self.configure(tablename,
                       onaccept = self.msg_channel_onaccept,
                       super_entity = "msg_channel",
                       )

        set_method("msg", "mcommons_channel",
                   method = "enable",
                   action = self.msg_channel_enable_interactive)

        set_method("msg", "mcommons_channel",
                   method = "disable",
                   action = self.msg_channel_disable_interactive)

        set_method("msg", "mcommons_channel",
                   method = "poll",
                   action = self.msg_channel_poll)

        # ---------------------------------------------------------------------
        return dict()

# =============================================================================
class S3ParsingModel(S3Model):
    """
        Message Parsing Model
    """

    names = ("msg_parser",
             "msg_parsing_status",
             "msg_session",
             "msg_keyword",
             "msg_sender",
             "msg_parser_enabled",
             "msg_parser_enable",
             "msg_parser_disable",
             "msg_parser_enable_interactive",
             "msg_parser_disable_interactive",
             )

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
        define_table(tablename,
                     # Source
                     channel_id(ondelete = "CASCADE"),
                     Field("function_name",
                           label = T("Parser"),
                           ),
                     Field("enabled", "boolean",
                           default = True,
                           label = T("Enabled?"),
                           represent = s3_yes_no_represent,
                           ),
                     *s3_meta_fields())

        self.configure(tablename,
                       onaccept = self.msg_parser_onaccept,
                       )

        set_method("msg", "parser",
                   method = "enable",
                   action = self.parser_enable_interactive)

        set_method("msg", "parser",
                   method = "disable",
                   action = self.parser_disable_interactive)

        set_method("msg", "parser",
                   method = "parse",
                   action = self.parser_parse)

        # ---------------------------------------------------------------------
        # Message parsing status
        # - component to core msg_message table
        #
        tablename = "msg_parsing_status"
        define_table(tablename,
                     # Component, not Instance
                     message_id(ondelete = "CASCADE"),
                     # Source
                     channel_id(ondelete = "CASCADE"),
                     Field("is_parsed", "boolean",
                           default = False,
                           label = T("Parsing Status"),
                           represent = lambda parsed: \
                                       (parsed and [T("Parsed")] or \
                                                   [T("Not Parsed")])[0],
                           ),
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
        define_table(tablename,
                     Field("from_address"),
                     Field("email"),
                     Field("created_datetime", "datetime",
                           default = current.request.utcnow,
                           ),
                     Field("expiration_time", "integer"),
                     Field("is_expired", "boolean",
                           default = False,
                           ),
                     *s3_meta_fields())

        # ---------------------------------------------------------------------
        # Keywords for Message Parsing
        #
        tablename = "msg_keyword"
        define_table(tablename,
                     Field("keyword",
                           label = T("Keyword"),
                           ),
                     # @ToDo: Move this to a link table
                     self.event_incident_type_id(),
                     *s3_meta_fields())

        # ---------------------------------------------------------------------
        # Senders for Message Parsing
        # - whitelist / blacklist / prioritise
        #
        tablename = "msg_sender"
        define_table(tablename,
                     Field("sender",
                           label = T("Sender"),
                           ),
                     # @ToDo: Make pe_id work for this
                     #self.super_link("pe_id", "pr_pentity"),
                     Field("priority", "integer",
                           label = T("Priority"),
                           ),
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
                                         args = [channel_id, function_name],
                                         period = 300,  # seconds
                                         timeout = 300, # seconds
                                         repeats = 0    # unlimited
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

    names = ("msg_rss_channel",
             "msg_rss",
             )

    def model(self):

        T = current.T

        define_table = self.define_table
        set_method = self.set_method
        super_link = self.super_link

        # ---------------------------------------------------------------------
        # RSS Settings for an account
        #
        tablename = "msg_rss_channel"
        define_table(tablename,
                     # Instance
                     super_link("channel_id", "msg_channel"),
                     Field("name", length=255, unique=True,
                           label = T("Name"),
                           ),
                     Field("description",
                           label = T("Description"),
                           ),
                     Field("enabled", "boolean",
                           default = True,
                           label = T("Enabled?"),
                           represent = s3_yes_no_represent,
                           ),
                     Field("url",
                           label = T("URL"),
                           requires = IS_URL(),
                           ),
                     s3_datetime(label = T("Last Polled"),
                                 writable = False,
                                 ),
                     Field("etag",
                           label = T("ETag"),
                           writable = False
                           ),
                     *s3_meta_fields())

        self.configure(tablename,
                       list_fields = ["name",
                                      "description",
                                      "enabled",
                                      "url",
                                      "date",
                                      "channel_status.status",
                                      ],
                       onaccept = self.msg_channel_onaccept,
                       super_entity = "msg_channel",
                       )

        set_method("msg", "rss_channel",
                   method = "enable",
                   action = self.msg_channel_enable_interactive)

        set_method("msg", "rss_channel",
                   method = "disable",
                   action = self.msg_channel_disable_interactive)

        set_method("msg", "rss_channel",
                   method = "poll",
                   action = self.msg_channel_poll)

        # ---------------------------------------------------------------------
        # RSS Feed Posts
        #
        tablename = "msg_rss"
        define_table(tablename,
                     # Instance
                     super_link("message_id", "msg_message"),
                     self.msg_channel_id(),
                     s3_datetime(default="now",
                                 label = T("Published on"),
                                 ),
                     Field("title",
                           label = T("Title"),
                           ),
                     Field("body", "text",
                           label = T("Content"),
                           ),
                     Field("from_address",
                           label = T("Link"),
                           ),
                     # http://pythonhosted.org/feedparser/reference-feed-author_detail.html
                     Field("author",
                           label = T("Author"),
                           ),
                     # http://pythonhosted.org/feedparser/reference-entry-tags.html
                     Field("tags", "list:string",
                           label = T("Tags"),
                           ),
                     self.gis_location_id(),
                     # Just present for Super Entity
                     Field("inbound", "boolean",
                           default = True,
                           readable = False,
                           writable = False,
                           ),
                     *s3_meta_fields())

        self.configure(tablename,
                       deduplicate = self.msg_rss_duplicate,
                       list_fields = ["channel_id",
                                      "title",
                                      "from_address",
                                      "date",
                                      "body"
                                      ],
                       super_entity = current.s3db.msg_message,
                       )

        # ---------------------------------------------------------------------
        return dict()

    # ---------------------------------------------------------------------
    @staticmethod
    def msg_rss_duplicate(item):
        """
            Import item deduplication, match by link (from_address)

            @param item: the S3ImportItem instance
        """

        from_address = item.data.get("from_address")
        table = item.table
        query = (table.from_address == from_address)
        duplicate = current.db(query).select(table.id,
                                             limitby=(0, 1)).first()
        if duplicate:
            item.id = duplicate.id
            item.method = item.METHOD.UPDATE

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

    names = ("msg_sms",)

    def model(self):

        #T = current.T
        user = current.auth.user
        if user and user.organisation_id:
            # SMS Messages need to be tagged to their org so that they can be sent through the correct gateway
            default = user.organisation_id
        else:
            default = None

        # ---------------------------------------------------------------------
        # SMS Messages: InBox & Outbox
        #
        tablename = "msg_sms"
        self.define_table(tablename,
                          # Instance
                          self.super_link("message_id", "msg_message"),
                          self.msg_channel_id(),
                          self.org_organisation_id(default = default),
                          s3_datetime(default="now"),
                          Field("body", "text",
                                # Allow multi-part SMS
                                #length = 160,
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
                          # Used e.g. for Clickatell
                          Field("remote_id",
                                #label = T("Remote ID"),
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

    names = ("msg_sms_outbound_gateway",
             "msg_sms_modem_channel",
             "msg_sms_smtp_channel",
             "msg_sms_webapi_channel",
             )

    def model(self):

        #T = current.T

        configure = self.configure
        define_table = self.define_table

        # ---------------------------------------------------------------------
        # SMS Outbound Gateway
        # - select which gateway is in active use for which Organisation/Branch
        #
        tablename = "msg_sms_outbound_gateway"
        define_table(tablename,
                     self.msg_channel_id(
                        requires = IS_ONE_OF(current.db, "msg_channel.channel_id",
                                             S3Represent(lookup="msg_channel"),
                                             instance_types = ("msg_sms_modem_channel",
                                                               "msg_sms_webapi_channel",
                                                               "msg_sms_smtp_channel",
                                                               ),
                                             sort = True,
                                             ),
                                         ),
                     #Field("outgoing_sms_handler", length=32,
                     #      requires = IS_IN_SET(current.msg.GATEWAY_OPTS,
                     #                           zero = None),
                     #      ),
                     # Allow selection of different gateways based on Organisation/Branch
                     self.org_organisation_id(),
                     # @ToDo: Allow selection of different gateways based on destination Location
                     #self.gis_location_id(),
                     # @ToDo: Allow addition of relevant country code (currently in deployment_settings)
                     #Field("default_country_code", "integer",
                     #      default = 44),
                     *s3_meta_fields())

        # ---------------------------------------------------------------------
        # SMS Modem Channel
        #
        tablename = "msg_sms_modem_channel"
        define_table(tablename,
                     self.super_link("channel_id", "msg_channel"),
                     Field("name"),
                     Field("description"),
                     Field("modem_port"),
                     Field("modem_baud", "integer",
                           default = 115200,
                           ),
                     Field("enabled", "boolean",
                           default = True,
                           ),
                     Field("max_length", "integer",
                           default = 160,
                           ),
                     *s3_meta_fields())

        configure(tablename,
                  super_entity = "msg_channel",
                  )

        # ---------------------------------------------------------------------
        # SMS via SMTP Channel
        #
        tablename = "msg_sms_smtp_channel"
        define_table(tablename,
                     self.super_link("channel_id", "msg_channel"),
                     Field("name"),
                     Field("description"),
                     Field("address", length=64,
                           requires = IS_NOT_EMPTY(),
                           ),
                     Field("subject", length=64),
                     Field("enabled", "boolean",
                           default = True,
                           ),
                     Field("max_length", "integer",
                           default = 160,
                           ),
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
        # https://www.twilio.com/docs/api/rest/sending-messages
        #
        tablename = "msg_sms_webapi_channel"
        define_table(tablename,
                     self.super_link("channel_id", "msg_channel"),
                     Field("name"),
                     Field("description"),
                     Field("url",
                           default = "https://api.clickatell.com/http/sendmsg", # Clickatell
                           #default = "https://secure.mcommons.com/api/send_message", # Mobile Commons
                           #default = "https://api.twilio.com/2010-04-01/Accounts/{AccountSid}/Messages", # Twilio (Untested)
                           requires = IS_URL(),
                           ),
                     Field("parameters",
                           default = "user=yourusername&password=yourpassword&api_id=yourapiid", # Clickatell
                           #default = "campaign_id=yourid", # Mobile Commons
                           #default = "From={RegisteredTelNumber}", # Twilio (Untested)
                           ),
                     Field("message_variable", "string",
                           default = "text", # Clickatell
                           #default = "body", # Mobile Commons
                           #default = "Body", # Twilio (Untested)
                           requires = IS_NOT_EMPTY(),
                           ),
                     Field("to_variable", "string",
                           default = "to", # Clickatell
                           #default = "phone_number", # Mobile Commons
                           #default = "To", # Twilio (Untested)
                           requires = IS_NOT_EMPTY(),
                           ),
                     Field("max_length", "integer",
                           default = 480, # Clickatell concat 3
                           ),
                     # If using HTTP Auth (e.g. Mobile Commons)
                     Field("username"),
                     Field("password"),
                     Field("enabled", "boolean",
                           default = True,
                           ),
                     *s3_meta_fields())

        configure(tablename,
                  super_entity = "msg_channel",
                  )

        # ---------------------------------------------------------------------
        return dict()

# =============================================================================
class S3TropoModel(S3Model):
    """
        Tropo can be used to send & receive SMS, Twitter & XMPP

        https://www.tropo.com
    """

    names = ("msg_tropo_channel",
             "msg_tropo_scratch",
             )

    def model(self):

        #T = current.T

        define_table = self.define_table
        set_method = self.set_method

        # ---------------------------------------------------------------------
        # Tropo Channels
        #
        tablename = "msg_tropo_channel"
        define_table(tablename,
                     self.super_link("channel_id", "msg_channel"),
                     Field("name"),
                     Field("description"),
                     Field("enabled", "boolean",
                           default = True,
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
                   method = "enable",
                   action = self.msg_channel_enable_interactive)

        set_method("msg", "tropo_channel",
                   method = "disable",
                   action = self.msg_channel_disable_interactive)

        set_method("msg", "tropo_channel",
                   method = "poll",
                   action = self.msg_channel_poll)

        # ---------------------------------------------------------------------
        # Tropo Scratch pad for outbound messaging
        #
        tablename = "msg_tropo_scratch"
        define_table(tablename,
                     Field("row_id", "integer"),
                     Field("message_id", "integer"),
                     Field("recipient"),
                     Field("message"),
                     Field("network"),
                     )

        # ---------------------------------------------------------------------
        return dict()

# =============================================================================
class S3TwilioModel(S3ChannelModel):
    """
        Twilio Inbound SMS channel
        - for Outbound, use Web API
    """

    names = ("msg_twilio_channel",
             "msg_twilio_sid",
             )

    def model(self):

        #T = current.T

        define_table = self.define_table
        set_method = self.set_method

        # ---------------------------------------------------------------------
        # Twilio Channels
        #
        tablename = "msg_twilio_channel"
        define_table(tablename,
                     # Instance
                     self.super_link("channel_id", "msg_channel"),
                     Field("name"),
                     Field("description"),
                     Field("enabled", "boolean",
                           default = True,
                           #label = T("Enabled?"),
                           represent = s3_yes_no_represent,
                           ),
                     Field("account_name", length=255, unique=True),
                     Field("url",
                           default = \
                               "https://api.twilio.com/2010-04-01/Accounts"
                           ),
                     Field("account_sid", length=64,
                           requires = IS_NOT_EMPTY(),
                           ),
                     Field("auth_token", "password", length=64,
                           readable = False,
                           requires = IS_NOT_EMPTY(),
                           ),
                     *s3_meta_fields())

        self.configure(tablename,
                       onaccept = self.msg_channel_onaccept,
                       super_entity = "msg_channel",
                       )

        set_method("msg", "twilio_channel",
                   method = "enable",
                   action = self.msg_channel_enable_interactive)

        set_method("msg", "twilio_channel",
                   method = "disable",
                   action = self.msg_channel_disable_interactive)

        set_method("msg", "twilio_channel",
                   method = "poll",
                   action = self.msg_channel_poll)

        # ---------------------------------------------------------------------
        # Twilio Message extensions
        # - store message sid to know which ones we've already downloaded
        #
        tablename = "msg_twilio_sid"
        define_table(tablename,
                     # Component not Instance
                     self.msg_message_id(ondelete = "CASCADE"),
                     Field("sid"),
                     *s3_meta_fields())

        # ---------------------------------------------------------------------
        return dict()

# =============================================================================
class S3TwitterModel(S3Model):

    names = ("msg_twitter_channel",
             "msg_twitter",
             )

    def model(self):

        T = current.T
        db = current.db

        configure = self.configure
        define_table = self.define_table
        set_method = self.set_method

        # ---------------------------------------------------------------------
        # Twitter Channel
        #
        password_widget = S3PasswordWidget()
        tablename = "msg_twitter_channel"
        define_table(tablename,
                     #Instance
                     self.super_link("channel_id", "msg_channel"),
                     # @ToDo: Allow different Twitter accounts for different PEs (Orgs / Teams)
                     #self.pr_pe_id(),
                     Field("name"),
                     Field("description"),
                     Field("enabled", "boolean",
                           default = True,
                           label = T("Enabled?"),
                           represent = s3_yes_no_represent,
                           ),
                     Field("twitter_account"),
                     Field("consumer_key", "password", 
                           widget = password_widget,
                           ),
                     Field("consumer_secret", "password",
                           widget = password_widget,
                           ),
                     Field("access_token", "password",
                           widget = password_widget,
                           ),
                     Field("access_token_secret", "password",
                           widget = password_widget,
                           ),
                     *s3_meta_fields())

        configure(tablename,
                  onaccept = self.msg_channel_onaccept,
                  #onvalidation = self.twitter_channel_onvalidation
                  super_entity = "msg_channel",
                  )

        set_method("msg", "twitter_channel",
                   method = "enable",
                   action = self.msg_channel_enable_interactive)

        set_method("msg", "twitter_channel",
                   method = "disable",
                   action = self.msg_channel_disable_interactive)

        set_method("msg", "twitter_channel",
                   method = "poll",
                   action = self.msg_channel_poll)

        # ---------------------------------------------------------------------
        # Twitter Messages: InBox & Outbox
        #
        tablename = "msg_twitter"
        define_table(tablename,
                     # Instance
                     self.super_link("message_id", "msg_message"),
                     self.msg_channel_id(),
                     s3_datetime(default = "now",
                                 label = T("Posted on"),
                                 ),
                     Field("body", length=140,
                           label = T("Message"),
                           ),
                     Field("from_address", #notnull=True,
                           label = T("From"),
                           represent = self.twitter_represent,
                           requires = IS_NOT_EMPTY(),
                           ),
                     Field("to_address",
                           label = T("To"),
                           represent = self.twitter_represent,
                           ),
                     Field("inbound", "boolean",
                           default = False,
                           label = T("Direction"),
                           represent = lambda direction: \
                                       (direction and [T("In")] or \
                                                      [T("Out")])[0],
                           ),
                     Field("msg_id", # Twitter Message ID
                           readable = False,
                           writable = False,
                           ),
                     *s3_meta_fields())

        configure(tablename,
                  list_fields = ["id",
                                 #"priority",
                                 #"category",
                                 "body",
                                 "from_address",
                                 "date",
                                 #"location_id",
                                 ],
                  #orderby = ~table.priority,
                  super_entity = "msg_message",
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
                                                           limitby=(0, 1)).first()
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

        https://dev.twitter.com/docs/api/1.1/get/search/tweets
    """

    names = ("msg_twitter_search",
             "msg_twitter_result",
             )

    def model(self):

        T = current.T
        db = current.db

        configure = self.configure
        define_table = self.define_table
        set_method = self.set_method

        # ---------------------------------------------------------------------
        # Twitter Search Query
        #
        tablename = "msg_twitter_search"
        define_table(tablename,
                     Field("keywords", "text",
                           label = T("Keywords"),
                           ),
                     # @ToDo: Allow setting a Point & Radius for filtering by geocode
                     #self.gis_location_id(),
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
        search_id = S3ReusableField("search_id", "reference %s" % tablename,
                    label = T("Search Query"),
                    ondelete = "CASCADE",
                    represent = represent,
                    requires = IS_EMPTY_OR(
                                IS_ONE_OF_EMPTY(db, "msg_twitter_search.id")
                                ),
                    )

        set_method("msg", "twitter_search",
                   method = "poll",
                   action = self.twitter_search_poll)

        set_method("msg", "twitter_search",
                   method = "keygraph",
                   action = self.twitter_keygraph)

        set_method("msg", "twitter_result",
                   method = "timeline",
                   action = self.twitter_timeline)

        # ---------------------------------------------------------------------
        # Twitter Search Results
        #
        # @ToDo: Store the places mentioned in the Tweet as linked Locations
        #
        tablename = "msg_twitter_result"
        define_table(tablename,
                     # Instance
                     self.super_link("message_id", "msg_message"),
                     # Just present for Super Entity
                     #self.msg_channel_id(),
                     search_id(),
                     s3_datetime(default="now",
                                 label = T("Tweeted on"),
                                 ),
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
                     self.gis_location_id(),
                     # Just present for Super Entity
                     #Field("inbound", "boolean",
                     #      default = True,
                     #      readable = False,
                     #      writable = False,
                     #      ),
                     *s3_meta_fields())

        configure(tablename,
                  list_fields = [#"category",
                                 #"priority",
                                 "body",
                                 "from_address",
                                 "date",
                                 "location_id",
                                 ],
                  #orderby=~table.priority,
                  super_entity = "msg_message",
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

        id = r.id
        tablename = r.tablename
        current.s3task.async("msg_twitter_search", args=[id])
        current.session.confirmation = \
            current.T("The search request has been submitted, so new messages should appear shortly - refresh to see them")
        # Filter results to this Search
        redirect(URL(f="twitter_result",
                     vars={"~.search_id": id}))

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
        # @ToDo: Link to KeyGraph results
        redirect(URL(f="twitter_result"))

# =============================================================================
    @staticmethod
    def twitter_timeline(r, **attr):
        """
            Display the Tweets on a Simile Timeline

            http://www.simile-widgets.org/wiki/Reference_Documentation_for_Timeline
        """

        if r.representation == "html" and r.name == "twitter_result":
            response = current.response
            s3 = response.s3
            appname = r.application

            # Add core Simile Code
            s3.scripts.append("/%s/static/scripts/simile/timeline/timeline-api.js" % appname)

            # Add our control script
            if s3.debug:
                s3.scripts.append("/%s/static/scripts/S3/s3.timeline.js" % appname)
            else:
                s3.scripts.append("/%s/static/scripts/S3/s3.timeline.min.js" % appname)

            # Add our data
            # @ToDo: Make this the initial data & then collect extra via REST with a stylesheet
            # add in JS using S3.timeline.eventSource.addMany(events) where events is a []
            if r.record:
                # Single record
                rows = [r.record]
            else:
                # Multiple records
                # @ToDo: Load all records & sort to closest in time
                # http://stackoverflow.com/questions/7327689/how-to-generate-a-sequence-of-future-datetimes-in-python-and-determine-nearest-d
                rows = r.resource.select(["date", "body"], limit=2000, as_rows=True)

            data = {"dateTimeFormat": "iso8601",
                    }

            now = r.utcnow
            tl_start = tl_end = now
            events = []
            import re
            for row in rows:
                # Dates
                start = row.date or ""
                if start:
                    if start < tl_start:
                        tl_start = start
                    if start > tl_end:
                        tl_end = start
                    start = start.isoformat()

                title = (re.sub(r"(?<=^|(?<=[^a-zA-Z0-9-_\.]))@([A-Za-z]+[A-Za-z0-9]+)|RT", "", row.body))
                if len(title) > 30:
                    title = title[:30]

                events.append({"start": start,
                               "title": title,
                               "description": row.body,
                               })
            data["events"] = events
            data = json.dumps(data, separators=SEPARATORS)

            code = "".join((
'''S3.timeline.data=''', data, '''
S3.timeline.tl_start="''', tl_start.isoformat(), '''"
S3.timeline.tl_end="''', tl_end.isoformat(), '''"
S3.timeline.now="''', now.isoformat(), '''"
'''))

            # Control our code in static/scripts/S3/s3.timeline.js
            s3.js_global.append(code)

            # Create the DIV
            item = DIV(_id="s3timeline", _class="s3-timeline")

            output = dict(item=item)

            # Maintain RHeader for consistency
            if attr.get("rheader"):
                rheader = attr["rheader"](r)
                if rheader:
                    output["rheader"] = rheader

            output["title"] = current.T("Twitter Timeline")
            response.view = "timeline.html"
            return output

        else:
            r.error(405, current.ERROR.BAD_METHOD)
# =============================================================================
class S3XFormsModel(S3Model):
    """
        XForms are used by the ODK Collect mobile client

        http://eden.sahanafoundation.org/wiki/BluePrint/Mobile#Android
    """

    names = ("msg_xforms_store",)

    def model(self):

        #T = current.T

        # ---------------------------------------------------------------------
        # SMS store for persistence and scratch pad for combining incoming xform chunks
        tablename = "msg_xforms_store"
        self.define_table(tablename,
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

    names = ("msg_basestation",)

    def model(self):

        T = current.T

        define_table = self.define_table

        # ---------------------------------------------------------------------
        # Base Stations (Cell Towers)
        #
        tablename = "msg_basestation"
        define_table(tablename,
                     self.super_link("site_id", "org_site"),
                     Field("name", notnull=True,
                           length=64, # Mayon Compatibility
                           label = T("Name"),
                           ),
                     Field("code", length=10, # Mayon compatibility
                           label = T("Code"),
                           # Deployments that don't wants site codes can hide them
                           #readable = False,
                           #writable = False,
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
        ADD_BASE = T("Create Base Station")
        current.response.s3.crud_strings[tablename] = Storage(
            label_create=T("Create Base Station"),
            title_display=T("Base Station Details"),
            title_list=T("Base Stations"),
            title_update=T("Edit Base Station"),
            title_upload=T("Import Base Stations"),
            title_map=T("Map of Base Stations"),
            label_list_button=T("List Base Stations"),
            label_delete_button=T("Delete Base Station"),
            msg_record_created=T("Base Station added"),
            msg_record_modified=T("Base Station updated"),
            msg_record_deleted=T("Base Station deleted"),
            msg_list_empty=T("No Base Stations currently registered"))

        self.configure(tablename,
                       deduplicate = self.msg_basestation_duplicate,
                       super_entity = "org_site",
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

        name = item.data.get("name")
        table = item.table
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

# END =========================================================================
