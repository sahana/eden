# -*- coding: utf-8 -*-

"""
    Messaging module
"""

module = "msg"
if deployment_settings.has_module(module):

    def messaging_tables():
        """ Load the tables required for Messaging, when-required"""

        person_id = s3db.pr_person_id
        location_id = s3db.gis_location_id

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
        table = db.define_table(tablename,
                                super_link("pe_id", "pr_pentity"),
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
                                *s3_meta_fields())

        s3mgr.configure(tablename,
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

        # Reusable Message ID
        message_id = S3ReusableField("message_id", db.msg_log,
                                     requires = IS_NULL_OR(IS_ONE_OF(db, "msg_log.id")),
                                     # FIXME: Subject works for Email but not SMS
                                     represent = lambda id: \
                                        db(db.msg_log.id == id).select(db.msg_log.subject,
                                                                       limitby=(0, 1)).first().subject,
                                     ondelete = "RESTRICT")

        # ---------------------------------------------------------------------
        # Message Limit - Used to limit the number of emails sent from the system
        tablename = "msg_limit"
        table = db.define_table(tablename,
                                s3_meta_created_on())

        # ---------------------------------------------------------------------
        # Message Tag - Used to tag a message to a resource
        tablename = "msg_tag"
        table = db.define_table(tablename,
                                message_id(),
                                Field("resource"),
                                Field("record_uuid", # null in this field implies subscription to the entire resource
                                      type=s3uuid,
                                      length=128),
                                *s3_meta_fields())

        s3mgr.configure(tablename,
                        list_fields=[ "id",
                                      "message_id",
                                      "record_uuid",
                                      "resource",
                                    ])

        # ---------------------------------------------------------------------
        # Settings
        # ---------------------------------------------------------------------
        tablename = "msg_email_settings"
        table = db.define_table(tablename,
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
                        *s3_timestamp())

        # ---------------------------------------------------------------------
        # SMS
        # ---------------------------------------------------------------------
        tablename = "msg_setting"
        table = db.define_table(tablename,
                                Field("outgoing_sms_handler",
                                      length=32,
                                      requires = IS_IN_SET(msg.GATEWAY_OPTS,
                                                           zero=None)),
                                # Moved to deployment_settings
                                #Field("default_country_code", "integer", default=44),
                                *s3_timestamp())

        # ---------------------------------------------------------------------
        tablename = "msg_modem_settings"
        table = db.define_table(tablename,
                                #Field("account_name"), # Nametag to remember account - To be used later
                                Field("modem_port"),
                                Field("modem_baud", "integer", default = 115200),
                                Field("enabled", "boolean", default = True),
                                #Field("preference", "integer", default = 5), To be used later
                                *s3_timestamp())

        # ---------------------------------------------------------------------
        tablename = "msg_api_settings"
        table = db.define_table(tablename,
                                Field("url",
                                      default = "https://api.clickatell.com/http/sendmsg"),
                                Field("parameters",
                                      default="user=yourusername&password=yourpassword&api_id=yourapiid"),
                                Field("message_variable", "string", default = "text"),
                                Field("to_variable", "string", default = "to"),
                                Field("enabled", "boolean", default = True),
                                #Field("preference", "integer", default = 5), To be used later
                                *s3_timestamp())

        # ---------------------------------------------------------------------
        tablename = "msg_smtp_to_sms_settings"
        table = db.define_table(tablename,
                                #Field("account_name"), # Nametag to remember account - To be used later
                                Field("address", length=64, requires=IS_NOT_EMPTY()),
                                Field("subject", length=64),
                                Field("enabled", "boolean", default = True),
                                #Field("preference", "integer", default = 5), To be used later
                                *s3_timestamp())

        # ---------------------------------------------------------------------
        tablename = "msg_tropo_settings"
        table = db.define_table(tablename,
                                Field("token_messaging"),
                                #Field("token_voice"),
                                *s3_timestamp())

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

        opt_msg_status = db.Table(None, "opt_msg_status",
                                  Field("status", "integer", notnull=True,
                                  requires = IS_IN_SET(msg_status_type_opts,
                                                       zero=None),
                                  default = 1,
                                  label = T("Status"),
                                  represent = lambda opt: \
                                    msg_status_type_opts.get(opt, UNKNOWN_OPT)))

        # Outbox - needs to be separate to Log since a single message sent needs different outbox entries for each recipient
        tablename = "msg_outbox"
        table = db.define_table(tablename,
                                message_id(),
                                super_link("pe_id", "pr_pentity"), # Person/Group to send the message out to
                                Field("address"),   # If set used instead of picking up from pe_id
                                Field("pr_message_method",
                                      length=32,
                                      requires = IS_IN_SET(msg_contact_method_opts,
                                                           zero=None),
                                      default = "EMAIL",
                                      label = T("Contact Method"),
                                      represent = lambda opt: \
                                        msg_contact_method_opts.get(opt, UNKNOWN_OPT)),
                                opt_msg_status,
                                Field("system_generated", "boolean", default = False),
                                Field("log"),
                                *s3_meta_fields())

        s3mgr.model.add_component(table, msg_log="message_id")

        s3mgr.configure(tablename,
                        list_fields=[ "id",
                                      "message_id",
                                      "pe_id",
                                      "status",
                                      "log",
                                    ])

        # ---------------------------------------------------------------------
        # Tropo Scratch pad for outbound messaging
        tablename = "msg_tropo_scratch"
        table = db.define_table(tablename,
                                Field("row_id","integer"),
                                Field("message_id","integer"),
                                Field("recipient"),
                                Field("message"),
                                Field("network"),
                                )

        # ---------------------------------------------------------------------
        # Inbound Messages
        # ---------------------------------------------------------------------
        # Channel - For inbound messages this tells which channel the message came in from.
        tablename = "msg_channel"
        table = db.define_table(tablename,
                                message_id(),
                                Field("pr_message_method",
                                      length=32,
                                      requires = IS_IN_SET(msg_contact_method_opts,
                                                           zero=None),
                                      default = "EMAIL"),
                                Field("log"),
                                *s3_meta_fields())

        # ---------------------------------------------------------------------
        # Status
        #tablename = "msg_email_inbound_status"
        #table = db.define_table(tablename,
        #                        Field("status"),
        #                        )

        # ---------------------------------------------------------------------
        # SMS store for persistence and scratch pad for combining incoming xform chunks
        tablename = "msg_xforms_store"
        table = db.define_table(tablename,
                                Field("sender", "string", length = 20),
                                Field("fileno", "integer"),
                                Field("totalno", "integer"),
                                Field("partno", "integer"),
                                Field("message", "string", length = 160),
                                )

        # =====================================================================
        def msg_compose(title_name = "Send Message",
                        type = None,
                        recipient_type = None,
                        recipient = None,
                        message = "",
                        redirect_module = "msg",
                        redirect_function = "compose",
                        redirect_args = None,
                        redirect_vars = None,
                       ):
            """
                Form to Compose a Message

                @param title_name: Title of the page
                @param type: The default message type: None, EMAIL, SMS or TWITTER
                @param recipient_type: Send to Persons or Groups? (pr_person or pr_group)
                @param recipient: The pe_id of the person/group to send the message to (Not hiding UI yet)
                @param message: The default message text
                @param redirect_module: Redirect to the specified module's url after login.
                @param redirect_function: Redirect to the specified function
                @param redirect_args:  List of args to include in redirects
                @param redirect_vars:  Dict of vars to include in redirects
            """

            ltable = db.msg_log
            otable = db.msg_outbox

            url = URL(redirect_module,
                      redirect_function,
                      args=redirect_args,
                      vars=redirect_vars)

            if auth.is_logged_in() or auth.basic():
                pass
            else:
                redirect(URL(c="default", f="user", args="login",
                             vars={"_next" : url}))

            ltable.message.default = message

            if type:
                otable.pr_message_method.default = type

            ltable.pe_id.writable = ltable.pe_id.readable = False
            ltable.sender.writable = ltable.sender.readable = False
            ltable.fromaddress.writable = ltable.fromaddress.readable = False
            ltable.verified.writable = ltable.verified.readable = False
            ltable.verified_comments.writable = ltable.verified_comments.readable = False
            ltable.actioned.writable = ltable.actioned.readable = False
            ltable.actionable.writable = ltable.actionable.readable = False
            ltable.actioned_comments.writable = ltable.actioned_comments.readable = False

            ltable.subject.label = T("Subject")
            ltable.message.label = T("Message")
            #ltable.priority.label = T("Priority")

            if recipient:
                ltable.pe_id.default = recipient
                otable.pe_id.writable = True
                otable.pe_id.default = recipient
                otable.pe_id.requires = IS_ONE_OF_EMPTY(db, "pr_pentity.pe_id")
            else:
                if recipient_type:
                    # Filter by Recipient Type
                    otable.pe_id.requires = IS_ONE_OF(db, "pr_pentity.pe_id",
                                                      orderby="instance_type",
                                                      filterby="instance_type",
                                                      filter_opts=(recipient_type,))
                otable.pe_id.writable = otable.pe_id.readable = True
                otable.pe_id.label = T("Recipients")
                otable.pe_id.comment = DIV(_class="tooltip",
                                           _title="%s|%s" % (T("Recipients"),
                                                             T("Please enter the first few letters of the Person/Group for the autocomplete.")))

            def compose_onvalidation(form):
                """ Set the sender and use msg.send_by_pe_id to route the message """
                vars = request.post_vars
                if not vars.pe_id:
                    session.error = T("Please enter the recipient")
                    redirect(url)
                table = db.pr_person
                query = (table.uuid == auth.user.person_uuid)
                sender_pe_id = db(query).select(table.pe_id,
                                                limitby=(0, 1)).first().pe_id
                if msg.send_by_pe_id(vars.pe_id,
                                     vars.subject,
                                     vars.message,
                                     sender_pe_id,
                                     vars.pr_message_method):
                    # Trigger a Process Outbox
                    msg.process_outbox(contact_method = vars.pr_message_method)
                    session.flash = T("Check outbox for the message status")
                    redirect(url)
                else:
                    session.error = T("Error in message")
                    redirect(URL(url))

            logform = crud.create(ltable,
                                  onvalidation = compose_onvalidation)
            outboxform = crud.create(otable)

            if recipient_type:
                response.s3.js_global.append("S3.msg_search_url = '%s';" % URL(c="msg", f="search", vars={"type":recipient_type}))
            else:
                response.s3.js_global.append("S3.msg_search_url = '%s';" % URL(c="msg", f="search"))
            if recipient:
                response.s3.jquery_ready.append("""
$('#msg_outbox_pe_id__row').hide();""")
            else:
                response.s3.jquery_ready.append("""
// Hide the real Input Field
$('#msg_outbox_pe_id').hide();
// Autocomplete-enable the Dummy Input
$('#dummy').autocomplete({
    source: S3.msg_search_url,
    minLength: 2,
    focus: function( event, ui ) {
        $( '#dummy' ).val( ui.item.name );
        return false;
    },
    select: function( event, ui ) {
        $( '#dummy_input' ).val( ui.item.name );
        $( '#msg_outbox_pe_id' ).val( ui.item.id );
        return false;
    }
})
.data( 'autocomplete' )._renderItem = function( ul, item ) {
    return $( '<li></li>' )
        .data( 'item.autocomplete', item )
        .append( '<a>' + item.name + '</a>' )
        .appendTo( ul );
};""")
            response.s3.jquery_ready.append("""
if ($('#msg_outbox_pr_message_method').val() != 'EMAIL') {
    // SMS/Tweets don't have subjects
    $('#msg_log_subject__row').hide();
}
$('#msg_outbox_pr_message_method').change(function() {
    if ($(this).val() == 'EMAIL') {
        // Emails have a Subject
        $('#msg_log_subject__row').show();
    } else {
        $('#msg_log_subject__row').hide();
    }
});""")

            return dict(logform = logform,
                        outboxform = outboxform,
                        title = T(title_name))

        # ---------------------------------------------------------------------
        # Twitter
        # ---------------------------------------------------------------------
        tablename = "msg_twitter_settings"
        table = db.define_table(tablename,
                                Field("pin"),
                                Field("oauth_key",
                                      readable = False, writable = False),
                                Field("oauth_secret",
                                      readable = False, writable = False),
                                Field("twitter_account", writable = False),
                                *s3_timestamp())

        def twitter_settings_onvalidation(form):
            """ Complete oauth: take tokens from session + pin from form, and do the 2nd API call to Twitter """
            if form.vars.pin and session.s3.twitter_request_key and session.s3.twitter_request_secret:
                try:
                    import tweepy
                except:
                    raise HTTP(501, body=T("Can't import tweepy"))

                oauth = tweepy.OAuthHandler(deployment_settings.twitter.oauth_consumer_key,
                                            deployment_settings.twitter.oauth_consumer_secret)
                oauth.set_request_token(session.s3.twitter_request_key, session.s3.twitter_request_secret)
                try:
                    oauth.get_access_token(form.vars.pin)
                    form.vars.oauth_key = oauth.access_token.key
                    form.vars.oauth_secret = oauth.access_token.secret
                    twitter = tweepy.API(oauth)
                    form.vars.twitter_account = twitter.me().screen_name
                    form.vars.pin = "" # we won't need it anymore
                    return
                except tweepy.TweepError:
                    session.error = T("Settings were reset because authenticating with Twitter failed")
            # Either user asked to reset, or error - clear everything
            for k in ["oauth_key", "oauth_secret", "twitter_account"]:
                form.vars[k] = None
            for k in ["twitter_request_key", "twitter_request_secret"]:
                session.s3[k] = ""

        s3mgr.configure(tablename,
                        onvalidation=twitter_settings_onvalidation)

        # ---------------------------------------------------------------------
        # Twitter Search Queries
        tablename = "msg_twitter_search"
        table = db.define_table(tablename,
                                Field("search_query", length = 140),
                                )
        # ---------------------------------------------------------------------
        resourcename = "twitter_search_results"
        tablename = "msg_twitter_search_results"
        table = db.define_table(tablename,
                                Field("tweet", length=140),
                                Field("posted_by"),
                                Field("posted_at"),
                                Field("twitter_search", db.msg_twitter_search),
                                )
        #table.twitter_search.requires = IS_ONE_OF(db, "twitter_search.search_query")
        #table.twitter_search.represent = lambda id: db(db.msg_twitter_search.id == id).select(db.msg_twitter_search.search_query, limitby = (0,1)).first().search_query

        s3mgr.model.add_component(table, msg_twitter_search="twitter_search")

        s3mgr.configure(tablename,
                        list_fields=[ "id",
                                      "tweet",
                                      "posted_by",
                                      "posted_at",
                                      "twitter_search",
                                    ])

        # ---------------------------------------------------------------------
        # Pass variables back to global scope (response.s3.*)
        return dict(msg_compose=msg_compose,
                    message_id=message_id)

    # Provide a handle to this load function
    s3mgr.loader(messaging_tables,
                 "msg_setting",
                 "msg_email_settings",
                 "msg_modem_settings",
                 "msg_smtp_to_sms_settings",
                 "msg_tropo_settings",
                 "msg_twitter_settings",
                 "msg_log",
                 "msg_limit",
                 "msg_tag",
                 "msg_channel",
                 "msg_outbox")

    # =========================================================================
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
    table = db.define_table(tablename,
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
                                      default = s3_logged_in_person()),
                            *s3_timestamp())

    s3mgr.configure("msg_subscription",
                    list_fields=["subscribe_mode",
                                 "subscription_frequency"])
    s3mgr.model.add_component("msg_subscription", pr_person="person_id")

    # =========================================================================
    # CAP: Common Alerting Protocol
    # http://docs.oasis-open.org/emergency/cap/v1.2/CAP-v1.2.html
    def cap_tables():
        """ Load the tables required for CAP, when-required"""

        s3mgr.load("msg_log")
        message_id = response.s3.message_id

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
        table = db.define_table(tablename,
                                message_id(),
                                location_id(),
                                Field("image", "upload", autodelete = True),
                                Field("url", requires=IS_NULL_OR(IS_URL())),
                                *s3_meta_fields())
        # Pass variables back to global scope (response.s3.*)
        return dict()

    # Provide a handle to this load function
    s3mgr.loader(cap_tables,
                 "msg_report")

    # =============================================================================
    # Tasks to be callable async
    # =============================================================================
    def process_outbox(contact_method, user_id=None):
        """
            Process Outbox
                - will normally be done Asynchronously if there is a worker alive

            @param contact_method: s3msg.MSG_CONTACT_OPTS
            @param user_id: calling request's auth.user.id or None
        """
        if user_id:
            # Authenticate
            auth.s3_impersonate(user_id)
        # Run the Task
        result = msg.process_outbox(contact_method)
        return result

    tasks["process_outbox"] = process_outbox

# END =========================================================================
