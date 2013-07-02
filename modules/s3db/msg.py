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

__all__ = ["S3MessagingModel",
           "S3BaseStationModel",
           "S3ChannelModel",
           "S3EmailInboundModel",
           "S3MCommonsModel",
           "S3ParsingModel",
           "S3RSSModel",
           "S3SMSOutboundModel",
           "S3SubscriptionModel",
           "S3TropoModel",
           "S3TwilioModel",
           "S3TwitterModel",
           "S3XFormsModel",
           "msg_search_subscription_notifications",
           ]

from gluon import *
from gluon.storage import Storage
from ..s3 import *

# =============================================================================
class S3MessagingModel(S3Model):
    """
        Messaging Framework
        - core models defined here

        @ToDo: Make Message a SuperEntity with each channel type having a separate instance
    """

    names = ["msg_inbox",
             "msg_log",
             "msg_limit",
             "msg_outbox",
             "msg_message_id",
             ]

    def model(self):

        T = current.T
        db = current.db

        UNKNOWN_OPT = current.messages.UNKNOWN_OPT

        configure = self.configure
        define_table = self.define_table
        super_link = self.super_link

        # Message priority
        msg_priority_opts = {3 : T("High"),
                             2 : T("Medium"),
                             1 : T("Low"),
                             }

        # ---------------------------------------------------------------------
        # InBox - all Inbound Messages
        #
        tablename = "msg_inbox"
        table = define_table(tablename,
                             Field("channel"),
                             Field("sender_phone"),
                             Field("received_on", "datetime"),
                             Field("subject"),
                             Field("body"),
                             *s3_meta_fields()
                             )

        # ---------------------------------------------------------------------
        # Message Log - all Inbound & Outbound Messages
        #
        tablename = "msg_log"
        table = define_table(tablename,
                             super_link("pe_id", "pr_pentity"),
                             Field("sender"),        # The name to go out incase of the email, if set used
                             Field("fromaddress"),   # From address if set changes sender to this
                             Field("recipient"),
                             Field("subject", length=78),
                             Field("message", "text"),
                             #Field("attachment", "upload", autodelete = True), #TODO
                             Field("verified", "boolean", default = False,
                                   represent = s3_yes_no_represent),
                             Field("verified_comments", "text"),
                             Field("actionable", "boolean", default = True,
                                   represent = s3_yes_no_represent),
                             Field("actioned", "boolean", default = False,
                                   represent = s3_yes_no_represent),
                             Field("actioned_comments", "text"),
                             Field("priority", "integer", default = 1,
                                   requires = IS_NULL_OR(IS_IN_SET(msg_priority_opts)),
                                   label = T("Priority")),
                             Field("inbound", "boolean", default = False,
                                   represent = lambda direction: \
                                       (direction and ["In"] or ["Out"])[0],
                                   label = T("Direction")),
                             Field("is_parsed", "boolean", default = False,
                                   represent = lambda status: \
                                       (status and ["Parsed"] or ["Not Parsed"])[0],
                                   label = T("Parsing Status")),
                             Field("reply", "text" ,
                                   label = T("Reply")),
                             Field("source_task_id",
                                   label = T("Message Source")),
                             *s3_meta_fields())

        configure(tablename,
                  list_fields=["id",
                               "inbound",
                               "pe_id",
                               "fromaddress",
                               "recipient",
                               "subject",
                               "message",
                               "verified",
                               #"verified_comments",
                               "actionable",
                               "actioned",
                               #"actioned_comments",
                               #"priority",
                               "is_parsed",
                               "reply",
                               "source_task_id"
                               ])

        # Components
        self.add_component("msg_outbox", msg_log="message_id")

        # Reusable Message ID
        message_id = S3ReusableField("message_id", table,
                                     requires = IS_NULL_OR(
                                                    IS_ONE_OF_EMPTY(db, "msg_log.id")),
                                     represent = self.message_represent,
                                     ondelete = "RESTRICT")

        # ---------------------------------------------------------------------
        # Outbound Messages
        # ---------------------------------------------------------------------
        # Show only the supported messaging methods
        msg_contact_method_opts = current.msg.MSG_CONTACT_OPTS

        # Valid message outbox statuses
        msg_status_type_opts = {1 : T("Unsent"),
                                2 : T("Sent"),
                                3 : T("Draft"),
                                4 : T("Invalid"),
                                }

        opt_msg_status = S3ReusableField("status", "integer",
                                         notnull=True,
                                         requires = IS_IN_SET(msg_status_type_opts,
                                                              zero=None),
                                         default = 1,
                                         label = T("Status"),
                                         represent = lambda opt: \
                                            msg_status_type_opts.get(opt, UNKNOWN_OPT))

        # Outbox - needs to be separate to Log since a single message sent needs different outbox entries for each recipient
        tablename = "msg_outbox"
        table = define_table(tablename,
                             message_id(),
                             super_link("pe_id", "pr_pentity"), # Person/Group to send the message out to
                             Field("address"),   # If set used instead of picking up from pe_id
                             Field("pr_message_method", length=32,
                                   requires = IS_IN_SET(msg_contact_method_opts,
                                                        zero=None),
                                   default = "EMAIL",
                                   label = T("Contact Method"),
                                   represent = lambda opt: \
                                        msg_contact_method_opts.get(opt, UNKNOWN_OPT)),
                             opt_msg_status(),
                             Field("system_generated", "boolean", default = False),
                             Field("log"),
                             *s3_meta_fields())

        configure(tablename,
                  orderby = ~table.created_on,
                  list_fields=["id",
                               "message_id",
                               "pe_id",
                               "status",
                               "log",
                               ])

        # ---------------------------------------------------------------------
        # Message Limit
        #  Used to limit the number of emails sent from the system
        #  - works by simply recording an entry for the timestamp to be checked against
        #
        # @ToDo: have separate limits for each Outbound Channel
        #
        tablename = "msg_limit"
        table = define_table(tablename,
                             *s3_timestamp())

        # ---------------------------------------------------------------------
        tablename = "msg_message"
        table = self.super_entity(tablename, "message_id",
                                  Field("sender",
                                        label = T("Sender")),
                                  Field("source",
                                        label = T("Source")),
                                  Field("body",
                                        label = T("Body")),
                                  Field("inbound", "boolean", default = False,
                                        represent = lambda direction: \
                                            (direction and ["In"] or ["Out"])[0],
                                        label = T("Direction")),
                                  # @ToDo: Indicate whether channel can be used for Inbound or Outbound
                                  #Field("inbound", "boolean",
                                  #      label = T("Inbound?")),
                                  #Field("outbound", "boolean",
                                  #      label = T("Outbound?")),
                                  )
        table.instance_type.readable = True

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        return Storage(
                msg_message_id=message_id,
            )

    # -------------------------------------------------------------------------
    @staticmethod
    def message_represent(id):
        """ Represent a Message in the Log """

        if not id:
            return current.messages["NONE"]

        db = current.db
        table = db.msg_log
        record = db(table.id == id).select(table.subject,
                                           table.message,
                                           limitby=(0, 1)).first()
        try:
            if record.subject:
                # EMail will use Subject
                return record.subject
        except:
            return current.messages.UNKNOWN_OPT

        # SMS/Tweet will use 1st 80 characters from body
        text = record.message
        if len(text) < 80:
            return text
        else:
            return "%s..." % text[:76]

# =============================================================================
class S3BaseStationModel(S3Model):

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
                       super_entity=("org_site"),
                       deduplciate = self.msg_basestation_duplicate,
                       )

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return Storage()

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
class S3ChannelModel(S3Model):
    """
        Messaging Channels
        - all Inbound & Outbound channels for messages are instances of this super-entity

        Knowing which Source Incoming Messages came in on allows correlation to
        Outbound messages (campaign_message, deployment notificstions, etc)

        @ToDo: Build a class S3ChannelTemplateModel(S3Model) which can have all
               the enable/disable controllers as methods & have Channel instances inherit from this
    """

    names = ["msg_channel"]

    def model(self):

        T = current.T

        define_table = self.define_table

        #----------------------------------------------------------------------
        # Super entity: msg_channel
        #
        channel_types = Storage(msg_email_inbound_channel = T("Email (Inbound)"),
                                # @ToDo:
                                #msg_facebook_channel = T("Facebook"),
                                msg_mcommons_channel = T("Mobile Commons (Inbound)"),
                                msg_sms_modem_channel = T("SMS Modem"),
                                msg_sms_webapi_channel = T("SMS WebAPI (Outbound)"),
                                msg_sms_smtp_channel = T("SMS via SMTP (Outbound)"),
                                msg_tropo_channel = T("Tropo"),
                                msg_twilio_inbound_channel = T("Twilio (Inbound)"),
                                msg_twitter_channel = T("Twitter"),
                                )

        tablename = "msg_channel"
        table = self.super_entity(tablename, "channel_id",
                                  channel_types,
                                  Field("name",
                                        label = T("Name")),
                                  Field("description",
                                        label = T("Description")),
                                  # @ToDo: Indicate whether channel can be used for Inbound or Outbound
                                  #Field("inbound", "boolean",
                                  #      label = T("Inbound?")),
                                  #Field("outbound", "boolean",
                                  #      label = T("Outbound?")),
                                  )
        table.instance_type.readable = True

        # ---------------------------------------------------------------------
        return Storage(
            )

    # -----------------------------------------------------------------------------
    @staticmethod
    def schedule(s3task):
        """
            Master Schedule method for various channels.
        """

        T = current.T
        db = current.db
        s3db = current.s3db
        session = current.session
        request = current.request
        function = request.function
        accountID = []

        if function == "schedule_email":
          f = "email_inbound_channel"
          table = s3db.msg_email_inbound_channel
          task = "msg_email_poll"

          try:
              id = request.args[0]
          except:
              session.error = T("Source not specified!")
              redirect(URL(f=f))

          record = db(table.id == id).select(table["username"],
                                      table["server"], limitby=(0, 1)).first()
          accountID.append(str(record["username"]))
          accountID.append(str(record["server"]))
        elif function == "schedule_twilio_sms":
          f = "twilio_inbound_channel"
          table = s3db.msg_twilio_inbound_channel
          account_id = "account_name"
          task = "msg_twilio_poll"
        elif function == "schedule_mcommons_sms":
          f = "mcommons_channel"
          table = s3db.msg_mcommons_channel
          account_id = "campaign_id"
          task = "msg_mcommons_poll"


        if not accountID:

          try:
              id = request.args[0]
          except:
              session.error = T("Source not specified!")
              redirect(URL(f=f))

          record = db(table.id == id).select(table[account_id],
                                           limitby=(0, 1)).first()

          accountID.append(str(record[account_id]))

        # A list "accountID" is passed as the variable to identify
        # the individual channel setting. A list is used so that
        # multiple paramters (e.g. username & server) can be passed
        s3task.schedule_task(task,
                             vars={"account_id": accountID},
                             period=300,  # seconds
                             timeout=300, # seconds
                             repeats=0    # unlimited
                             )

        redirect(URL(f=f))

    # -----------------------------------------------------------------------------
    @staticmethod
    def enable():
        """
            Master enable method for various channels.
        """

        T = current.T
        db = current.db
        s3db = current.s3db
        session = current.session
        request = current.request
        function = request.function

        if function == "enable_email":
          f = "email_inbound_channel"
          table = s3db.msg_email_inbound_channel

          try:
              id = request.args[0]
          except:
              session.error = T("Source not specified!")
              redirect(URL(f=f))

          stable = s3db.scheduler_task

          settings = db(table.id == id).select(table["username"],
                                               table["server"],
                                               limitby=(0, 1)).first()
          records = db(stable.id > 0).select(stable.id,
                                             stable.vars)
          for record in records:
              if "account_id" in record.vars:
                  r = record.vars.split("\"account_id\":")[1]
                  s = r.split("}")[0]
                  q = s.split("\"")[1].split("\"")[0]
                  try:
                    server =  s.split("\"")[3]
                    if (q == settings["username"]) and \
                       (server == settings["server"]):
                        db(stable.id == record.id).update(enabled = True)
                  except:
                    pass

          redirect(URL(f=f))
        elif function == "enable_twilio_sms":
          f = "twilio_inbound_channel"
          table = s3db.msg_twilio_inbound_channel
          account_id = "account_name"
        elif function == "enable_mcommons_sms":
          f = "mcommons_channel"
          table = s3db.msg_mcommons_channel
          account_id = "campaign_id"

        try:
            id = request.args[0]
        except:
            session.error = T("Source not specified!")
            redirect(URL(f=f))

        stable = s3db.scheduler_task

        settings = db(table.id == id).select(table[account_id],
                                             limitby=(0, 1)).first()
        records = db(stable.id > 0).select(stable.id,
                                           stable.vars)
        for record in records:
            if "account_id" in record.vars:
                r = record.vars.split("\"account_id\":")[1]
                s = r.split("}")[0]
                q = s.split("\"")[1].split("\"")[0]
                if (q == settings[account_id]) :
                    db(stable.id == record.id).update(enabled = True)

        redirect(URL(f=f))

    # -----------------------------------------------------------------------------
    @staticmethod
    def disable():
        """
            Master disable method for various channels.
        """

        T = current.T
        db = current.db
        s3db = current.s3db
        session = current.session
        request = current.request
        function = request.function

        if function == "disable_email":
          f = "email_inbound_channel"
          table = s3db.msg_email_inbound_channel

          try:
              id = request.args[0]
          except:
              session.error = T("Source not specified!")
              redirect(URL(f=f))

          stable = s3db.scheduler_task

          settings = db(table.id == id).select(table["username"],
                                               table["server"],
                                               limitby=(0, 1)).first()
          records = db(stable.id > 0).select(stable.id,
                                             stable.vars)
          for record in records:
              if "account_id" in record.vars:
                  r = record.vars.split("\"account_id\":")[1]
                  s = r.split("}")[0]
                  q = s.split("\"")[1].split("\"")[0]
                  try:
                    server =  s.split("\"")[3]
                    if (q == settings["username"]) and \
                       (server == settings["server"]):
                        db(stable.id == record.id).update(enabled = False)
                  except:
                    pass

          redirect(URL(f=f))
        elif function == "disable_twilio_sms":
          f = "twilio_inbound_channel"
          table = s3db.msg_twilio_inbound_channel
          account_id = "account_name"
        elif function == "disable_mcommons_sms":
          f = "mcommons_channel"
          table = s3db.msg_mcommons_channel
          account_id = "campaign_id"

        try:
            id = request.args[0]
        except:
            session.error = T("Source not specified!")
            redirect(URL(f=f))

        stable = s3db.scheduler_task

        settings = db(table.id == id).select(table[account_id],
                                             limitby=(0, 1)).first()
        records = db(stable.id > 0).select(stable.id,
                                           stable.vars)
        for record in records:
            if "account_id" in record.vars:
                r = record.vars.split("\"account_id\":")[1]
                s = r.split("}")[0]
                q = s.split("\"")[1].split("\"")[0]
                if (q == settings[account_id]) :
                    db(stable.id == record.id).update(enabled = False)

        redirect(URL(f=f))

# =============================================================================
class S3EmailInboundModel(S3ChannelModel):
    """
        Inbound Email

        Outbound Email is currently handled via deployment_settings
    """

    names = ["msg_email_inbound_channel",
             "msg_email_inbound_status",
             "msg_email_inbox",
             ]

    def model(self):

        T = current.T

        define_table = self.define_table

        # ---------------------------------------------------------------------
        # Email Inbound Channels
        #
        tablename = "msg_email_inbound_channel"
        table = define_table(tablename,
                             self.super_link("channel_id", "msg_channel"),
                             Field("name"),
                             Field("description"),
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

        self.configure(tablename,
                       super_entity = "msg_channel",
                       )

        # ---------------------------------------------------------------------
        # Email Inbox
        #
        tablename = "msg_email_inbox"
        table = define_table(tablename,
                             self.super_link("message_id", "msg_message"),
                             Field("sender", notnull=True,
                                   label = T("Sender"),
                                   requires = IS_EMAIL()),
                             Field("subject", length=78,    # RFC 2822
                                   label = T("Subject")),
                             Field("body", "text",
                                   label = T("Body")),
                             *s3_meta_fields())

        #table.sender.comment = SPAN("*", _class="req")
        VIEW_EMAIL_INBOX = T("View Email InBox")
        current.response.s3.crud_strings[tablename] = Storage(
            #title_create = T("Add Incoming Email"),
            title_display = T("Email Details"),
            title_list = VIEW_EMAIL_INBOX,
            #title_update = T("Edit Email"),
            title_search = T("Search Email InBox"),
            label_list_button = VIEW_EMAIL_INBOX,
            #label_create_button = T("Add Incoming Email"),
            #msg_record_created = T("Email added"),
            #msg_record_modified = T("Email updated"),
            msg_record_deleted = T("Email deleted"),
            msg_list_empty = T("No Emails currently in InBox"))

        # ---------------------------------------------------------------------
        # Status
        # - @ToDo: What is this used for?
        tablename = "msg_email_inbound_status"
        table = define_table(tablename,
                             Field("status"))

        # ---------------------------------------------------------------------
        return Storage()

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

        # ---------------------------------------------------------------------
        tablename = "msg_mcommons_channel"
        table = define_table(tablename,
                             self.super_link("channel_id", "msg_channel"),
                             Field("name"),
                             Field("description"),
                             Field("campaign_id",
                                   length=128,
                                   unique=True,
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
                       )

        # ---------------------------------------------------------------------
        return Storage()

# =============================================================================
class S3ParsingModel(S3Model):
    """
        Message Parsing Model
    """

    names = ["msg_workflow",
             "msg_session",
             "msg_keyword",
             "msg_sender",
             ]

    def model(self):

        T = current.T

        # ---------------------------------------------------------------------
        # Link between Message Sources and Workflows in parser.py
        #
        tablename = "msg_workflow"
        table = self.define_table(tablename,
                                  # @ToDo: Link this to Channel?
                                  Field("source_task_id",
                                        label = T("Inbound Message Source"),
                                        represent = self.source_represent,
                                        ),
                                  Field("workflow_task_id",
                                        label = T("Workflow")),
                                  *s3_meta_fields())

        # ---------------------------------------------------------------------
        # Login sessions for Message Parsing
        #
        tablename = "msg_session"
        table = self.define_table(tablename,
                                  Field("email"),
                                  Field("created_datetime","datetime",
                                        default = current.request.utcnow),
                                  Field("expiration_time", "integer"),
                                  Field("is_expired", "boolean",
                                        default = False),
                                  Field("sender"),
                                  *s3_meta_fields())

        # ---------------------------------------------------------------------
        # Keywords for Message Parsing
        #
        tablename = "msg_keyword"
        table = self.define_table(tablename,
                                  Field("keyword",
                                        label=T("Keyword")),
                                  # @ToDo: Move this to a link table
                                  self.event_incident_type_id(),
                                  *s3_meta_fields())

        # ---------------------------------------------------------------------
        # Senders for Message Parsing
        #
        tablename = "msg_sender"
        table = self.define_table(tablename,
                                  self.super_link("pe_id", "pr_pentity"),
                                  Field("priority", "integer",
                                        label=T("Priority")),
                                  *s3_meta_fields())

        # ---------------------------------------------------------------------
        return Storage()

    # -------------------------------------------------------------------------
    @staticmethod
    def source_represent(id, show_link=True):
        """
            Represent a Message Source in the Workflow Table

            @ToDo: Extend beyond just Email
        """

        db = current.db
        stable = db.msg_email_inbound_channel
        wtable = db.msg_workflow
        # @ToDo: If we already have the source_task_id, why do we look it up again!?
        source = db(wtable.source_task_id == id).select(wtable.source_task_id,
                                                        limitby=(0, 1)
                                                        ).first()
        setting = db(stable.username == source.source_task_id).select(stable.id,
                                                                      limitby=(0, 1)
                                                                      ).first()
        repr = source.source_task_id
        if setting:
            id = setting.id
            repr = A(repr, _href=URL(f="email_inbound_channel",
                                     args=["update", id]))
            return repr
        else:
            return repr
    # -----------------------------------------------------------------------------
    @staticmethod
    def schedule_parser(s3task):
        """
            Schedule a Parsing Workflow
        """

        T = current.T
        db = current.db
        s3db = current.s3db
        session = current.session
        request = current.request

        try:
            id = request.args[0]
        except:
            session.error = T("Workflow not specified!")
            redirect(URL(f="workflow"))

        table = s3db.msg_workflow
        record = db(table.id == id).select(table.workflow_task_id,
                                           table.source_task_id,
                                           limitby=(0, 1)).first()
        s3task.schedule_task("msg_parse_workflow",
                             vars={"workflow": record.workflow_task_id,
                                   "source": record.source_task_id},
                             period=300,  # seconds
                             timeout=300, # seconds
                             repeats=0    # unlimited
                             )

        redirect(URL(f="workflow"))

    # -----------------------------------------------------------------------------
    @staticmethod
    def enable_parser():
        """
            Enables different parsing workflows.
        """

        T = current.T
        db = current.db
        s3db = current.s3db
        session = current.session
        request = current.request

        try:
            id = request.args[0]
        except:
            session.error = T("Workflow not specified!")
            redirect(URL(f="workflow"))

        stable = s3db.scheduler_task
        wtable = s3db.msg_workflow

        records = db(stable.id > 0).select()
        workflow = db(wtable.id == id).select(wtable.workflow_task_id,
                                              wtable.source_task_id,
                                              limitby=(0, 1)).first()

        for record in records:
            if "workflow" and "source" in record.vars:
                r = record.vars.split("\"workflow\":")[1]
                s = r.split("}")[0]
                s = s.split("\"")[1].split("\"")[0]

                u = record.vars.split("\"source\":")[1]
                v = u.split(",")[0]
                v = v.split("\"")[1]

                if (s == workflow.workflow_task_id) and \
                   (v == workflow.source_task_id):
                    db(stable.id == record.id).update(enabled = True)

        redirect(URL(f="workflow"))
    # -----------------------------------------------------------------------------
    @staticmethod
    def disable_parser():
        """
            Disables different parsing workflows.
        """

        T = current.T
        db = current.db
        s3db = current.s3db
        session = current.session
        request = current.request

        try:
            id = request.args[0]
        except:
            session.error = T("Workflow not specified!")
            redirect(URL(f="workflow"))

        stable = s3db.scheduler_task
        wtable = s3db.msg_workflow

        records = db(stable.id > 0).select()
        workflow = db(wtable.id == id).select(wtable.workflow_task_id,
                                              wtable.source_task_id,
                                              limitby=(0, 1)).first()
        for record in records:
            if "workflow" and "source" in record.vars:
                r = record.vars.split("\"workflow\":")[1]
                s = r.split("}")[0]
                s = s.split("\"")[1].split("\"")[0]

                u = record.vars.split("\"source\":")[1]
                v = u.split(",")[0]
                v = v.split("\"")[1]

                if (s == workflow.workflow_task_id) and (v == workflow.source_task_id) :
                    db(stable.id == record.id).update(enabled = False)

        redirect(URL(f="workflow"))

# =============================================================================
class S3RSSModel(S3ChannelModel):
    """
        RSS channel
    """

    names = ["msg_rss_channel",
             "msg_rss_feed"
             ]

    def model(self):

        T = current.T

        define_table = self.define_table

        # ---------------------------------------------------------------------
        # RSS Settings for an account
        #
        tablename = "msg_rss_channel"
        table = define_table(tablename,
                             self.super_link("channel_id", "msg_channel"),
                             Field("name"),
                             Field("description"),
                             Field("url"),
                             Field("subscribed", "boolean", default = True,
                                    represent = s3_yes_no_represent,
                                    label = T("Subscription Status")),
                             *s3_meta_fields())

        self.configure(tablename,
                       super_entity = "msg_channel",
                       )

        # ---------------------------------------------------------------------
        # RSS Feeds
        #
        tablename = "msg_rss_feed"
        table = define_table(tablename,
                             Field("title"),
                             Field("link"),
                             Field("created_on","datetime"),
                             Field("description"),
                             *s3_meta_fields())

        self.configure(tablename,
                       list_fields = ["title",
                                      "link",
                                      "created_on",
                                      "description"
                                      ]
                       )

        # ---------------------------------------------------------------------
        return Storage()


# =============================================================================
class S3SMSOutboundModel(S3Model):
    """
        SMS: Short Message Service

        These can be sent through a number of different gateways
        - Modem
        - Web API
        - SMTP
        - Tropo
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
        tablename = "msg_sms_modem_channel"
        table = define_table(tablename,
                             self.super_link("channel_id", "msg_channel"),
                             Field("name"),
                             Field("description"),
                             # Nametag to remember account - To be used later
                             #Field("account_name"),
                             Field("modem_port"),
                             Field("modem_baud", "integer", default = 115200),
                             Field("enabled", "boolean", default = True),
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
        return Storage()

# =============================================================================
class S3SubscriptionModel(S3Model):
    """
        Handle Subscription
        - currently this is just for Saved Searches
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
        return Storage()

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

        # ---------------------------------------------------------------------
        # Tropo Channels
        #
        tablename = "msg_tropo_channel"
        table = define_table(tablename,
                             self.super_link("channel_id", "msg_channel"),
                             Field("name"),
                             Field("description"),
                             Field("token_messaging"),
                             #Field("token_voice"),
                             *s3_meta_fields())

        self.configure(tablename,
                       super_entity = "msg_channel",
                       )

        # ---------------------------------------------------------------------
        # Tropo Scratch pad for outbound messaging
        #
        tablename = "msg_tropo_scratch"
        table = define_table(tablename,
                             Field("row_id","integer"),
                             Field("message_id","integer"),
                             Field("recipient"),
                             Field("message"),
                             Field("network")
                             )

        # ---------------------------------------------------------------------
        return Storage()

# =============================================================================
class S3TwilioModel(S3ChannelModel):
    """
        Twilio Inbound SMS channel
    """

    names = ["msg_twilio_inbound_channel",
             "msg_twilio_inbox"
             ]

    def model(self):

        #T = current.T

        define_table = self.define_table

        # ---------------------------------------------------------------------
        # Twilio Channels
        #
        tablename = "msg_twilio_inbound_channel"
        table = define_table(tablename,
                             self.super_link("channel_id", "msg_channel"),
                             Field("name"),
                             Field("description"),
                             Field("account_name",
                                   length=255,
                                   unique=True),
                             Field("url",
                                   default = \
                                   "https://api.twilio.com/2010-04-01/Accounts"
                                   ),
                             Field("account_sid", length=64,
                                   requires=IS_NOT_EMPTY()),
                             Field("auth_token", "password", length=64,
                                   readable = False,
                                   requires=IS_NOT_EMPTY()),
                             *s3_meta_fields())

        self.configure(tablename,
                       super_entity = "msg_channel",
                       )

        # ---------------------------------------------------------------------
        # Twilio InBox
        #
        tablename = "msg_twilio_inbox"
        table = define_table(tablename,
                             Field("sid", length=64),
                             Field("body", "text"),
                             Field("status"),
                             Field("sender"),
                             Field("received_on"),
                             *s3_meta_fields())

        self.configure(tablename,
                       list_fields = ["body",
                                      "sender",
                                      "received_on"
                                      ]
                       )

        # ---------------------------------------------------------------------
        return Storage()

# =============================================================================
class S3TwitterModel(S3Model):

    names = ["msg_twitter_channel",
             "msg_twitter_search",
             "msg_twitter_search_results",
             ]

    def model(self):

        #T = current.T
        db = current.db

        configure = self.configure
        define_table = self.define_table

        # ---------------------------------------------------------------------
        # Twitter Channels
        #
        tablename = "msg_twitter_channel"
        table = define_table(tablename,
                             self.super_link("channel_id", "msg_channel"),
                             Field("name"),
                             Field("description"),
                             Field("pin"),
                             Field("oauth_key",
                                   readable = False, writable = False),
                             Field("oauth_secret",
                                   readable = False, writable = False),
                             Field("twitter_account",
                                   writable = False),
                             *s3_meta_fields())

        configure(tablename,
                  super_entity = "msg_channel",
                  onvalidation = self.twitter_channel_onvalidation
                  )

        # ---------------------------------------------------------------------
        # Twitter Search Queries
        #
        # @ToDo: Use link table to msg_keyword instead?
        tablename = "msg_twitter_search"
        table = define_table(tablename,
                             Field("search_query", length=140),
                             *s3_meta_fields())

        # ---------------------------------------------------------------------
        # @ToDo: Rename as twitter_inbox
        # - Q? Do we need to separate stuff directed at us via @username vs general searching other than by column?
        tablename = "msg_twitter_search_results"
        table = define_table(tablename,
                             Field("tweet", length=140,
                                   writable=False),
                             Field("category",
                                   writable=False),
                             Field("priority", "integer",
                                   writable=False),
                             self.gis_location_id(),
                             Field("posted_by",
                                   represent = self.twitter_represent,
                                   writable=False),
                             Field("posted_at",
                                   writable=False),
                             Field("twitter_search", db.msg_twitter_search,
                                   writable=False),
                             *s3_meta_fields())

        #table.twitter_search.requires = IS_ONE_OF(db, "twitter_search.search_query")
        #table.twitter_search.represent = lambda id: db(db.msg_twitter_search.id == id).select(db.msg_twitter_search.search_query,
                                                                                              #limitby = (0, 1)).first().search_query

        #self.add_component(table, msg_twitter_search="twitter_search")

        configure(tablename,
                  orderby=~table.priority,
                  list_fields=["id",
                               "priority",
                               "category",
                               "location_id",
                               "tweet",
                               "posted_by",
                               "posted_at",
                               "twitter_search",
                               ])

        # ---------------------------------------------------------------------
        return Storage()

    # -------------------------------------------------------------------------
    @staticmethod
    def twitter_represent(nickname, show_link=True):
        """
            Represent a Twitter account
        """

        db = current.db
        s3db = current.s3db
        table = s3db.pr_contact
        query = (table.contact_method == "TWITTER") & \
                (table.value == nickname)
        row = db(query).select(table.pe_id,
                               limitby=(0, 1)).first()
        if row:
            repr = s3db.pr_pentity_represent(row.pe_id, show_label=False)
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
                                  Field("sender", "string", length=20),
                                  Field("fileno", "integer"),
                                  Field("totalno", "integer"),
                                  Field("partno", "integer"),
                                  Field("message", "string", length=160)
                                  )

        # ---------------------------------------------------------------------
        return Storage()

# =============================================================================
def msg_search_subscription_notifications(frequency):
    """
        Send Notifications for all Subscriptions
        - run by Scheduler (models/tasks.py)
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
