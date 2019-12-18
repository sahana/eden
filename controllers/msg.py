# -*- coding: utf-8 -*-

"""
    Messaging Module - Controllers
"""

module = request.controller
resourcename = request.function

if not settings.has_module(module):
    raise HTTP(404, body="Module disabled: %s" % module)

# -----------------------------------------------------------------------------
def index():
    """ Module's Home Page """

    module_name = settings.modules[module].name_nice
    response.title = module_name
    return {"module_name": module_name,
            }

# -----------------------------------------------------------------------------
def basestation():
    """ RESTful CRUD controller for Base Stations """

    return s3_rest_controller()

# =============================================================================
def compose():
    """ Compose a Message which can be sent to a pentity via a number of different communications channels """

    return msg.compose()

# =============================================================================
def message():
    """
        RESTful CRUD controller for the master message log
    """

    tablename = "msg_message"
    table = s3db.msg_message

    table.instance_type.readable = True
    table.instance_type.label = T("Channel")

    # CRUD Strings
    s3.crud_strings[tablename] = Storage(
        title_display = T("Message Details"),
        title_list = T("Message Log"),
        label_list_button = T("View Message Log"),
        msg_list_empty = T("No Messages currently in the Message Log"),
        )

    def postp(r, output):
        if r.interactive:
            # Normal Action Buttons
            s3_action_buttons(r)
            # Custom Action Buttons
            s3.actions += [{"label": s3_str(T("Mark Sender")),
                            "url": URL(f = "mark_sender",
                                       args = ["[id]"],
                                       ),
                            "_class": "action-btn",
                            },
                           ]

        return output
    s3.postp = postp

    s3db.configure(tablename,
                   deletable = False,
                   editable = False,
                   insertable = False,
                   )

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def contact():
    """
        RESTful CRUD controller for the Contact Form
    """

    def prep(r):
        if not auth.s3_has_role("ADMIN"):
            r.method = "create"
        return True
    s3.prep = prep

    return s3_rest_controller()

# =============================================================================
def mark_sender():
    """
        Assign priority to the given sender
    """

    try:
        mid = request.args[0]
    except:
        raise SyntaxError

    mtable = s3db.msg_message
    stable = s3db.msg_sender

    # @ToDo: Replace 2 queries with Join
    srecord = db(mtable.id == mid).select(mtable.from_address,
                                          limitby=(0, 1)
                                          ).first()
    sender = srecord.from_address
    record = db(stable.sender == sender).select(stable.id,
                                                limitby=(0, 1)
                                                ).first()

    if record:
        args = "update"
    else:
        args = "create"

    url = URL(f="sender", args=args, vars={"sender": sender})
    redirect(url)

# =============================================================================
def outbox():
    """ View the contents of the Outbox """

    if not auth.s3_logged_in():
        session.error = T("Requires Login!")
        redirect(URL(c="default", f="user", args="login"))

    tablename = "msg_outbox"
    table = s3db[tablename]

    table.message_id.label = T("Message")
    table.message_id.writable = False
    table.message_id.readable = True

    table.pe_id.readable = True
    table.pe_id.label = T("Recipient")

    table.message_id.represent = s3db.msg_message_represent
    table.pe_id.represent = s3db.pr_PersonEntityRepresent(default_label="")

    # CRUD Strings
    s3.crud_strings[tablename] = Storage(
        title_display = T("Message Details"),
        title_list = T("Outbox"),
        label_list_button = T("View Outbox"),
        label_delete_button = T("Delete Message"),
        msg_record_deleted = T("Message deleted"),
        msg_list_empty = T("No Messages currently in Outbox")
    )

    def postp(r, output):
        if isinstance(output, dict):
            add_btn = A(T("Compose"),
                        _class="action-btn",
                        _href=URL(f="compose")
                        )
            output["rheader"] = add_btn

        return output
    s3.postp = postp

    s3db.configure(tablename,
                   # Permissions-based
                   #deletable = False,
                   editable = False,
                   insertable = False,
                   )

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def email_outbox():
    """
        RESTful CRUD controller for the Email Outbox
        - all Outbound Email Messages are visible here
    """

    if not auth.s3_logged_in():
        session.error = T("Requires Login!")
        redirect(URL(c="default", f="user", args="login"))

    tablename = "msg_email"
    table = s3db.msg_email
    s3.filter = (table.inbound == False)
    table.inbound.readable = False

    # CRUD Strings
    s3.crud_strings[tablename] = Storage(
        title_display = T("Email Details"),
        title_list = T("Sent Emails"),
        label_list_button = T("View Sent Emails"),
        label_delete_button = T("Delete Email"),
        msg_record_deleted = T("Email deleted"),
        msg_list_empty = T("No Emails currently in Outbox")
    )

    def postp(r, output):
        if isinstance(output, dict):
            add_btn = A(T("Compose"),
                        _class="action-btn",
                        _href=URL(f="compose")
                        )
            output["rheader"] = add_btn

        return output
    s3.postp = postp

    s3db.configure(tablename,
                   # Permissions-based
                   #deletable = False,
                   editable = False,
                   insertable = False,
                   listadd = False,
                   list_fields = ["id",
                                  "date",
                                  "to_address",
                                  "subject",
                                  "body",
                                  ],
                   )

    return s3_rest_controller(module, "email")

# -----------------------------------------------------------------------------
def facebook_outbox():
    """
        RESTful CRUD controller for the Facebook Outbox
        - all Outbound Facebook Messages are visible here
    """

    if not auth.s3_logged_in():
        session.error = T("Requires Login!")
        redirect(URL(c="default", f="user", args="login"))

    tablename = "msg_facebook"
    table = s3db.msg_facebook
    s3.filter = (table.inbound == False)
    table.inbound.readable = False

    # CRUD Strings
    s3.crud_strings[tablename] = Storage(
        title_display = T("Post Details"),
        title_list = T("Sent Posts"),
        label_list_button = T("View Sent Posts"),
        label_delete_button = T("Delete Post"),
        msg_record_deleted = T("Post deleted"),
        msg_list_empty = T("No Posts currently in Outbox")
    )

    #def postp(r, output):
    #    if isinstance(output, dict):
    #        add_btn = A(T("Compose"),
    #                    _class="action-btn",
    #                    _href=URL(f="compose")
    #                    )
    #        output["rheader"] = add_btn
    #    return output
    #s3.postp = postp

    s3db.configure(tablename,
                   # Permissions-based
                   #deletable = False,
                   editable = False,
                   insertable = False,
                   listadd = False,
                   list_fields = ["id",
                                  "date",
                                  #"to_address",
                                  "body",
                                  ],
                   )

    return s3_rest_controller(module, "facebook")

# -----------------------------------------------------------------------------
def sms_outbox():
    """
        RESTful CRUD controller for the SMS Outbox
        - all sent SMS are visible here
    """

    if not auth.s3_logged_in():
        session.error = T("Requires Login!")
        redirect(URL(c="default", f="user", args="login"))

    tablename = "msg_sms"
    table = s3db.msg_sms
    s3.filter = (table.inbound == False)
    table.inbound.readable = False

    # CRUD Strings
    s3.crud_strings[tablename] = Storage(
        title_display = T("SMS Details"),
        title_list = T("Sent SMS"),
        label_list_button = T("View Sent SMS"),
        label_delete_button = T("Delete SMS"),
        msg_record_deleted = T("SMS deleted"),
        msg_list_empty = T("No SMS currently in Outbox")
    )

    def postp(r, output):
        if isinstance(output, dict):
            add_btn = A(T("Compose"),
                        _class="action-btn",
                        _href=URL(f="compose")
                        )
            output["rheader"] = add_btn

        return output
    s3.postp = postp

    s3db.configure(tablename,
                   # Permissions-based
                   #deletable = False,
                   editable = False,
                   insertable = False,
                   listadd = False,
                   list_fields = ["id",
                                  "date",
                                  "to_address",
                                  "body",
                                  ],
                   )

    return s3_rest_controller(module, "sms")

# -----------------------------------------------------------------------------
def twitter_outbox():
    """
        RESTful CRUD controller for the Twitter Outbox
        - all sent Tweets are visible here
    """

    if not auth.s3_logged_in():
        session.error = T("Requires Login!")
        redirect(URL(c="default", f="user", args="login"))

    tablename = "msg_twitter"
    table = s3db.msg_twitter
    s3.filter = (table.inbound == False)
    table.inbound.readable = False

    # CRUD Strings
    s3.crud_strings[tablename] = Storage(
        title_display = T("Tweet Details"),
        title_list = T("Sent Tweets"),
        label_list_button = T("View Sent Tweets"),
        label_delete_button = T("Delete Tweet"),
        msg_record_deleted = T("Tweet deleted"),
        msg_list_empty = T("No Tweets currently in Outbox")
    )

    def postp(r, output):
        if isinstance(output, dict):
            add_btn = A(T("Compose"),
                        _class="action-btn",
                        _href=URL(f="compose")
                        )
            output["rheader"] = add_btn

        return output
    s3.postp = postp

    s3db.configure(tablename,
                   # Permissions-based
                   #deletable = False,
                   editable = False,
                   insertable = False,
                   listadd = False,
                   list_fields = ["id",
                                  "date",
                                  "to_address",
                                  "body",
                                  ],
                   )

    return s3_rest_controller(module, "twitter")

# =============================================================================
def inbox():
    """
        RESTful CRUD controller for the Inbox
        - all Inbound Messages are visible here
    """

    if not auth.s3_logged_in():
        session.error = T("Requires Login!")
        redirect(URL(c="default", f="user", args="login"))

    table = s3db.msg_message
    s3.filter = (table.inbound == True)
    table.inbound.readable = False

    tablename = "msg_message"
    # CRUD Strings
    s3.crud_strings[tablename] = Storage(
        title_display = T("Message Details"),
        title_list = T("InBox"),
        label_list_button = T("View InBox"),
        label_delete_button = T("Delete Message"),
        msg_record_deleted = T("Message deleted"),
        msg_list_empty = T("No Messages currently in InBox")
    )

    s3db.configure(tablename,
                   # Permissions-based
                   #deletable = False,
                   editable = False,
                   insertable = False,
                   list_fields = ["id",
                                  "date",
                                  "channel_id",
                                  "from_address",
                                  "body",
                                  ],
                   )

    return s3_rest_controller(module, "message")

# -----------------------------------------------------------------------------
def email_inbox():
    """
        RESTful CRUD controller for the Email Inbox
        - all Inbound Email Messages are visible here
    """

    if not auth.s3_logged_in():
        session.error = T("Requires Login!")
        redirect(URL(c="default", f="user", args="login"))

    s3.filter = (FS("inbound") == True)

    from s3 import S3SQLCustomForm, S3SQLInlineComponent
    crud_form = S3SQLCustomForm("date",
                                "subject",
                                "from_address",
                                "body",
                                S3SQLInlineComponent(
                                    "attachment",
                                    name = "document_id",
                                    label = T("Attachments"),
                                    fields = ["document_id",],
                                    ),
                                )

    tablename = "msg_email"

    # CRUD Strings
    s3.crud_strings[tablename] = Storage(
        title_display = T("Email Details"),
        title_list = T("Email InBox"),
        label_list_button = T("View Email InBox"),
        label_delete_button = T("Delete Email"),
        msg_record_deleted = T("Email deleted"),
        msg_list_empty = T("No Emails currently in InBox")
    )

    s3db.configure(tablename,
                   crud_form = crud_form,
                   # Permissions-based
                   #deletable = False,
                   editable = False,
                   insertable = False,
                   list_fields = ["id",
                                  "date",
                                  "from_address",
                                  "subject",
                                  "body",
                                  (T("Attachments"), "attachment.document_id"),
                                  ],
                   )

    def prep(r):
        s3db.msg_email.inbound.readable = False
        if r.id:
            s3db.msg_attachment.document_id.label = ""
        return True
    s3.prep = prep

    return s3_rest_controller(module, "email")

# =============================================================================
def rss():
    """
       RESTful CRUD controller for RSS feed posts
    """

    if not auth.s3_has_role("ADMIN"):
        auth.permission.fail()

    tablename = "msg_rss"
    table = s3db.msg_rss

    # To represent the description suitably
    # If it is an image display an image
    #table.description.represent = lambda description:  HTML(description)

    # CRUD Strings
    s3.crud_strings[tablename] = Storage(
        title_display = T("RSS Post Details"),
        title_list = T("RSS Posts"),
        label_list_button = T("View RSS Posts"),
        label_delete_button = T("Delete Post"),
        msg_record_deleted = T("RSS Post deleted"),
        msg_list_empty = T("No Posts available")
        )

    s3db.configure(tablename,
                   # Permissions-based
                   #deletable = False,
                   editable = False,
                   insertable = False,
                   list_fields = ["id",
                                  "date",
                                  "body",
                                  ],
                   )

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def sms_inbox():
    """
        RESTful CRUD controller for the SMS Inbox
        - all Inbound SMS Messages go here
    """

    if not auth.s3_logged_in():
        session.error = T("Requires Login!")
        redirect(URL(c="default", f="user", args="login"))

    tablename = "msg_sms"
    table = s3db[tablename]
    s3.filter = (table.inbound == True)
    table.inbound.readable = False

    # CRUD Strings
    s3.crud_strings[tablename] = Storage(
        title_display = T("SMS Details"),
        title_list = T("SMS InBox"),
        label_list_button = T("View SMS InBox"),
        label_delete_button = T("Delete SMS"),
        msg_record_deleted = T("SMS deleted"),
        msg_list_empty = T("No SMS currently in InBox")
    )

    s3db.configure(tablename,
                   # Permissions-based
                   #deletable = False,
                   editable = False,
                   insertable = False,
                   list_fields = ["id",
                                  "date",
                                  "from_address",
                                  "body",
                                  ],
                   )

    return s3_rest_controller(module, "sms")

# -----------------------------------------------------------------------------
def twitter():
    """
        Twitter RESTful Controller

        @ToDo: Action Button to update async
    """

    s3db.configure("msg_twitter",
                   editable = False,
                   insertable = False,
                   list_fields = ["id",
                                  "date",
                                  "from_address",
                                  "to_address",
                                  "body",
                                  ],
                   )

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def twitter_inbox():
    """
        RESTful CRUD controller for the Twitter Inbox
        - all Inbound Tweets (Directed Messages) are visible here
    """

    if not auth.s3_logged_in():
        session.error = T("Requires Login!")
        redirect(URL(c="default", f="user", args="login"))

    tablename = "msg_twitter"
    table = s3db.msg_twitter
    s3.filter = (table.inbound == True)
    table.inbound.readable = False

    # CRUD Strings
    s3.crud_strings[tablename] = Storage(
        title_display = T("Tweet Details"),
        title_list = T("Twitter InBox"),
        label_list_button = T("View Twitter InBox"),
        label_delete_button = T("Delete Tweet"),
        msg_record_deleted = T("Tweet deleted"),
        msg_list_empty = T("No Tweets currently in InBox")
    )

    s3db.configure(tablename,
                   editable = False,
                   insertable = False,
                   list_fields = ["id",
                                  "date",
                                  "from_address",
                                  "body",
                                  ],
                   )

    return s3_rest_controller(module, "twitter")

# =============================================================================
def tropo():
    """
        Receive a JSON POST from the Tropo WebAPI

        @see: https://www.tropo.com/docs/webapi/newhowitworks.htm
    """

    # Stored in modules/tropo.py
    from tropo import Tropo, Session

    try:
        s = Session(request.body.read())
        t = Tropo()
        # This is their service contacting us, so parse their request
        try:
            row_id = s.parameters["row_id"]
            # This is an Outbound message which we've requested Tropo to send for us
            table = s3db.msg_tropo_scratch
            query = (table.row_id == row_id)
            row = db(query).select().first()
            # Send the message
            #t.message(say_obj={"say":{"value":row.message}},to=row.recipient,network=row.network)
            t.call(to=row.recipient, network=row.network)
            t.say(row.message)
            # Update status to sent in Outbox
            outbox = s3db.msg_outbox
            db(outbox.id == row.row_id).update(status=2)
            # @ToDo: Set message log to actioned
            #log = s3db.msg_log
            #db(log.id == row.message_id).update(actioned=True)
            # Clear the Scratchpad
            db(query).delete()
            return t.RenderJson()
        except:
            # This is an Inbound message
            try:
                message = s.initialText
                # This is an SMS/IM
                # Place it in the InBox
                uuid = s.id
                recipient = s.to["id"]
                try:
                    fromaddress = s.fromaddress["id"]
                except:
                    # SyntaxError: s.from => invalid syntax (why!?)
                    fromaddress = ""
                # @ToDo: Update to new model
                #s3db.msg_log.insert(uuid=uuid, fromaddress=fromaddress,
                #                    recipient=recipient, message=message,
                #                    inbound=True)
                # Send the message to the parser
                reply = msg.parse_message(message)
                t.say([reply])
                return t.RenderJson()
            except:
                # This is a Voice call
                # - we can't handle these yet
                raise HTTP(501)
    except:
        # GET request or some random POST
        pass

# =============================================================================
@auth.s3_requires_membership(1)
def sms_outbound_gateway():
    """ SMS Outbound Gateway selection for the messaging framework """

    # CRUD Strings
    s3.crud_strings["msg_sms_outbound_gateway"] = Storage(
        label_create = T("Create SMS Outbound Gateway"),
        title_display = T("SMS Outbound Gateway Details"),
        title_list = T("SMS Outbound Gateways"),
        title_update = T("Edit SMS Outbound Gateway"),
        label_list_button = T("List SMS Outbound Gateways"),
        label_delete_button = T("Delete SMS Outbound Gateway"),
        msg_record_created = T("SMS Outbound Gateway added"),
        msg_record_modified = T("SMS Outbound Gateway updated"),
        msg_record_deleted = T("SMS Outbound Gateway deleted"),
        msg_list_empty = T("No SMS Outbound Gateways currently registered"))

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def channel():
    """
        RESTful CRUD controller for Channels
        - unused
    """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def email_channel():
    """
        RESTful CRUD controller for Inbound Email channels
            - appears in the administration menu
    """

    if not auth.s3_has_role("ADMIN"):
        auth.permission.fail()

    tablename = "msg_email_channel"
    table = s3db[tablename]

    table.server.label = T("Server")
    table.protocol.label = T("Protocol")
    table.use_ssl.label = "SSL"
    table.port.label = T("Port")
    table.username.label = T("Username")
    table.password.label = T("Password")
    table.delete_from_server.label = T("Delete from Server?")
    table.port.comment = DIV(_class="tooltip",
                             _title="%s|%s" % (T("Port"),
                                               T("For POP-3 this is usually 110 (995 for SSL), for IMAP this is usually 143 (993 for IMAP).")))
    table.delete_from_server.comment = DIV(_class="tooltip",
                                           _title="%s|%s" % (T("Delete"),
                                                             T("If this is set to True then mails will be deleted from the server after downloading.")))

    # CRUD Strings
    s3.crud_strings[tablename] = Storage(
        title_display = T("Email Settings"),
        title_list = T("Email Accounts"),
        label_create = T("Create Email Account"),
        title_update = T("Edit Email Settings"),
        label_list_button = T("View Email Accounts"),
        msg_record_created = T("Account added"),
        msg_record_deleted = T("Email Account deleted"),
        msg_list_empty = T("No Accounts currently defined"),
        msg_record_modified = T("Email Settings updated")
        )

    def postp(r, output):
        if r.interactive:
            # Normal Action Buttons
            s3_action_buttons(r)
            # Custom Action Buttons for Enable/Disable
            table = r.table
            query = (table.deleted == False)
            rows = db(query).select(table.id,
                                    table.enabled,
                                    )
            restrict_e = [str(row.id) for row in rows if not row.enabled]
            restrict_d = [str(row.id) for row in rows if row.enabled]

            s3.actions += [{"label": s3_str(T("Enable")),
                            "_class": "action-btn",
                            "url": URL(args=["[id]", "enable"]),
                            "restrict": restrict_e,
                            },
                           {"label": s3_str(T("Disable")),
                            "_class": "action-btn",
                            "url": URL(args = ["[id]", "disable"]),
                            "restrict": restrict_d,
                            },
                           ]
            if not s3task._is_alive():
                # No Scheduler Running
                s3.actions += [{"label": s3_str(T("Poll")),
                                "_class": "action-btn",
                                "url": URL(args = ["[id]", "poll"]),
                                "restrict": restrict_d,
                                },
                               ]
        return output
    s3.postp = postp

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def facebook_channel():
    """
        RESTful CRUD controller for Facebook channels
            - appears in the administration menu
    """

    if not auth.s3_has_role("ADMIN"):
        auth.permission.fail()

    tablename = "msg_facebook_channel"
    table = s3db[tablename]

    # CRUD Strings
    s3.crud_strings[tablename] = Storage(
        title_display = T("Facebook Settings"),
        title_list = T("Facebook Accounts"),
        label_create = T("Add Facebook Account"),
        title_update = T("Edit Facebook Settings"),
        label_list_button = T("View Facebook Accounts"),
        msg_record_created = T("Account added"),
        msg_record_deleted = T("Facebook Account deleted"),
        msg_list_empty = T("No Accounts currently defined"),
        msg_record_modified = T("Facebook Settings updated")
        )

    def postp(r, output):
        if r.interactive:
            # Normal Action Buttons
            s3_action_buttons(r)
            # Custom Action Buttons for Enable/Disable
            table = r.table
            query = (table.deleted == False)
            rows = db(query).select(table.id,
                                    table.enabled,
                                    )
            restrict_e = [str(row.id) for row in rows if not row.enabled]
            restrict_d = [str(row.id) for row in rows if row.enabled]

            s3.actions += [{"label": s3_str(T("Enable")),
                            "_class": "action-btn",
                            "url": URL(args=["[id]", "enable"]),
                            "restrict": restrict_e,
                            },
                           {"label": s3_str(T("Disable")),
                            "_class": "action-btn",
                            "url": URL(args = ["[id]", "disable"]),
                            "restrict": restrict_d,
                            },
                           ]
            #if not s3task._is_alive():
            #    # No Scheduler Running
            #    s3.actions += [{"label": s3_str(T("Poll")),
            #                    "_class": "action-btn",
            #                    "url": URL(args = ["[id]", "poll"]),
            #                    "restrict": restrict_d),
            #                    }
            #                   ]
        return output
    s3.postp = postp

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def mcommons_channel():
    """
        RESTful CRUD controller for Mobile Commons SMS Channels
            - appears in the administration menu
    """

    if not auth.s3_has_role("ADMIN"):
        auth.permission.fail()

    tablename = "msg_mcommons_channel"
    table = s3db[tablename]

    table.name.label = T("Account Name")
    table.name.comment = DIV(_class="tooltip",
                             _title="%s|%s" % (T("Account Name"),
                                               T("Name for your Mobile Commons Account")))

    table.campaign_id.label = T("Campaign ID")

    table.url.label = T("URL")
    table.url.comment = DIV(_class="tooltip",
                            _title="%s|%s" % (T("URL"),
                                              T("URL for the Mobile Commons API")))

    table.username.label = T("Username")
    table.password.label = T("Password")
    table.timestmp.label = T("Last Downloaded")
    table.timestmp.writable = False

    # CRUD Strings
    s3.crud_strings[tablename] = Storage(
        title_display = T("Mobile Commons Setting Details"),
        title_list = T("Mobile Commons Settings"),
        label_create = T("Add Mobile Commons Settings"),
        title_update = T("Edit Mobile Commons Settings"),
        label_list_button = T("View Mobile Commons Settings"),
        msg_record_created = T("Mobile Commons Setting added"),
        msg_record_deleted = T("Mobile Commons Setting deleted"),
        msg_list_empty = T("No Mobile Commons Settings currently defined"),
        msg_record_modified = T("Mobile Commons settings updated")
        )

    def postp(r, output):
        if r.interactive:
            # Normal Action Buttons
            s3_action_buttons(r)
            # Custom Action Buttons for Enable/Disable
            table = r.table
            query = (table.deleted == False)
            rows = db(query).select(table.id,
                                    table.enabled,
                                    )
            restrict_e = [str(row.id) for row in rows if not row.enabled]
            restrict_d = [str(row.id) for row in rows if row.enabled]

            s3.actions += [{"label": s3_str(T("Enable")),
                            "_class": "action-btn",
                            "url": URL(args=["[id]", "enable"]),
                            "restrict": restrict_e,
                            },
                           {"label": s3_str(T("Disable")),
                            "_class": "action-btn",
                            "url": URL(args = ["[id]", "disable"]),
                            "restrict": restrict_d,
                            },
                           ]
            if not s3task._is_alive():
                # No Scheduler Running
                s3.actions += [{"label": s3_str(T("Poll")),
                                "_class": "action-btn",
                                "url": URL(args = ["[id]", "poll"]),
                                "restrict": restrict_d,
                                },
                               ]
        return output
    s3.postp = postp

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def gcm_channel():
    """
        RESTful CRUD controller for Google Cloud Messaging Channels
            - appears in the administration menu
    """

    if not auth.s3_has_role("ADMIN"):
        auth.permission.fail()

    tablename = "msg_gcm_channel"
    table = s3db[tablename]

    table.name.label = T("Account Name")
    table.name.comment = DIV(_class="tooltip",
                             _title="%s|%s" % (T("Account Label"),
                                               T("Label for GCM Account")))

    table.api_key.label = T("API KEY")

    # CRUD Strings
    s3.crud_strings[tablename] = Storage(
        title_display = T("Google Cloud Messaging Setting Details"),
        title_list = T("Google Cloud Messaging Settings"),
        label_create = T("Add Google Cloud Messaging Settings"),
        title_update = T("Edit Google Cloud Messaging Settings"),
        label_list_button = T("View Google Cloud Messaging Settings"),
        msg_record_created = T("Google Cloud Messaging Setting added"),
        msg_record_deleted = T("Google Cloud Messaging Setting deleted"),
        msg_list_empty = T("No Google Cloud Messaging Settings currently defined"),
        msg_record_modified = T("Google Cloud Messaging settings updated")
        )

    def postp(r, output):
        if r.interactive:
            # Normal Action Buttons
            s3_action_buttons(r)
            # Custom Action Buttons for Enable/Disable
            table = r.table
            query = (table.deleted != True)
            rows = db(query).select(table.id,
                                    table.enabled,
                                    )
            restrict_e = [str(row.id) for row in rows if not row.enabled]
            restrict_d = [str(row.id) for row in rows if row.enabled]

            s3.actions += [{"label": s3_str(T("Enable")),
                            "_class": "action-btn",
                            "url": URL(args=["[id]", "enable"]),
                            "restrict": restrict_e,
                            },
                           {"label": s3_str(T("Disable")),
                            "_class": "action-btn",
                            "url": URL(args = ["[id]", "disable"]),
                            "restrict": restrict_d,
                            },
                           ]
            #if not s3task._is_alive():
                # No Scheduler Running
            #    s3.actions += [{"label": s3_str(T("Poll")),
            #                    "_class": "action-btn",
            #                    "url": URL(args = ["[id]", "poll"]),
            #                    "restrict": restrict_d,
            #                    },
            #                   ]
        return output
    s3.postp = postp

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def rss_channel():
    """
       RESTful CRUD controller for RSS channels
       - appears in the administration menu
    """

    if not auth.s3_has_role("ADMIN"):
        auth.permission.fail()

    tablename = "msg_rss_channel"
    table = s3db[tablename]

    table.name.label = T("Name")
    table.description.label = T("Description")
    table.url.label = T("URL/Link")
    table.url.comment = DIV(_class="tooltip",
                            _title="%s|%s" % (T("URL"),
                                              T("Link for the RSS Feed.")))
    table.enabled.comment = DIV(_class="tooltip",
                                _title="%s|%s" % (T("Subscriptions Status"),
                                                  T("Are you susbscribed?")))

    # CRUD Strings
    s3.crud_strings[tablename] = Storage(
        title_display = T("RSS Channel Details"),
        title_list = T("RSS Channels"),
        label_create = T("Add RSS Channel"),
        title_update = T("Edit RSS Channel"),
        label_list_button = T("View RSS Channels"),
        msg_record_created = T("Channel added"),
        msg_record_deleted = T("RSS Channel deleted"),
        msg_list_empty = T("No RSS Channels currently defined"),
        msg_record_modified = T("RSS Channel updated"))

    def status_represent(v):
        try:
            v = int(v)
        except:
            # Text
            return v
        return "There have been no new entries for %s requests" % v

    s3db.msg_channel_status.status.represent = status_represent

    def postp(r, output):
        if r.interactive:
            # Normal Action Buttons
            s3_action_buttons(r)
            # Custom Action Buttons for Enable/Disable
            table = r.table
            query = (table.deleted == False)
            rows = db(query).select(table.id,
                                    table.enabled,
                                    )
            restrict_e = [str(row.id) for row in rows if not row.enabled]
            restrict_d = [str(row.id) for row in rows if row.enabled]

            s3.actions += [{"label": s3_str(T("Subscribe")),
                            "_class": "action-btn",
                            "url": URL(args=["[id]", "enable"]),
                            "restrict": restrict_e,
                            },
                           {"label": s3_str(T("Unsubscribe")),
                            "_class": "action-btn",
                            "url": URL(args = ["[id]", "disable"]),
                            "restrict": restrict_d,
                            },
                           ]
            if not s3task._is_alive():
                # No Scheduler Running
                s3.actions += [{"label": s3_str(T("Poll")),
                                "_class": "action-btn",
                                "url": URL(args = ["[id]", "poll"]),
                                "restrict": restrict_d,
                                },
                               ]
        return output
    s3.postp = postp

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def twilio_channel():
    """
        RESTful CRUD controller for Twilio SMS channels
            - appears in the administration menu
    """

    if not auth.s3_has_role("ADMIN"):
        auth.permission.fail()

    tablename = "msg_twilio_channel"
    table = s3db[tablename]

    table.account_name.label = T("Account Name")
    table.account_name.comment = DIV(_class="tooltip",
                                     _title="%s|%s" % (T("Account Name"),
                                                       T("Identifier Name for your Twilio Account.")))

    table.url.label = T("URL")
    table.url.comment = DIV(_class="tooltip",
                            _title="%s|%s" % (T("URL"),
                                              T("URL for the twilio API.")))

    table.account_sid.label = "Account SID"
    table.auth_token.label = T("AUTH TOKEN")

    # CRUD Strings
    s3.crud_strings[tablename] = Storage(
        title_display = T("Twilio Channel Details"),
        title_list = T("Twilio Channels"),
        label_create = T("Add Twilio Channel"),
        title_update = T("Edit Twilio Channel"),
        label_list_button = T("View Twilio Channels"),
        msg_record_created = T("Twilio Channel added"),
        msg_record_deleted = T("Twilio Channel deleted"),
        msg_record_modified = T("Twilio Channel updated"),
        msg_list_empty = T("No Twilio Channels currently defined"))

    def postp(r, output):
        if r.interactive:
            # Normal Action Buttons
            s3_action_buttons(r)
            # Custom Action Buttons for Enable/Disable
            table = r.table
            query = (table.deleted == False)
            rows = db(query).select(table.id,
                                    table.enabled,
                                    )
            restrict_e = [str(row.id) for row in rows if not row.enabled]
            restrict_d = [str(row.id) for row in rows if row.enabled]

            s3.actions += [{"label": s3_str(T("Enable")),
                            "_class": "action-btn",
                            "url": URL(args=["[id]", "enable"]),
                            "restrict": restrict_e,
                            },
                           {"label": s3_str(T("Disable")),
                            "_class": "action-btn",
                            "url": URL(args = ["[id]", "disable"]),
                            "restrict": restrict_d,
                            },
                           ]
            if not s3task._is_alive():
                # No Scheduler Running
                s3.actions += [{"label": s3_str(T("Poll")),
                                "_class": "action-btn",
                                "url": URL(args = ["[id]", "poll"]),
                                "restrict": restrict_d,
                                },
                               ]
        return output
    s3.postp = postp

    return s3_rest_controller()

# -----------------------------------------------------------------------------
@auth.s3_requires_membership(1)
def sms_modem_channel():
    """
        RESTful CRUD controller for modem channels
        - appears in the administration menu
        Multiple Modems can be configured to receive Inbound Messages
    """

    try:
        import serial
    except ImportError:
        session.error = T("Python Serial module not available within the running Python - this needs installing to activate the Modem")
        redirect(URL(c="admin", f="index"))

    tablename = "%s_%s" % (module, resourcename)
    table = s3db[tablename]

    table.modem_port.label = T("Port")
    table.modem_baud.label = T("Baud")
    table.enabled.label = T("Enabled")
    table.modem_port.comment = DIV(_class="tooltip",
                                   _title="%s|%s" % (T("Port"),
                                                     T("The serial port at which the modem is connected - /dev/ttyUSB0, etc on linux and com1, com2, etc on Windows")))
    table.modem_baud.comment = DIV(_class="tooltip",
                                   _title="%s|%s" % (T("Baud"),
                                                     T("Baud rate to use for your modem - The default is safe for most cases")))
    table.enabled.comment = DIV(_class="tooltip",
                                _title="%s|%s" % (T("Enabled"),
                                                  T("Unselect to disable the modem")))

    # CRUD Strings
    s3.crud_strings[tablename] = Storage(
        label_create = T("Add Modem Channel"),
        title_display = T("Modem Channel Details"),
        title_list = T("Modem Channels"),
        title_update = T("Edit Modem Channel"),
        label_list_button = T("View Modem Channels"),
        msg_record_created = T("Modem Channel added"),
        msg_record_modified = T("Modem Channel updated"),
        msg_record_deleted = T("Modem Channel deleted"),
        msg_list_empty = T("No Modem Channels currently defined"))

    return s3_rest_controller()

#------------------------------------------------------------------------------
@auth.s3_requires_membership(1)
def sms_smtp_channel():
    """
        RESTful CRUD controller for SMTP to SMS Outbound channels
        - appears in the administration menu
    """

    tablename = "%s_%s" % (module, resourcename)
    table = s3db[tablename]

    table.address.label = T("Address")
    table.subject.label = T("Subject")
    table.enabled.label = T("Enabled")
    table.address.comment = DIV(_class="tooltip",
                                _title="%s|%s" % (T("Address"),
                                                  T("Email Address to which to send SMS messages. Assumes sending to phonenumber@address")))
    table.subject.comment = DIV(_class="tooltip",
                                _title="%s|%s" % (T("Subject"),
                                                  T("Optional Subject to put into Email - can be used as a Security Password by the service provider")))
    table.enabled.comment = DIV(_class="tooltip",
                                _title="%s|%s" % (T("Enabled"),
                                                  T("Unselect to disable this SMTP service")))

    # CRUD Strings
    s3.crud_strings["msg_sms_outbound_gateway"] = Storage(
        label_create=T("Create SMTP to SMS Channel"),
        title_display=T("SMTP to SMS Channel Details"),
        title_list=T("SMTP to SMS Channels"),
        title_update=T("Edit SMTP to SMS Channel"),
        label_list_button=T("List SMTP to SMS Channels"),
        label_delete_button=T("Delete SMTP to SMS Channel"),
        msg_record_created=T("SMTP to SMS Channel added"),
        msg_record_modified=T("SMTP to SMS Channel updated"),
        msg_record_deleted=T("SMTP to SMS Channel deleted"),
        msg_list_empty=T("No SMTP to SMS Channels currently registered"))

    s3db.configure(tablename,
                   update_next = URL(args=[1, "update"]))

    return s3_rest_controller()

#------------------------------------------------------------------------------
@auth.s3_requires_membership(1)
def sms_webapi_channel():
    """
        RESTful CRUD controller for Web API channels
        - appears in the administration menu
    """

    tablename = "%s_%s" % (module, resourcename)
    table = s3db[tablename]

    table.url.label = T("URL")
    table.message_variable.label = T("Message variable")
    table.to_variable.label = T("To variable")
    table.username.label = T("Username")
    table.password.label = T("Password")
    table.enabled.label = T("Enabled")
    table.url.comment = DIV(_class="tooltip",
        _title="%s|%s" % (T("URL"),
                          T("The URL of your web gateway without the POST parameters")))
    table.parameters.comment = DIV(_class="tooltip",
        _title="%s|%s" % (T("Parameters"),
                          T("The POST variables other than the ones containing the message and the phone number")))
    table.message_variable.comment = DIV(_class="tooltip",
        _title="%s|%s" % (T("Message Variable"),
                          T("The POST variable on the URL used for sending messages")))
    table.to_variable.comment = DIV(_class="tooltip",
        _title="%s|%s" % (T("To variable"),
                          T("The POST variable containing the phone number")))
    table.username.comment = DIV(_class="tooltip",
        _title="%s|%s" % (T("Username"),
                          T("If the service requries HTTP BASIC Auth (e.g. Mobile Commons)")))
    table.password.comment = DIV(_class="tooltip",
        _title="%s|%s" % (T("Password"),
                          T("If the service requries HTTP BASIC Auth (e.g. Mobile Commons)")))
    table.enabled.comment = DIV(_class="tooltip",
        _title="%s|%s" % (T("Enabled"),
                          T("Unselect to disable this API service")))

    # CRUD Strings
    s3.crud_strings[tablename] = Storage(
        label_create=T("Create Web API Channel"),
        title_display=T("Web API Channel Details"),
        title_list=T("Web API Channels"),
        title_update=T("Edit Web API Channel"),
        label_list_button=T("List Web API Channels"),
        label_delete_button=T("Delete Web API Channel"),
        msg_record_created=T("Web API Channel added"),
        msg_record_modified=T("Web API Channel updated"),
        msg_record_deleted=T("Web API Channel deleted"),
        msg_list_empty=T("No Web API Channels currently registered"))

    return s3_rest_controller()

# -----------------------------------------------------------------------------
@auth.s3_requires_membership(1)
def tropo_channel():
    """
        RESTful CRUD controller for Tropo channels
        - appears in the administration menu
    """

    tablename = "msg_tropo_channel"
    table = s3db[tablename]

    table.token_messaging.label = T("Tropo Messaging Token")
    table.token_messaging.comment = DIV(DIV(_class="stickytip",
                                            _title="%s|%s" % (T("Tropo Messaging Token"),
                                                              T("The token associated with this application on") + " <a href='https://www.tropo.com/docs/scripting/troposessionapi.htm' target=_blank>Tropo.com</a>")))
    #table.token_voice.label = T("Tropo Voice Token")
    #table.token_voice.comment = DIV(DIV(_class="stickytip",_title=T("Tropo Voice Token") + "|" + T("The token associated with this application on") + " <a href='https://www.tropo.com/docs/scripting/troposessionapi.htm' target=_blank>Tropo.com</a>"))
    # CRUD Strings
    s3.crud_strings[tablename] = Storage(
        label_create=T("Create Tropo Channel"),
        title_display=T("Tropo Channel Details"),
        title_list=T("Tropo Channels"),
        title_update=T("Edit Tropo Channel"),
        label_list_button=T("List Tropo Channels"),
        label_delete_button=T("Delete Tropo Channel"),
        msg_record_created=T("Tropo Channel added"),
        msg_record_modified=T("Tropo Channel updated"),
        msg_record_deleted=T("Tropo Channel deleted"),
        msg_list_empty=T("No Tropo Channels currently registered"))

    return s3_rest_controller()

# -----------------------------------------------------------------------------
@auth.s3_requires_membership(1)
def twitter_channel():
    """
        RESTful CRUD controller for Twitter channels
        - appears in the administration menu
        Only 1 of these normally in existence
            @ToDo: Don't enforce
    """

    #try:
    #    import tweepy
    #except:
    #    session.error = T("tweepy module not available within the running Python - this needs installing for non-Tropo Twitter support!")
    #    redirect(URL(c="admin", f="index"))

    tablename = "%s_%s" % (module, resourcename)
    table = s3db[tablename]

    # CRUD Strings
    s3.crud_strings[tablename] = Storage(
        title_display = T("Twitter account Details"),
        title_list = T("Twitter accounts"),
        label_create = T("Add Twitter account"),
        title_update = T("Edit Twitter account"),
        label_list_button = T("View Twitter accounts"),
        msg_record_created = T("Twitter account added"),
        msg_record_deleted = T("Twitter account deleted"),
        msg_record_modified = T("Twitter account updated"),
        msg_list_empty = T("No Twitter accounts currently defined"))

    def prep(r):
        oauth_consumer_key = settings.msg.twitter_oauth_consumer_key
        oauth_consumer_secret = settings.msg.twitter_oauth_consumer_secret
        if not (oauth_consumer_key and oauth_consumer_secret):
           session.error = T("You should edit Twitter settings in models/000_config.py")
           return True
        oauth = tweepy.OAuthHandler(oauth_consumer_key,
                                   oauth_consumer_secret)

        if r.http == "GET" and r.method in ("create", "update"):
           # We're showing the form
           _s3 = session.s3
           try:
               _s3.twitter_oauth_url = oauth.get_authorization_url()
               _s3.twitter_request_key = oauth.request_token.key
               _s3.twitter_request_secret = oauth.request_token.secret
           except tweepy.TweepError:
               session.error = T("Problem connecting to twitter.com - please refresh")
               return True
           #table.pin.readable = True
           #table.pin.label = T("PIN number from Twitter (leave empty to detach account)")
           #table.pin.value = ""
           table.twitter_account.label = T("Current Twitter account")
           return True
        else:
           # Not showing form, no need for pin
           #table.pin.readable = False
           #table.pin.label = T("PIN") # won't be seen
           #table.pin.value = ""       # but let's be on the safe side
           pass
        return True
    #s3.prep = prep

    # Post-process
    def postp(r, output):
        if r.interactive:
            # Normal Action Buttons
            s3_action_buttons(r)
            # Custom Action Buttons for Enable/Disable
            table = r.table
            query = (table.deleted == False)
            rows = db(query).select(table.id,
                                    table.enabled,
                                    )
            restrict_e = [str(row.id) for row in rows if not row.enabled]
            restrict_d = [str(row.id) for row in rows if row.enabled]

            s3.actions += [{"label": s3_str(T("Enable")),
                            "_class": "action-btn",
                            "url": URL(args=["[id]", "enable"]),
                            "restrict": restrict_e,
                            },
                           {"label": s3_str(T("Disable")),
                            "_class": "action-btn",
                            "url": URL(args = ["[id]", "disable"]),
                            "restrict": restrict_d,
                            },
                           ]
            if not s3task._is_alive():
                # No Scheduler Running
                s3.actions += [{"label": s3_str(T("Poll")),
                                "_class": "action-btn",
                                "url": URL(args = ["[id]", "poll"]),
                                "restrict": restrict_d,
                                },
                               ]

            #if isinstance(output, dict):
            #    if r.http == "GET" and r.method in ("create", "update"):
            #        rheader = A(T("Collect PIN from Twitter"),
            #                    _href=session.s3.twitter_oauth_url,
            #                    _target="_blank")
            #        output["rheader"] = rheader
        return output
    s3.postp = postp

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def inject_search_after_save(output):
    """
        Inject a Search After Save checkbox
        in the Twitter Search Query Form
    """

    if "form" in output:
        id = "search_after_save"
        label = LABEL("%s:" % T("Search After Save?"),
                      _for="msg_twitter_search")
        widget = INPUT(_name="search_after_save",
                       _type="checkbox",
                       value="on",
                       _id=id,
                       _class="boolean")
        comment = ""
        if s3_formstyle == "bootstrap":
            _controls = DIV(widget, comment, _class="controls")
            row = DIV(label,
                      _controls,
                      _class="control-group",
                      _id="%s__row" % id
                      )
        elif callable(s3_formstyle):
            row = s3_formstyle(id, label, widget, comment)
        else:
            # Unsupported
            raise

        output["form"][0][-2].append(row)

# -----------------------------------------------------------------------------
def action_after_save(form):
    """
        Schedules Twitter query search immediately after save
        depending on flag
    """

    if request.post_vars.get("search_after_save"):
        s3task.run_async("msg_twitter_search", args=[form.vars.id])
        session.information = T("The search results should appear shortly - refresh to see them")

# -----------------------------------------------------------------------------
def twitter_search():
    """
       RESTful CRUD controller to add keywords
       for Twitter Search
    """

    tablename = "msg_twitter_search"
    table = s3db[tablename]

    table.is_processed.writable = False
    table.is_searched.writable = False
    table.is_processed.readable = False
    table.is_searched.readable = False

    # Tweak languages to those supported by Twitter
    S3Msg = s3base.S3Msg()
    try:
        import tweepy
    except:
        session.error = T("tweepy module not available within the running Python - this needs installing for non-Tropo Twitter support!")
        redirect(URL(c="msg", f="index"))

    twitter_settings = S3Msg.get_twitter_api()
    supported_languages = ['fr', 'en', 'ar', 'ja', 'es', 'de', 'it', 'id', 'pt', 'ko', 'tr', 'ru', 'nl', 'fil',
                       'msa', 'zh-tw', 'zh-cn', 'hi', 'no', 'sv', 'fi', 'da', 'pl', 'hu', 'fa', 'he', 'ur', 'th']
    if twitter_settings:
        twitter_api = twitter_settings[0]

        try:
            supported_languages = [str(x["code"]) for x in twitter_api.supported_languages()]
        except (tweepy.TweepError, AttributeError):
            # List according to Twitter 1.1 API https://dev.twitter.com/docs/api/1.1/get/help/languages
            pass

    substitute_list = {"en-gb": "en",
                       "pt-br": "pt"}

    new_langs = []
    lang_default = current.response.s3.language

    langs = set(settings.get_L10n_languages().keys())
    for l in langs:
        if l in supported_languages:
            new_langs.append(l)
        else:
            supported_substitute = substitute_list.get(l)
            if supported_substitute:
                if lang_default == l:
                    lang_default = supported_substitute
                if supported_substitute not in langs:
                    new_langs.append(supported_substitute)
            else:
                if lang_default == l:
                    lang_default = 'en'

    langs = new_langs

    table.lang.requires = IS_IN_SET(langs)
    table.lang.default = lang_default

    comment = "Add the keywords separated by single spaces."
    table.keywords.comment = DIV(_class="tooltip",
                                 _title="%s|%s" % (T("Keywords"),
                                                   T(comment)))

    # CRUD Strings
    s3.crud_strings[tablename] = Storage(
        title_display = T("Twitter Search Queries"),
        title_list = T("Twitter Search Queries"),
        label_create = T("Add Twitter Search Query"),
        title_update = T("Edit Twitter Search Query"),
        label_list_button = T("View Queries"),
        msg_record_created = T("Query added"),
        msg_record_deleted = T("Query deleted"),
        msg_list_empty = T("No Query currently defined"),
        msg_record_modified = T("Query updated")
        )

    if request.post_vars.get("search_after_save"):
        url_after_save = URL(f="twitter_result")
    else:
        url_after_save = None

    s3db.configure(tablename,
                   listadd=True,
                   deletable=True,
                   create_onaccept=action_after_save,
                   create_next=url_after_save
                   )

    def prep(r):
        if r.interactive:
            table = s3db.msg_twitter_channel
            if not db(table.id > 0).select(table.id,
                                           limitby=(0, 1)).first():
                session.error = T("Need to configure Twitter Authentication")
                redirect(URL(f="twitter_channel"))
        return True
    s3.prep = prep

    def postp(r, output):
        if r.interactive:
            # Normal Action Buttons
            s3_action_buttons(r)

            # Custom Action Buttons
            rtable = r.table
            query = (rtable.deleted == False) & \
                    (rtable.is_searched == False)
            records = db(query).select(rtable.id)

            restrict_s = [str(record.id) for record in records]

            query = (rtable.deleted == False) & \
                    (rtable.is_processed == False)
            records = db(query).select(rtable.id)

            restrict_k = [str(record.id) for record in records]

            # @ToDo: Make these S3Methods rather than additional controllers
            s3.actions += [{"label": s3_str(T("Search")),
                            "_class": "action-btn",
                            "url": URL(args=["[id]", "poll"]),
                            "restrict": restrict_s,
                            },
                           {"label": s3_str(T("Analyze with KeyGraph")),
                            "_class": "action-btn",
                            "url": URL(args=["[id]", "keygraph"]),
                            "restrict": restrict_k,
                            },
                           ]

            inject_search_after_save(output)

        return output
    s3.postp = postp

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def twitter_result():
    """
       RESTful CRUD controller for Twitter Search Results.
    """

    tablename = "msg_twitter_result"
    # CRUD Strings
    s3.crud_strings[tablename] = Storage(
        title_display = T("Twitter Search Results"),
        title_list = T("Twitter Search Results"),
        label_list_button = T("View Tweets"),
        msg_record_deleted = T("Tweet deleted"),
        msg_list_empty = T("No Tweets Available."),
        )

    from s3.s3filter import S3DateFilter, S3TextFilter

    filter_widgets = [
        S3DateFilter("date",
                     label=T("Tweeted on"),
                     hide_time=True,
                     _class="date-filter-class",
                     comment=T("Filter Tweets by the date they were tweeted on"),
                     ),
        S3TextFilter("from_address",
                     label=T("Tweeted by"),
                     _class="tweeter-filter-class",
                     comment=T("Filter Tweets by who tweeted them"),
                     )
        ]

    report_fields = ["search_id",
                     "date",
                     "lang",
                     ]

    report_options = Storage(
        rows=report_fields,
        cols=report_fields,
        fact=report_fields,
        defaults=Storage(
            rows="search_id",
            cols="lang",
            totals=True,
        )
    )
    s3db.configure(tablename,
                   deletable=False,
                   editable=False,
                   insertable=False,
                   filter_widgets=filter_widgets,
                   report_options=report_options,
                   )

    def postp(r, output):
        if r.id or r.method in ("read", "display"):
            # Display the Tweet as an Embedded tweet
            record = output["item"].record
            # Tweet link
            twitter_url = "https://twitter.com/%s/statuses/%s" % (record.from_address,
                                                                  record.tweet_id)
            script_url = "https://platform.twitter.com/widgets.js"
            # Themeable Throbber
            throbber = DIV(_class = "s3-twitter-throbber",
                           )
            # Display throbber while Tweet loads
            tweet_container = DIV(throbber,
                                  _class = "s3-twitter-container",
                                  )
            tweet_user = TAG[""](A(_href = twitter_url,
                                   _style = "display: none"),
                                 )
            # Configure Tweet display
            attributes = {"_width": "350px",
                          "_data-conversation": "none",
                          "_class": "twitter-tweet",
                          "lang": record.lang,
                          }
            tweet = TAG["blockquote"](tweet_container,
                                      tweet_user,
                                      SCRIPT(_src = script_url,
                                             _charset = "utf-8"),
                                      **attributes
                                      )
            # Insert tweet
            output["item"] = tweet
        return output

    s3.postp = postp

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def sender():
    """
       RESTful CRUD controller for whitelisting senders.
       User can assign priority to senders.
    """

    tablename = "msg_sender"

    # CRUD Strings
    s3.crud_strings[tablename] = Storage(
        title_display = T("Whitelisted Senders"),
        title_list = T("Whitelisted Senders"),
        label_create = T("Whitelist a Sender"),
        title_update = T("Edit Sender Priority"),
        label_list_button = T("View Sender Priority"),
        msg_record_created = T("Sender Whitelisted"),
        msg_record_deleted = T("Sender deleted"),
        msg_list_empty = T("No Senders Whitelisted"),
        msg_record_modified = T("Sender Priority updated")
        )

    s3db.configure(tablename, listadd=True)

    def prep(r):
        if r.method == "create":
            dsender = request.vars['sender']
            dpriority = request.vars['priority']
            r.table.sender.default = dsender
            r.table.priority.default = dpriority

        return True
    s3.prep = prep

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def keyword():
    """ REST Controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def parser():
    """
        RESTful CRUD controller for Parsers
            - appears in the administration menu
    """

    if not auth.s3_has_role("ADMIN"):
        auth.permission.fail()

    def prep(r):
        if r.interactive:
            # CRUD Strings
            s3.crud_strings["msg_parser"] = Storage(
                title_display = T("Parser Connection Details"),
                title_list = T("Parser Connections"),
                label_create = T("Connect Parser"),
                title_update = T("Edit Parser Connection"),
                label_list_button = T("View Parser Connections"),
                msg_record_created = T("Parser connected"),
                msg_record_deleted = T("Parser connection removed"),
                msg_record_modified = T("Parser connection updated"),
                msg_list_empty = T("No Parsers currently connected"),
            )

            import inspect
            import sys

            template = settings.get_msg_parser()
            module_name = "applications.%s.modules.templates.%s.parser" % \
                (appname, template)
            __import__(module_name)
            mymodule = sys.modules[module_name]
            S3Parser = mymodule.S3Parser()

            # Dynamic lookup of the parsing functions in S3Parser class.
            parsers = inspect.getmembers(S3Parser, \
                                         predicate=inspect.isfunction)
            parse_opts = []
            pappend = parse_opts.append
            for p in parsers:
                p = p[0]
                # Filter out helper functions
                if not p.startswith("_"):
                    pappend(p)

            table = r.table
            table.channel_id.requires = IS_ONE_OF(db, "msg_channel.channel_id",
                                                  s3base.S3Represent(lookup="msg_channel"),
                                                  sort = True,
                                                  )
            table.function_name.requires = IS_IN_SET(parse_opts,
                                                     zero = None)
        return True
    s3.prep = prep

    def postp(r, output):
        if r.interactive:
            # Normal Action Buttons
            s3_action_buttons(r)
            # Custom Action Buttons for Enable/Disable
            table = r.table
            query = (table.deleted == False)
            rows = db(query).select(table.id,
                                    table.enabled,
                                    )
            restrict_e = [str(row.id) for row in rows if not row.enabled]
            restrict_d = [str(row.id) for row in rows if row.enabled]

            s3.actions += [{"label": s3_str(T("Enable")),
                            "_class": "action-btn",
                            "url": URL(args=["[id]", "enable"]),
                            "restrict": restrict_e,
                            },
                           {"label": s3_str(T("Disable")),
                            "_class": "action-btn",
                            "url": URL(args = ["[id]", "disable"]),
                            "restrict": restrict_d,
                            },
                           ]
            if not s3task._is_alive():
                # No Scheduler Running
                s3.actions += [{"label": s3_str(T("Parse")),
                                "_class": "action-btn",
                                "url": URL(args = ["[id]", "parse"]),
                                "restrict": restrict_d,
                                },
                               ]

        return output
    s3.postp = postp

    return s3_rest_controller()

# =============================================================================
# The following functions hook into the pr functions:
#
def group():
    """ RESTful CRUD controller """

    if auth.is_logged_in() or auth.basic():
        pass
    else:
        redirect(URL(c="default", f="user", args="login",
        vars={"_next":URL(c="msg", f="group")}))

    module = "pr"
    tablename = "%s_%s" % (module, resourcename)
    table = s3db[tablename]

    # Hide unnecessary fields
    table.description.readable = table.description.writable = False

    # Do not show system groups
    s3.filter = (table.system == False)

    return s3_rest_controller(module, resourcename,
                              rheader = s3db.pr_rheader,
                              )

# -----------------------------------------------------------------------------
def group_membership():
    """ RESTful CRUD controller """

    if auth.is_logged_in() or auth.basic():
        pass
    else:
        redirect(URL(c="default", f="user", args="login",
        vars={"_next": URL(c="msg", f="group_membership")}))

    table = s3db.pr_group_membership

    # Hide unnecessary fields
    table.comments.readable = table.comments.writable = False
    table.group_head.readable = table.group_head.writable = False

    return s3_rest_controller("pr", resourcename)

# -----------------------------------------------------------------------------
def contacts():
    """
        Allow the user to add, update and delete their contacts
        - seems to be unused (was called 'contact' & was broken)
    """

    table = s3db.pr_contact
    #ptable = s3db.pr_person

    if auth.is_logged_in() or auth.basic():
        s3.filter = (table.pe_id == auth.user.pe_id)
    else:
        redirect(URL(c="default", f="user", args="login",
            vars={"_next": URL(c="msg", f="contact")}))

    # These fields will be populated automatically
    table.name.writable = table.name.readable = False
    table.pe_id.writable = table.pe_id.readable = False
    table.person_name.writable = table.person_name.readable = False
    table.id.writable = False
    #table.id.readable = False

    def msg_contact_onvalidation(form):
        # Add the person id to the record
        if auth.user:
            form.vars.pe_id = auth.user.pe_id

    s3db.configure(table._tablename,
                   onvalidation = msg_contact_onvalidation)

    def prep(r):
        # Restrict update and delete access to contacts not owned by the user
        if r.id :
            pe_id = r.record.pe_id
            if auth.user and auth.user.pe_id == pe_id:
                return True
            else:
                session.error = T("Access denied")
                return {"bypass": True, "output": redirect(URL(r=request))}
        else:
            return True
    s3.prep = prep

    response.menu_options = []

    return s3_rest_controller("pr", "contact")

# -----------------------------------------------------------------------------
def search():
    """
        Do a search of groups which match a type
        - used for auto-completion
    """

    if not (auth.is_logged_in() or auth.basic()):
        # Not allowed
        return

    # JQuery UI Autocomplete uses 'term' instead of 'value'
    # (old JQuery Autocomplete uses 'q' instead of 'value')
    value = request.vars.term or request.vars.q
    if not value:
        return

    # Call the search function
    type = get_vars.get("type", None)
    if type:
        items = person_search(value, type)
    else:
        items = person_search(value)
    # Encode in JSON
    item = json.dumps(items)
    response.headers["Content-Type"] = "application/json"
    return item

# -----------------------------------------------------------------------------
def recipient_represent(id, default_label=""):
    """ Simplified output as-compared to pr_pentity_represent """

    output = ""
    table = s3db.pr_pentity
    pe = db(table.pe_id == id).select(table.instance_type,
                                      limitby=(0, 1)).first()
    if not pe:
        return output
    instance_type = pe.instance_type
    table = db.get(instance_type, None)
    if not table:
        return output
    if instance_type == "pr_person":
        person = db(table.pe_id == id).select(table.first_name,
                                              table.middle_name,
                                              table.last_name,
                                              limitby=(0, 1)).first()
        if person:
            output = s3_fullname(person)
    elif instance_type == "pr_group":
        group = db(table.pe_id == id).select(table.name,
                                             limitby=(0, 1)).first()
        if group:
            output = group.name
    return output

# -----------------------------------------------------------------------------
def person_search(value, type=None):
    """ Search for People & Groups which match a search term """

    # Shortcuts
    groups = s3db.pr_group
    persons = s3db.pr_person

    items = []

    # We want to do case-insensitive searches
    # (default anyway on MySQL/SQLite, but not PostgreSQL)
    value = value.lower()

    if type:
        represent = recipient_represent
    else:
        represent = s3db.pr_pentity_represent

    if type == "pr_group" or not type:
        # Check Groups
        query = (groups["name"].lower().like("%" + value + "%")) & (groups.deleted == False)
        rows = db(query).select(groups.pe_id)
        for row in rows:
            items.append({"id":row.pe_id, "name":represent(row.pe_id, default_label = "")})

    if type == "pr_person" or not type:
        # Check Persons
        deleted = (persons.deleted == False)

        # First name
        query = (persons["first_name"].lower().like("%" + value + "%")) & deleted
        rows = db(query).select(persons.pe_id, cache=s3db.cache)
        for row in rows:
            items.append({"id":row.pe_id, "name":represent(row.pe_id, default_label = "")})

        # Middle name
        query = (persons["middle_name"].lower().like("%" + value + "%")) & deleted
        rows = db(query).select(persons.pe_id, cache=s3db.cache)
        for row in rows:
            items.append({"id":row.pe_id, "name":represent(row.pe_id, default_label = "")})

        # Last name
        query = (persons["last_name"].lower().like("%" + value + "%")) & deleted
        rows = db(query).select(persons.pe_id, cache=s3db.cache)
        for row in rows:
            items.append({"id":row.pe_id, "name":represent(row.pe_id, default_label = "")})

    return items

# -----------------------------------------------------------------------------
def subscription():
    """ RESTful CRUD controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
# Send Outbound Messages (was for being called via cron, now useful for debugging)
# -----------------------------------------------------------------------------
def process_email_outbox():
    """ Send Pending Email Messages """

    msg.process_outbox(contact_method = "EMAIL")

# -----------------------------------------------------------------------------
def process_sms_outbox():
    """ Send Pending SMS Messages """

    msg.process_outbox(contact_method = "SMS")

# -----------------------------------------------------------------------------
def process_twitter_outbox():
    """ Send Pending Twitter Messages """

    msg.process_outbox(contact_method = "TWITTER")

# =============================================================================
# Enabled only for testing:
#
@auth.s3_requires_membership(1)
def facebook_post():
    """ Post to Facebook """

    title = T("Post to Facebook")

    # Test the formstyle
    formstyle = s3.crud.formstyle
    row = formstyle("test", "test", "test", "test")
    if isinstance(row, tuple):
        # Formstyle with separate row for label (e.g. default Eden formstyle)
        tuple_rows = True
    else:
        # Formstyle with just a single row (e.g. Bootstrap, Foundation or DRRPP)
        tuple_rows = False

    form_rows = []
    comment = ""

    _id = "channel_id"
    label = LABEL("%s:" % T("Channel"))

    table = s3db.msg_facebook_channel
    query = (table.deleted == False) & \
            (table.enabled == True)
    rows = db(query).select(table.channel_id, table.name)
    options = [OPTION(row.name, _value=row.channel_id) for row in rows]
    channel_select = SELECT(_name = "channel_id",
                            _id = _id,
                            *options
                            )
    widget = channel_select
    row = formstyle("%s__row" % _id, label, widget, comment)
    if tuple_rows:
        form_rows.append(row[0])
        form_rows.append(row[1])
    else:
        form_rows.append(row)

    _id = "post"
    label = LABEL("%s:" % T("Contents"))
    widget = TEXTAREA(_name = "post",
                      )
    row = formstyle("%s__row" % _id, label, widget, comment)
    if tuple_rows:
        form_rows.append(row[0])
        form_rows.append(row[1])
    else:
        form_rows.append(row)

    _id = "submit"
    label = ""
    widget = INPUT(_type="submit", _value=T("Post"))
    row = formstyle("%s__row" % _id, label, widget, comment)
    if tuple_rows:
        form_rows.append(row[0])
        form_rows.append(row[1])
    else:
        form_rows.append(row)

    if tuple_rows:
        # Assume TRs
        form = FORM(TABLE(*form_rows))
    else:
        form = FORM(*form_rows)

    if form.accepts(request.vars, session):
        form_vars = form.vars
        channel_id = form_vars.get("channel_id")
        post = form_vars.get("post")
        if channel_id and post:
            msg.post_to_facebook(post, channel_id)

    output = {"form": form,
              "title": title,
              }
    return output

# =============================================================================
# Enabled only for testing:
#
@auth.s3_requires_membership(1)
def twitter_post():
    """ Post to Twitter """

    title = T("Post to Twitter")

    # Test the formstyle
    formstyle = s3.crud.formstyle
    row = formstyle("test", "test", "test", "test")
    if isinstance(row, tuple):
        # Formstyle with separate row for label (e.g. default Eden formstyle)
        tuple_rows = True
    else:
        # Formstyle with just a single row (e.g. Bootstrap, Foundation or DRRPP)
        tuple_rows = False

    form_rows = []
    comment = ""

    _id = "channel_id"
    label = LABEL("%s:" % T("Channel"))

    table = s3db.msg_twitter_channel
    query = (table.deleted == False) & \
            (table.enabled == True)
    rows = db(query).select(table.channel_id, table.name)
    options = [OPTION(row.name, _value=row.channel_id) for row in rows]
    channel_select = SELECT(_name = "channel_id",
                            _id = _id,
                            *options
                            )
    widget = channel_select
    row = formstyle("%s__row" % _id, label, widget, comment)
    if tuple_rows:
        form_rows.append(row[0])
        form_rows.append(row[1])
    else:
        form_rows.append(row)

    _id = "post"
    label = LABEL("%s:" % T("Contents"))
    widget = TEXTAREA(_name = "post",
                      )
    row = formstyle("%s__row" % _id, label, widget, comment)
    if tuple_rows:
        form_rows.append(row[0])
        form_rows.append(row[1])
    else:
        form_rows.append(row)

    _id = "submit"
    label = ""
    widget = INPUT(_type="submit", _value=T("Post"))
    row = formstyle("%s__row" % _id, label, widget, comment)
    if tuple_rows:
        form_rows.append(row[0])
        form_rows.append(row[1])
    else:
        form_rows.append(row)

    if tuple_rows:
        # Assume TRs
        form = FORM(TABLE(*form_rows))
    else:
        form = FORM(*form_rows)

    if form.accepts(request.vars, session):
        form_vars = form.vars
        channel_id = form_vars.get("channel_id")
        post = form_vars.get("post")
        if channel_id and post:
            msg.send_tweet(post)

    output = {"form": form,
              "title": title,
              }
    return output

# =============================================================================
# Enabled only for testing:
#
@auth.s3_requires_membership(1)
def tag():
    """ RESTful CRUD controller """

    return s3_rest_controller()

# =============================================================================
# Enabled only for testing:
#
def readKeyGraph(queryID):
    """  """

    import os
    curpath = os.getcwd()

    f = open("%s.txt" % queryID, "r")

    topics = int(next(f))

    nodelabel = {}
    E = []
    nodetopic = {}
    for x in range(0, topics):
        thisnodes = []
        nodes = int(next(f).split("KEYGRAPH_NODES:")[1])
        for y in range(0, nodes):
            s = next(f)
            nodeid = s.split(":")[0]
            nodetopic[str(nodeid)] = x
            l1 = s.split(":")[1]
            l2 = s.split(":")[2]
            try:
                nodelabel[str(nodeid)] = unicode(l2.strip())
            except:
                pass
        edges = int(next(f).split("KEYGRAPH_EDGES:")[1])
        edges = edges / 2
        for y in range(0,edges):
            s = next(f)
            n1 = s.split(" ")[0].strip()
            n2 = s.split(" ")[1].strip()
            if (n1 in nodelabel.keys()) and (n2 in nodelabel.keys()):
                E.append((str(n1), str(n2)))

        next(f)
        next(f)

    """
    for x in range(0,len(E)):
        lx = list(E[x])
        lx.append((nodetopic[E[x][0]] - nodetopic[E[x][1]] + 3)*100)
        E[x] = tuple(lx)
    """
    #import networkx as nx
    from igraph import Graph, write_svg
    #g = nx.Graph()
    g = Graph()
    g.add_vertices([ str(s) for s in nodelabel.keys()])
    #g.add_nodes_from(nodelabel)
    g.add_edges(E)
    g.vs["name"] = list(nodelabel.values())
    g.vs["label"] = g.vs["name"]
    g.vs["doc_id"] = list(nodelabel.keys())
    layout = g.layout_lgl()
    #layout = g.layout_kamada_kawai()
    visual_style = {}
    visual_style["vertex_size"] = 20
    #visual_style["vertex_color"] = [color_dict[gender] for gender in g.vs["gender"]]
    visual_style["vertex_label"] = g.vs["name"]
    #visual_style["edge_width"] = [1 + 2 * int(len(is_formal)) for is_formal in g.vs["label"]]
    visual_style["layout"] = layout
    visual_style["bbox"] = (2000, 2000)
    visual_style["margin"] = 20
    #plot(g, **visual_style)
    #c =  g.clusters().subgraphs()
    filename = "%s.svg" % queryID
    write_svg(g.community_fastgreedy().as_clustering().graph, layout=layout, **visual_style)
    #plot(g.community_fastgreedy().as_clustering(), layout=layout)
    #plot(g)
    #g.add_weighted_edges_from(E)
    #nx.relabel_nodes(g, nodelabel, copy=False)
    #nx.draw(g, node_size=100, font_size=8, edge_size=10000)
    #labels = nx.draw_networkx_labels(g,pos=nx.spring_layout(g),labels=nodelabel)
    #import matplotlib.pyplot as plt
    #plt.savefig('kg3.png', facecolor='w', edgecolor='w',orientation='portrait', papertype=None, format=None,transparent=False, bbox_inches=None, pad_inches=0.1)
    #plt.show()

# END ================================================================================
