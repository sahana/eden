# -*- coding: utf-8 -*-

""" Sahana Eden Messaging Model

    @copyright: 2009-2012 (c) Sahana Software Foundation
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
           "S3CAPModel",
           "S3EmailModel",
           "S3SMSModel",
           "S3SubscriptionModel",
           "S3TropoModel",
           "S3TwitterModel",
           "S3XFormsModel",
        ]

from gluon import *
from gluon.storage import Storage
from ..s3 import *

# =============================================================================
class S3MessagingModel(S3Model):
    """
        Messaging Framework
        - core models defined here
    """

    names = ["msg_log",
             "msg_limit",
             #"msg_tag",
             "msg_outbox",
             #"msg_channel",
             "msg_message_id",
            ]

    def model(self):

        T = current.T
        db = current.db
        s3 = current.response.s3
        msg = current.msg

        UNKNOWN_OPT = current.messages.UNKNOWN_OPT

        # Message priority
        msg_priority_opts = {
            3:T("High"),
            2:T("Medium"),
            1:T("Low")
        }
        # ---------------------------------------------------------------------
        # Message Log - all Inbound & Outbound Messages
        # ---------------------------------------------------------------------
        tablename = "msg_log"
        table = self.define_table(tablename,
                                  self.super_link("pe_id", "pr_pentity"),
                                  Field("sender"),        # The name to go out incase of the email, if set used
                                  Field("fromaddress"),   # From address if set changes sender to this
                                  Field("recipient"),
                                  Field("subject", length=78),
                                  Field("message", "text"),
                                  #Field("attachment", "upload", autodelete = True), #TODO
                                  Field("verified", "boolean", default = False),
                                  Field("verified_comments", "text"),
                                  Field("actionable", "boolean", default = True),
                                  Field("actioned", "boolean", default = False),
                                  Field("actioned_comments", "text"),
                                  Field("priority", "integer", default = 1,
                                        requires = IS_NULL_OR(IS_IN_SET(msg_priority_opts)),
                                        label = T("Priority")),
                                  Field("inbound", "boolean", default = False,
                                        represent = lambda direction: \
                                            (direction and ["In"] or ["Out"])[0],
                                        label = T("Direction")),
                                  *s3.meta_fields())

        self.configure(tablename,
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
                                    #"priority"
                                    ])

        # Components
        self.add_component("msg_outbox", msg_log="message_id")

        # Reusable Message ID
        message_id = S3ReusableField("message_id", db.msg_log,
                                     requires = IS_NULL_OR(IS_ONE_OF(db, "msg_log.id")),
                                     # FIXME: Subject works for Email but not SMS
                                     represent = self.message_represent,
                                     ondelete = "RESTRICT")

        # ---------------------------------------------------------------------
        # Message Limit
        #  Used to limit the number of emails sent from the system
        #  - works by simply recording an entry for the timestamp to be checked against
        # @ToDo: have separate limits for Email & SMS
        tablename = "msg_limit"
        table = self.define_table(tablename,
                                  *s3.timestamp())

        # ---------------------------------------------------------------------
        # Message Tag - Used to tag a message to a resource
        # tablename = "msg_tag"
        # table = self.define_table(tablename,
                                  # message_id(),
                                  # Field("resource"),
                                  # Field("record_uuid", # null in this field implies subscription to the entire resource
                                        # type=s3uuid,
                                        # length=128),
                                  # *s3.meta_fields())

        # self.configure(tablename,
                       # list_fields=[ "id",
                                     # "message_id",
                                     # "record_uuid",
                                     # "resource",
                                    # ])

        # ---------------------------------------------------------------------
        # Outbound Messages
        # ---------------------------------------------------------------------
        # Show only the supported messaging methods
        msg_contact_method_opts = msg.MSG_CONTACT_OPTS

        # Valid message outbox statuses
        msg_status_type_opts = {
            1:T("Unsent"),
            2:T("Sent"),
            3:T("Draft"),
            4:T("Invalid")
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
        table = self.define_table(tablename,
                                  message_id(),
                                  self.super_link("pe_id", "pr_pentity"), # Person/Group to send the message out to
                                  Field("address"),   # If set used instead of picking up from pe_id
                                  Field("pr_message_method",
                                        length=32,
                                        requires = IS_IN_SET(msg_contact_method_opts,
                                                             zero=None),
                                        default = "EMAIL",
                                        label = T("Contact Method"),
                                        represent = lambda opt: \
                                            msg_contact_method_opts.get(opt, UNKNOWN_OPT)),
                                  opt_msg_status(),
                                  Field("system_generated", "boolean", default = False),
                                  Field("log"),
                                  *s3.meta_fields())

        self.configure(tablename,
                       list_fields=[ "id",
                                     "message_id",
                                     "pe_id",
                                     "status",
                                     "log",
                                    ])

        # ---------------------------------------------------------------------
        # Inbound Messages
        # ---------------------------------------------------------------------
        # Channel - For inbound messages this tells which channel the message came in from.
        tablename = "msg_channel"
        table = self.define_table(tablename,
                                  message_id(),
                                  Field("pr_message_method",
                                        length=32,
                                        requires = IS_IN_SET(msg_contact_method_opts,
                                                             zero=None),
                                        default = "EMAIL"),
                                  Field("log"),
                                  *s3.meta_fields())

        # ---------------------------------------------------------------------
        # Pass variables back to global scope (response.s3.*)
        return Storage(
                msg_message_id=message_id,
            )

    # -------------------------------------------------------------------------
    @staticmethod
    def message_represent(id):
        """ Represent a Message in the Log """

        NONE = current.messages.NONE
        if not id:
            return NONE

        db = current.db
        s3db = current.s3db
        table = s3db.msg_log
        query = (table.id == id)

        record = db(query).select(table.subject,
                                  limitby=(0, 1)).first()
        if not record:
            return NONE

        if record.subject:
            # EMail will use Subject
            return record.subject
        # SMS/Tweet will use 1st 80 characters from body
        text = record.message
        if len(text) < 80:
            return text
        else:
            return "%s..." % text[:76]

# =============================================================================
class S3CAPModel(S3Model):
    """
        CAP: Common Alerting Protocol
        - this module is a non-functional stub

        http://eden.sahanafoundation.org/wiki/BluePrint/Messaging#CAP
    """

    names = ["msg_report"]

    def model(self):

        T = current.T
        s3 = current.response.s3

        location_id = self.gis_location_id
        message_id = self.msg_message_id

        # CAP alert Status Code (status)
        cap_alert_status_code_opts = {
            "Actual":T("Actionable by all targeted recipients"),
            "Exercise":T("Actionable only by designated exercise participants; exercise identifier SHOULD appear in <note>"),
            "System":T("For messages that support alert network internal functions"),
            "Test":T("Technical testing only, all recipients disregard"),
            "Draft":T("preliminary template or draft, not actionable in its current form"),
        }
        # CAP info Event Category (category)
        cap_info_category_opts = {
            "Geo":T("Geophysical (inc. landslide)"),
            "Met":T("Meteorological (inc. flood)"),
            "Safety":T("General emergency and public safety"),
            "Security":T("Law enforcement, military, homeland and local/private security"),
            "Rescue":T("Rescue and recovery"),
            "Fire":T("Fire suppression and rescue"),
            "Health":T("Medical and public health"),
            "Env":T("Pollution and other environmental"),
            "Transport":T("Public and private transportation"),
            "Infra":T("Utility, telecommunication, other non-transport infrastructure"),
            "CBRNE":T("Chemical, Biological, Radiological, Nuclear or High-Yield Explosive threat or attack"),
            "Other":T("Other events"),
        }
        # CAP info Response Type (responseType)
        cap_info_responseType_opts = {
            "Shelter":T("Take shelter in place or per <instruction>"),
            "Evacuate":T("Relocate as instructed in the <instruction>"),
            "Prepare":T("Make preparations per the <instruction>"),
            "Execute":T("Execute a pre-planned activity identified in <instruction>"),
            "Avoid":T("Avoid the subject event as per the <instruction>"),
            "Monitor":T("Attend to information sources as described in <instruction>"),
            "Assess":T("Evaluate the information in this message.  (This value SHOULD NOT be used in public warning applications.)"),
            "AllClear":T("The subject event no longer poses a threat or concern and any follow on action is described in <instruction>"),
            "None":T("No action recommended"),
        }

        # Reports
        # Verified reports ready to be sent out as alerts or displayed on a map
        msg_report_type_opts = {
            "Shelter":T("Take shelter in place or per <instruction>"),
            "Evacuate":T("Relocate as instructed in the <instruction>"),
            "Prepare":T("Make preparations per the <instruction>"),
            "Execute":T("Execute a pre-planned activity identified in <instruction>"),
            "Avoid":T("Avoid the subject event as per the <instruction>"),
            "Monitor":T("Attend to information sources as described in <instruction>"),
            "Assess":T("Evaluate the information in this message.  (This value SHOULD NOT be used in public warning applications.)"),
            "AllClear":T("The subject event no longer poses a threat or concern and any follow on action is described in <instruction>"),
            "None":T("No action recommended"),
        }

        tablename = "msg_report"
        table = self.define_table(tablename,
                                  message_id(),
                                  location_id(),
                                  Field("image", "upload", autodelete = True),
                                  Field("url", requires=IS_NULL_OR(IS_URL())),
                                  *s3.meta_fields())

        # ---------------------------------------------------------------------
        # Pass variables back to global scope (response.s3.*)
        return Storage()

# =============================================================================
class S3EmailModel(S3Model):
    """
        Settings for Inbound Email

        Outbound Email is handled via deployment_settings
    """

    names = ["msg_email_settings",
            ]

    def model(self):

        # @ToDo: i18n labels
        #T = current.T
        s3 = current.response.s3

        # ---------------------------------------------------------------------
        tablename = "msg_email_settings"
        table = self.define_table(tablename,
                                  Field("inbound_mail_server"),
                                  Field("inbound_mail_type",
                                        requires = IS_IN_SET(["imap", "pop3"],
                                                             zero=None)),
                                  Field("inbound_mail_ssl", "boolean"),
                                  Field("inbound_mail_port", "integer"),
                                  Field("inbound_mail_username"),
                                  Field("inbound_mail_password"),
                                  Field("inbound_mail_delete", "boolean"),
                                  # Also needs to be used by Auth (order issues), DB calls are overheads
                                  # - as easy for admin to edit source in 000_config.py as to edit DB (although an admin panel can be nice)
                                  #Field("outbound_mail_server"),
                                  #Field("outbound_mail_from"),
                                  *s3.meta_fields())

        # ---------------------------------------------------------------------
        return Storage()

# =============================================================================
class S3SMSModel(S3Model):
    """
        SMS: Short Message Service

        These can be sent through a number of different gateways
        - modem
        - api
        - smtp
        - tropo
    """

    names = ["msg_setting",
             "msg_modem_settings",
             "msg_api_settings",
             "msg_smtp_to_sms_settings",
            ]

    def model(self):

        T = current.T
        s3 = current.response.s3
        msg = current.msg

        # ---------------------------------------------------------------------
        # Settings
        tablename = "msg_setting"
        table = self.define_table(tablename,
                                  Field("outgoing_sms_handler",
                                        length=32,
                                        requires = IS_IN_SET(msg.GATEWAY_OPTS,
                                                             zero=None)),
                                  # Moved to deployment_settings
                                  #Field("default_country_code", "integer",
                                  #      default=44),
                                  *s3.meta_fields())

        # ---------------------------------------------------------------------
        tablename = "msg_modem_settings"
        table = self.define_table(tablename,
                                  # Nametag to remember account - To be used later
                                  #Field("account_name"),
                                  Field("modem_port"),
                                  Field("modem_baud", "integer", default = 115200),
                                  Field("enabled", "boolean", default = True),
                                  # To be used later
                                  #Field("preference", "integer", default = 5),
                                  *s3.meta_fields())

        # ---------------------------------------------------------------------
        tablename = "msg_api_settings"
        table = self.define_table(tablename,
                                  Field("url",
                                        default = "https://api.clickatell.com/http/sendmsg"),
                                  Field("parameters",
                                        default="user=yourusername&password=yourpassword&api_id=yourapiid"),
                                  Field("message_variable", "string",
                                        default = "text"),
                                  Field("to_variable", "string",
                                        default = "to"),
                                  Field("enabled", "boolean", default = True),
                                  # To be used later
                                  #Field("preference", "integer", default = 5),
                                  *s3.meta_fields())

        # ---------------------------------------------------------------------
        tablename = "msg_smtp_to_sms_settings"
        table = self.define_table(tablename,
                                  # Nametag to remember account - To be used later
                                  #Field("account_name"),
                                  Field("address", length=64,
                                        requires=IS_NOT_EMPTY()),
                                  Field("subject", length=64),
                                  Field("enabled", "boolean", default = True),
                                  # To be used later
                                  #Field("preference", "integer", default = 5),
                                  *s3.meta_fields())

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
        db = current.db
        auth = current.auth
        s3 = current.response.s3

        person_id = self.pr_person_id

        # @ToDo: Use msg.CONTACT_OPTS
        msg_subscription_mode_opts = {
                                        1:T("Email"),
                                        #2:T("SMS"),
                                        #3:T("Email and SMS")
                                    }
        # @ToDo: Move this to being a component of the Saved Search
        #        (so that each search can have it's own subscription options)
        # @ToDo: Make Conditional
        # @ToDo: CRUD Strings
        tablename = "msg_subscription"
        table = self.define_table(tablename,
                                  Field("user_id","integer",
                                        default = auth.user_id,
                                        requires = IS_NOT_IN_DB(db, "msg_subscription.user_id"),
                                        readable = False,
                                        writable = False
                                        ),
                                  Field("subscribe_mode","integer",
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
                                  person_id(label = T("Person"),
                                            default = auth.s3_logged_in_person()),
                                  *s3.meta_fields())

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

    names = ["msg_tropo_settings",
             "msg_tropo_scratch",
            ]

    def model(self):

        #T = current.T
        s3 = current.response.s3

        # ---------------------------------------------------------------------
        tablename = "msg_tropo_settings"
        table = self.define_table(tablename,
                                  Field("token_messaging"),
                                  #Field("token_voice"),
                                  *s3.meta_fields())

        # ---------------------------------------------------------------------
        # Tropo Scratch pad for outbound messaging
        tablename = "msg_tropo_scratch"
        table = self.define_table(tablename,
                                  Field("row_id","integer"),
                                  Field("message_id","integer"),
                                  Field("recipient"),
                                  Field("message"),
                                  Field("network")
                                )

        # ---------------------------------------------------------------------
        return Storage()

# =============================================================================
class S3TwitterModel(S3Model):

    names = ["msg_twitter_settings",
             "msg_twitter_search",
             "msg_twitter_search_results"
            ]

    def model(self):

        T = current.T
        db = current.db
        s3 = current.response.s3

        # ---------------------------------------------------------------------
        tablename = "msg_twitter_settings"
        table = self.define_table(tablename,
                                  Field("pin"),
                                  Field("oauth_key",
                                        readable = False, writable = False),
                                  Field("oauth_secret",
                                        readable = False, writable = False),
                                  Field("twitter_account", writable = False),
                                  *s3.meta_fields())

        self.configure(tablename,
                       onvalidation=self.twitter_settings_onvalidation)

        # ---------------------------------------------------------------------
        # Twitter Search Queries
        tablename = "msg_twitter_search"
        table = self.define_table(tablename,
                                  Field("search_query", length = 140),
                                  *s3.meta_fields())

        # ---------------------------------------------------------------------
        tablename = "msg_twitter_search_results"
        table = self.define_table(tablename,
                                  Field("tweet", length=140),
                                  Field("posted_by"),
                                  Field("posted_at"),
                                  Field("twitter_search", db.msg_twitter_search),
                                  *s3.meta_fields())

        #table.twitter_search.requires = IS_ONE_OF(db, "twitter_search.search_query")
        #table.twitter_search.represent = lambda id: db(db.msg_twitter_search.id == id).select(db.msg_twitter_search.search_query,
                                                                                              #limitby = (0, 1)).first().search_query

        #self.add_component(table, msg_twitter_search="twitter_search")

        self.configure(tablename,
                       list_fields=[ "id",
                                     "tweet",
                                     "posted_by",
                                     "posted_at",
                                     "twitter_search",
                                    ])

        # ---------------------------------------------------------------------
        return Storage()

    # -------------------------------------------------------------------------
    @staticmethod
    def twitter_settings_onvalidation(form):
        """
            Complete oauth: take tokens from session + pin from form, and do the 2nd API call to Twitter
        """

        T = current.T
        session = current.session
        settings = current.deployment_settings
        s3 = session.s3
        vars = form.vars

        if vars.pin and s3.twitter_request_key and s3.twitter_request_secret:
            try:
                import tweepy
            except:
                raise HTTP(501, body=T("Can't import tweepy"))

            oauth = tweepy.OAuthHandler(settings.twitter.oauth_consumer_key,
                                        settings.twitter.oauth_consumer_secret)
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
        s3 = current.response.s3

        # ---------------------------------------------------------------------
        # SMS store for persistence and scratch pad for combining incoming xform chunks
        tablename = "msg_xforms_store"
        table = self.define_table(tablename,
                                  Field("sender", "string", length = 20),
                                  Field("fileno", "integer"),
                                  Field("totalno", "integer"),
                                  Field("partno", "integer"),
                                  Field("message", "string", length = 160)
                                )

        # ---------------------------------------------------------------------
        return Storage()

# END =========================================================================
