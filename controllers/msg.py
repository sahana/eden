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

    module_name = settings.modules[module].get("name_nice")
    response.title = module_name
    return {"module_name": module_name,
            }

# -----------------------------------------------------------------------------
def basestation():
    """ RESTful CRUD controller for Base Stations """

    return crud_controller()

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

    return crud_controller()

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

    return crud_controller()

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

    return crud_controller()

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
                        _class = "action-btn",
                        _href = URL(f="compose")
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

    return crud_controller(module, "email")

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

    return crud_controller(module, "sms")

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

    return crud_controller(module, "message")

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

    from core import CustomForm, InlineComponent
    crud_form = CustomForm("date",
                           "subject",
                           "from_address",
                           "body",
                           InlineComponent(
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

    return crud_controller(module, "email")

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

    return crud_controller()

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

    return crud_controller(module, "sms")

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
@auth.requires_membership("ADMIN")
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

    return crud_controller()

# -----------------------------------------------------------------------------
def channel():
    """
        RESTful CRUD controller for Channels
        - unused
    """

    return crud_controller()

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
                            "restrict": restrict_e,
                            "url": URL(args = ["[id]", "enable"]),
                            "_class": "action-btn",
                            },
                           {"label": s3_str(T("Disable")),
                            "restrict": restrict_d,
                            "url": URL(args = ["[id]", "disable"]),
                            "_class": "action-btn",
                            },
                           ]
            if not s3task._is_alive():
                # No Scheduler Running
                s3.actions += [{"label": s3_str(T("Poll")),
                                "restrict": restrict_d,
                                "url": URL(args = ["[id]", "poll"]),
                                "_class": "action-btn",
                                },
                               ]
        return output
    s3.postp = postp

    return crud_controller()

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
                            "restrict": restrict_e,
                            "url": URL(args=["[id]", "enable"]),
                            "_class": "action-btn",
                            },
                           {"label": s3_str(T("Disable")),
                            "restrict": restrict_d,
                            "url": URL(args = ["[id]", "disable"]),
                            "_class": "action-btn",
                            },
                           ]
            if not s3task._is_alive():
                # No Scheduler Running
                s3.actions += [{"label": s3_str(T("Poll")),
                                "restrict": restrict_d,
                                "url": URL(args = ["[id]", "poll"]),
                                "_class": "action-btn",
                                },
                               ]
        return output
    s3.postp = postp

    return crud_controller()

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
                            "restrict": restrict_e,
                            "url": URL(args=["[id]", "enable"]),
                            "_class": "action-btn",
                            },
                           {"label": s3_str(T("Disable")),
                            "restrict": restrict_d,
                            "url": URL(args = ["[id]", "disable"]),
                            "_class": "action-btn",
                            },
                           ]
            #if not s3task._is_alive():
                # No Scheduler Running
            #    s3.actions += [{"label": s3_str(T("Poll")),
            #                    "restrict": restrict_d,
            #                    "url": URL(args = ["[id]", "poll"]),
            #                    "_class": "action-btn",
            #                    },
            #                   ]
        return output
    s3.postp = postp

    return crud_controller()

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
                            "restrict": restrict_e,
                            "url": URL(args=["[id]", "enable"]),
                            "_class": "action-btn",
                            },
                           {"label": s3_str(T("Unsubscribe")),
                            "restrict": restrict_d,
                            "url": URL(args = ["[id]", "disable"]),
                            "_class": "action-btn",
                            },
                           ]
            if not s3task._is_alive():
                # No Scheduler Running
                s3.actions += [{"label": s3_str(T("Poll")),
                                "restrict": restrict_d,
                                "url": URL(args = ["[id]", "poll"]),
                                "_class": "action-btn",
                                },
                               ]
        return output
    s3.postp = postp

    return crud_controller()

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
                            "restrict": restrict_e,
                            "url": URL(args=["[id]", "enable"]),
                            "_class": "action-btn",
                            },
                           {"label": s3_str(T("Disable")),
                            "restrict": restrict_d,
                            "url": URL(args = ["[id]", "disable"]),
                            "_class": "action-btn",
                            },
                           ]
            if not s3task._is_alive():
                # No Scheduler Running
                s3.actions += [{"label": s3_str(T("Poll")),
                                "restrict": restrict_d,
                                "url": URL(args = ["[id]", "poll"]),
                                "_class": "action-btn",
                                },
                               ]
        return output
    s3.postp = postp

    return crud_controller()

# -----------------------------------------------------------------------------
@auth.requires_membership("ADMIN")
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

    return crud_controller()

#------------------------------------------------------------------------------
@auth.requires_membership("ADMIN")
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

    return crud_controller()

#------------------------------------------------------------------------------
@auth.requires_membership("ADMIN")
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

    return crud_controller()

# -----------------------------------------------------------------------------
@auth.requires_membership("ADMIN")
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

    return crud_controller()

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

    return crud_controller()

# -----------------------------------------------------------------------------
def keyword():
    """ REST Controller """

    return crud_controller()

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
                            "restrict": restrict_e,
                            "url": URL(args=["[id]", "enable"]),
                            "_class": "action-btn",
                            },
                           {"label": s3_str(T("Disable")),
                            "restrict": restrict_d,
                            "url": URL(args = ["[id]", "disable"]),
                            "_class": "action-btn",
                            },
                           ]
            if not s3task._is_alive():
                # No Scheduler Running
                s3.actions += [{"label": s3_str(T("Parse")),
                                "restrict": restrict_d,
                                "url": URL(args = ["[id]", "parse"]),
                                "_class": "action-btn",
                                },
                               ]

        return output
    s3.postp = postp

    return crud_controller()

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

    return crud_controller(module, resourcename,
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

    return crud_controller("pr", resourcename)

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

    return crud_controller("pr", "contact")

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

    return crud_controller()

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

# =============================================================================
# Enabled only for testing:
#
@auth.requires_membership("ADMIN")
def tag():
    """ RESTful CRUD controller """

    return crud_controller()

# END ================================================================================
