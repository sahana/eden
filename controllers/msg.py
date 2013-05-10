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
    return dict(module_name=module_name)

# =============================================================================
def compose():
    """ Compose a Message which can be sent to a pentity via a number of different communications channels """

    return msg.compose()

# =============================================================================
def outbox():
    """ View the contents of the Outbox """

    if not auth.s3_logged_in():
        session.error = T("Requires Login!")
        redirect(URL(c="default", f="user", args="login"))

    tablename = "%s_%s" % (module, resourcename)
    table = s3db[tablename]

    table.message_id.label = T("Message")
    table.message_id.writable = False
    table.pe_id.readable = True
    table.pe_id.label = T("Recipient")

    # Subject works for Email but not SMS
    table.message_id.represent = lambda id: db(db.msg_log.id == id).select(db.msg_log.message, limitby=(0, 1)).first().message
    table.pe_id.represent = lambda id: s3db.pr_pentity_represent(id, default_label = "")

    # CRUD Strings
    s3.crud_strings[tablename] = Storage(
        title_list = T("View Outbox"),
        title_update = T("Edit Message"),
        label_list_button = T("View Outbox"),
        label_delete_button = T("Delete Message"),
        msg_record_modified = T("Message updated"),
        msg_record_deleted = T("Message deleted"),
        msg_list_empty = T("No Messages currently in Outbox")
    )

    add_btn = A(T("Compose"),
                _class="action-btn",
                _href=URL(f="compose")
                )

    s3db.configure(tablename, listadd=False)
    return s3_rest_controller(module, resourcename, add_btn = add_btn)

# =============================================================================
def log():
    """
        RESTful CRUD controller for the Master Message Log
        - all Inbound & Outbound Messages go here

        @ToDo: Field Labels for i18n
    """

    if not auth.s3_logged_in():
        session.error = T("Requires Login!")
        redirect(URL(c="default", f="user", args="login"))

    tablename = "%s_%s" % (module, resourcename)
    table = s3db[tablename]

    # CRUD Strings
    ADD_MESSAGE = T("Add Message")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_MESSAGE,
        title_display = T("Message Details"),
        title_list = T("Messages"),
        title_update = T("Edit message"),
        title_search = T("Search messages"),
        subtitle_create = T("Send new message"),
        label_list_button = T("List Messages"),
        label_create_button = ADD_MESSAGE,
        msg_record_created = T("Message added"),
        msg_record_modified = T("Message updated"),
        msg_record_deleted = T("Message deleted"),
        msg_list_empty = T("No messages in the system"))

    s3db.configure(tablename, listadd=False)
    return s3_rest_controller()

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
            # Set message log to actioned
            log = s3db.msg_log
            db(log.id == row.message_id).update(actioned=True)
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
                s3db.msg_log.insert(uuid=uuid, fromaddress=fromaddress,
                                    recipient=recipient, message=message,
                                    inbound=True)
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
def twitter_search():
    """ Controller to modify Twitter search queries """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def twitter_search_results():
    """
        Controller to view tweets from user saved search queries

        @ToDo: Action Button to update async
    """

    def prep(r):
        if r.interactive:
            table = r.table
            if not db(table.id > 0).select(table.id,
                                           limitby=(0, 1)).first():
                # Update results
                result = msg.receive_subscribed_tweets()
                if not result:
                    session.error = T("Need to configure Twitter Authentication")
                    redirect(URL(f="twitter_channel", args=[1, "update"]))
        return True
    s3.prep = prep

    s3db.configure("msg_twitter_search_results",
                   insertable=False,
                   editable=False)
    return s3_rest_controller()

# =============================================================================
@auth.s3_requires_membership(1)
def sms_outbound_gateway():
    """ SMS Outbound Gateway selection for the messaging framework """

    tablename = "%s_%s" % (module, resourcename)
    table = s3db[tablename]
    table.outgoing_sms_handler.label = T("Outgoing SMS Handler")
    table.outgoing_sms_handler.comment = DIV(DIV(_class="tooltip",
        _title="%s|%s" % (T("Outgoing SMS Handler"),
                          T("Selects what type of gateway to use for outbound SMS"))))
    # CRUD Strings
    s3.crud_strings[tablename] = Storage(
        title_update = T("Edit SMS Outbound Gateway"),
        msg_record_modified = T("SMS Outbound Gateway updated")
    )

    def prep(r):
        if r.http == "POST":
            # Go to the details page for the chosen SMS Gateway
            outgoing_sms_handler = request.post_vars.get("outgoing_sms_handler",
                                                         None)
            if outgoing_sms_handler == "WEB_API":
                s3db.configure(tablename,
                               update_next = URL(f="sms_webapi_channel",
                                                 args=[1, "update"]))
            elif outgoing_sms_handler == "SMTP":
                s3db.configure(tablename,
                               update_next = URL(f="sms_smtp_channel",
                                                 args=[1, "update"]))
            elif outgoing_sms_handler == "MODEM":
                s3db.configure(tablename,
                               update_next = URL(f="sms_modem_channel",
                                                 args=[1, "update"]))
            elif outgoing_sms_handler == "TROPO":
                s3db.configure(tablename,
                               update_next = URL(f="tropo_channel",
                                                 args=[1, "update"]))
            else:
                s3db.configure(tablename,
                               update_next = URL(args=[1, "update"]))
        return True
    s3.prep = prep

    s3db.configure(tablename,
                    deletable=False,
                    listadd=False)

    #response.menu_options = admin_menu_options
    return s3_rest_controller()

# -----------------------------------------------------------------------------
def channel():
    """
        RESTful CRUD controller for Channels
    """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def email_inbound_channel():
    """
        RESTful CRUD controller for Inbound Email channels
            - appears in the administration menu
    """

    if not auth.s3_has_role(ADMIN):
        session.error = UNAUTHORISED
        redirect(URL(f="index"))

    tablename = "msg_email_inbound_channel"
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
        title_display = T("Email Setting Details"),
        title_list = T("Email Settings"),
        title_create = T("Add Email Settings"),
        title_update = T("Edit Email Settings"),
        title_search = T("Search Email Settings"),
        label_list_button = T("View Email Settings"),
        label_create_button = T("Add Email Settings"),
        msg_record_created = T("Setting added"),
        msg_record_deleted = T("Email Setting deleted"),
        msg_list_empty = T("No Settings currently defined"),
        msg_record_modified = T("Email settings updated")
        )

    #response.menu_options = admin_menu_options
    s3db.configure(tablename, listadd=True, deletable=True)

    def postp(r, output):
        wtable = s3db.msg_workflow
        stable = s3db.scheduler_task
        mtable = r.table

        s3_action_buttons(r)
        query = (stable.enabled == False)
        records = db(query).select()
        rows = []
        for record in records:
            if "username" in record.vars:
                r = record.vars.split("\"username\":")[1]
                s = r.split("}")[0]
                s = s.split("\"")[1].split("\"")[0]

                record1 = db(mtable.username == s).select(mtable.id)
                if record1:
                    for rec in record1:
                        rows += [rec]

        restrict_e = [str(row.id) for row in rows]

        query = (stable.enabled == True              )
        records = db(query).select()
        rows = []
        for record in records:
            if "username" in record.vars:
                r = record.vars.split("\"username\":")[1]
                s = r.split("}")[0]
                s = s.split("\"")[1].split("\"")[0]

                record1 = db(mtable.username == s).select(mtable.id)
                if record1:
                    for rec in record1:
                        rows += [rec]

        restrict_d = [str(row.id) for row in rows]

        rows = []
        records = db(stable.id > 0).select()
        tasks = [record.vars for record in records]
        sources = []
        for task in tasks:
            if "username" in task:
                u = task.split("\"username\":")[1]
                v = u.split(",")[0]
                v = v.split("\"")[1]
                sources += [v]

        msettings = db(mtable.deleted == False).select(mtable.ALL)
        for msetting in msettings :
            if msetting.username:
                if (msetting.username not in sources):
                    if msetting:
                        rows += [msetting]

        restrict_a = [str(row.id) for row in rows]

        s3.actions = \
        s3.actions + [
                       dict(label=str(T("Enable")),
                            _class="action-btn",
                            url=URL(f="enable_email",
                                    args="[id]"),
                            restrict = restrict_e)
                       ]
        s3.actions.append(dict(label=str(T("Disable")),
                               _class="action-btn",
                               url = URL(f = "disable_email",
                                         args = "[id]"),
                               restrict = restrict_d)
                          )
        s3.actions.append(dict(label=str(T("Activate")),
                               _class="action-btn",
                               url = URL(f = "schedule_email",
                                         args = "[id]"),
                               restrict = restrict_a)
                          )
        return output
    s3.postp = postp

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def mcommons_channel():
    """
        RESTful CRUD controller for Mobile Commons SMS Channels
            - appears in the administration menu
    """

    if not auth.s3_has_role(ADMIN):
        session.error = UNAUTHORISED
        redirect(URL(f="index"))

    tablename = "msg_mcommons_channel"
    table = s3db[tablename]

    table.name.label = T("Account Name")
    table.name.comment = DIV(_class="tooltip",
                             _title="%s|%s" % (T("Account Name"),
                                               T("Name for your Twilio Account.")))

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
        title_create = T("Add Mobile Commons Settings"),
        title_update = T("Edit Mobile Commons Settings"),
        title_search = T("Search Mobile Commons Settings"),
        label_list_button = T("View Mobile Commons Settings"),
        label_create_button = T("Add Mobile Commons Settings"),
        msg_record_created = T("Mobile Commons Setting added"),
        msg_record_deleted = T("Mobile Commons Setting deleted"),
        msg_list_empty = T("No Mobile Commons Settings currently defined"),
        msg_record_modified = T("Mobile Commons settings updated")
        )

    def postp(r, output):
        if r.interactive:
            stable = s3db.scheduler_task
            table = r.table

            s3_action_buttons(r)
            query = (stable.enabled == False)
            records = db(query).select(stable.vars)
            rows = []
            for record in records:
                if "account" in record.vars:
                    r = record.vars.split("\"account\":")[1]
                    s = r.split("}")[0]
                    s = s.split("\"")[1].split("\"")[0]

                    record1 = db(table.campaign_id == s).select(table.id)
                    if record1:
                        for rec in record1:
                            rows += [rec]

            restrict_e = [str(row.id) for row in rows]

            query = (stable.enabled == True)
            records = db(query).select(stable.vars)
            rows = []
            for record in records:
                if "account" in record.vars:
                    r = record.vars.split("\"account\":")[1]
                    s = r.split("}")[0]
                    s = s.split("\"")[1].split("\"")[0]

                    record1 = db(table.account_name == s).select(table.id)
                    if record1:
                        for rec in record1:
                            rows += [rec]

            restrict_d = [str(row.id) for row in rows]

            records = db(stable.id > 0).select(stable.vars)
            tasks = [record.vars for record in records]
            sources = []
            for task in tasks:
                if "account" in task:
                    u = task.split("\"account\":")[1]
                    v = u.split(",")[0]
                    v = v.split("\"")[1]
                    sources += [v]

            settings = db(table.deleted == False).select(table.id,
                                                         table.name)
            rows = []
            for setting in settings :
                if setting.name:
                    if (setting.name not in sources):
                        if setting:
                            rows += [setting]

            restrict_a = [str(row.id) for row in rows]

            s3.actions = \
            s3.actions + [
                           dict(label=str(T("Enable")),
                                _class="action-btn",
                                url=URL(f="enable_mcommons_sms",
                                        args="[id]"),
                                restrict = restrict_e)
                           ]
            s3.actions.append(dict(label=str(T("Disable")),
                                   _class="action-btn",
                                   url = URL(f = "disable_mcommons_sms",
                                             args = "[id]"),
                                   restrict = restrict_d)
                              )
            s3.actions.append(dict(label=str(T("Activate")),
                                   _class="action-btn",
                                   url = URL(f = "schedule_mcommons_sms",
                                             args = "[id]"),
                                   restrict = restrict_a)
                              )
        return output
    s3.postp = postp

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def twilio_inbound_channel():
    """
        RESTful CRUD controller for Twilio SMS channels
            - appears in the administration menu
    """

    if not auth.s3_has_role(ADMIN):
        session.error = UNAUTHORISED
        redirect(URL(f="index"))

    tablename = "msg_twilio_inbound_channel"
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
        title_display = T("Twilio Setting Details"),
        title_list = T("Twilio Settings"),
        title_create = T("Add Twilio Settings"),
        title_update = T("Edit Twilio Settings"),
        title_search = T("Search Twilio Settings"),
        label_list_button = T("View Twilio Settings"),
        label_create_button = T("Add Twilio Settings"),
        msg_record_created = T("Twilio Setting added"),
        msg_record_deleted = T("Twilio Setting deleted"),
        msg_list_empty = T("No Twilio Settings currently defined"),
        msg_record_modified = T("Twilio settings updated")
        )

    def postp(r, output):

        stable = s3db.scheduler_task
        ttable = r.table

        s3_action_buttons(r)
        query = (stable.enabled == False)
        records = db(query).select()
        rows = []
        for record in records:
            if "account" in record.vars:
                r = record.vars.split("\"account\":")[1]
                s = r.split("}")[0]
                s = s.split("\"")[1].split("\"")[0]

                record1 = db(ttable.account_name == s).select(ttable.id)
                if record1:
                    for rec in record1:
                        rows += [rec]

        restrict_e = [str(row.id) for row in rows]

        query = (stable.enabled == True)
        records = db(query).select()
        rows = []
        for record in records:
            if "account" in record.vars:
                r = record.vars.split("\"account\":")[1]
                s = r.split("}")[0]
                s = s.split("\"")[1].split("\"")[0]

                record1 = db(ttable.account_name == s).select(ttable.id)
                if record1:
                    for rec in record1:
                        rows += [rec]

        restrict_d = [str(row.id) for row in rows]

        rows = []
        records = db(stable.id > 0).select()
        tasks = [record.vars for record in records]
        sources = []
        for task in tasks:
            if "account" in task:
                u = task.split("\"account\":")[1]
                v = u.split(",")[0]
                v = v.split("\"")[1]
                sources += [v]

        tsettings = db(ttable.deleted == False).select(ttable.ALL)
        for tsetting in tsettings :
            if tsetting.account_name:
                if (tsetting.account_name not in sources):
                    if tsetting:
                        rows += [tsetting]

        restrict_a = [str(row.id) for row in rows]

        s3.actions = \
        s3.actions + [
                       dict(label=str(T("Enable")),
                            _class="action-btn",
                            url=URL(f="enable_twilio_sms",
                                    args="[id]"),
                            restrict = restrict_e)
                       ]
        s3.actions.append(dict(label=str(T("Disable")),
                               _class="action-btn",
                               url = URL(f = "disable_twilio_sms",
                                         args = "[id]"),
                               restrict = restrict_d)
                          )
        s3.actions.append(dict(label=str(T("Activate")),
                               _class="action-btn",
                               url = URL(f = "schedule_twilio_sms",
                                         args = "[id]"),
                               restrict = restrict_a)
                          )
        return output
    s3.postp = postp

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def keyword():
    """ REST Controller """
    
    return s3_rest_controller()

# -----------------------------------------------------------------------------
def sender():
    """ REST Controller """
    
    return s3_rest_controller()

# -----------------------------------------------------------------------------
def workflow():
    """
        RESTful CRUD controller for workflows
            - appears in the administration menu
    """

    if not auth.s3_has_role(ADMIN):
        session.error = UNAUTHORISED
        redirect(URL(f="index"))

    table = s3db.msg_workflow
    table.source_task_id.label = T("Message Source")
    table.source_task_id.comment = DIV(_class="tooltip",
                                       _title="%s|%s" % (T("Message Source"),
                                                         T("This is the name of the username for the Inbound Message Source.")))
    table.workflow_task_id.label = T("Parsing Workflow")
    table.workflow_task_id.comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Parsing Workflow"),
                                                           T("This is the name of the parsing function used as a workflow.")))

    # CRUD Strings
    s3.crud_strings["msg_workflow"] = Storage(
        title_display = T("Setting Details"),
        title_list = T("Parser Settings"),
        title_create = T("Add Parser Settings"),
        title_update = T("Edit Parser Settings"),
        title_search = T("Search Parser Settings"),
        label_list_button = T("View Settings"),
        label_create_button = T("Add Parser Settings"),
        msg_record_created = T("Setting added"),
        msg_record_deleted = T("Parser Setting deleted"),
        msg_list_empty = T("No Settings currently defined"),
        msg_record_modified = T("Message Parser settings updated")
    )

    #s3db.configure("msg_workflow", listadd=True, deletable=True)

    def prep(r):
        if r.interactive:
            import inspect
            import sys

            parser = settings.get_msg_parser()
            module_name = "applications.%s.private.templates.%s.parser" % \
                (appname, parser)
            __import__(module_name)
            mymodule = sys.modules[module_name]
            S3Parsing = mymodule.S3Parsing()

            mtable = s3db.msg_email_inbound_channel
            ttable = s3db.msg_twilio_inbound_channel
            source_opts = []
            append = source_opts.append
            records = db(mtable.id > 0).select(mtable.username)
            for record in records:
                append(record.username)

            records = db(ttable.deleted == False).select(ttable.account_name)
            for record in records:
                append(record.account_name)

            # Dynamic lookup of the parsing functions in S3Parsing class.
            parsers = inspect.getmembers(S3Parsing, predicate=inspect.isfunction)
            parse_opts = []
            for parser in parsers:
                parse_opts += [parser[0]]

            r.table.source_task_id.requires = IS_IN_SET(source_opts, zero=None)
            r.table.workflow_task_id.requires = IS_IN_SET(parse_opts, \
                                                          zero=None)
        return True
    s3.prep = prep

    def postp(r, output):

        wtable = s3db.msg_workflow
        stable = db["scheduler_task"]

        s3_action_buttons(r)
        query = stable.enabled == False
        records = db(query).select()
        rows = []
        for record in records:
            if "workflow" and "source" in record.vars:
                r = record.vars.split("\"workflow\":")[1]
                s = r.split("}")[0]
                s = s.split("\"")[1].split("\"")[0]

                u = record.vars.split("\"source\":")[1]
                v = u.split(",")[0]
                v = v.split("\"")[1]

                query = (wtable.workflow_task_id == s) & \
                        (wtable.source_task_id == v)
                record1 = db(query).select(wtable.id)
                if record1:
                    for rec in record1:
                        rows += [rec]

        restrict_e = [str(row.id) for row in rows]

        query = stable.enabled == True
        records = db(query).select()
        rows = []
        for record in records:
            if "workflow" and "source" in record.vars:
                r = record.vars.split("\"workflow\":")[1]
                s = r.split("}")[0]
                s = s.split("\"")[1].split("\"")[0]

                u = record.vars.split("\"source\":")[1]
                v = u.split(",")[0]
                v = v.split("\"")[1]

                query = (wtable.workflow_task_id == s) & \
                        (wtable.source_task_id == v)
                record1 = db(query).select(wtable.id)
                if record1:
                    for rec in record1:
                        rows += [rec]

        restrict_d = [str(row.id) for row in rows]

        rows = []
        records = db(stable.id > 0).select(stable.vars)
        tasks = [record.vars for record in records]
        parser1 = []
        for task in tasks:
            if "workflow" in task:
                r = task.split("\"workflow\":")[1]
                s = r.split("}")[0]
                s = s.split("\"")[1].split("\"")[0]

                parser1 += [s]
        parser2 = []
        for task in tasks:
            if "source" in task:
                u = task.split("\"source\":")[1]
                v = u.split(",")[0]
                v = v.split("\"")[1]
                parser2 += [v]


        workflows = db(wtable.id > 0).select(wtable.id,
                                             wtable.workflow_task_id,
                                             wtable.source_task_id)

        for workflow in workflows :
            if workflow.workflow_task_id and workflow.source_task_id:
                if (workflow.workflow_task_id not in parser1) or \
                   (workflow.source_task_id not in parser2):
                    rows += [workflow]

        restrict_a = [str(row.id) for row in rows]

        s3.actions = \
        s3.actions + [
                       dict(label=str(T("Enable")),
                            _class="action-btn",
                            url=URL(f="enable_parser",
                                    args="[id]"),
                            restrict = restrict_e)
                      ]

        s3.actions.append(dict(label=str(T("Disable")),
                                        _class="action-btn",
                                        url = URL(f = "disable_parser",
                                                  args = "[id]"),
                                        restrict = restrict_d)
                                   )

        s3.actions.append(dict(label=str(T("Activate")),
                                        _class="action-btn",
                                        url = URL(f = "schedule_parser",
                                                  args = "[id]"),
                                        restrict = restrict_a)
                                   )

        return output
    s3.postp = postp

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def schedule_parser():
    """
        Schedule a Parsing Workflow
    """

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
def schedule_email():
    """
        Schedule Inbound Email
    """

    try:
        id = request.args[0]
    except:
        session.error = T("Source not specified!")
        redirect(URL(f="email_inbound_channel"))

    table = s3db.msg_email_inbound_channel
    record = db(table.id == id).select(table.username,
                                       limitby=(0, 1)).first()
    s3task.schedule_task("msg_email_poll",
                         vars={"username": record.username},
                         period=300,  # seconds
                         timeout=300, # seconds
                         repeats=0    # unlimited
                         )

    redirect(URL(f="email_inbound_channel"))

# -----------------------------------------------------------------------------
def schedule_mcommons_sms():
    """
        Schedules Mobile Commons Inbound SMS
    """

    try:
        id = request.args[0]
    except:
        session.error = T("Source not specified!")
        redirect(URL(f="mcommons_channel"))

    table = s3db.msg_mcommons_channel
    record = db(table.id == id).select(table.campaign_id,
                                       limitby=(0, 1)).first()
    s3task.schedule_task("msg_mcommons_poll",
                         vars={"campaign_id": record.campaign_id},
                         period=300,  # seconds
                         timeout=300, # seconds
                         repeats=0    # unlimited
                         )

    redirect(URL(f="mcommons_channel"))

# -----------------------------------------------------------------------------
def schedule_twilio_sms():
    """
        Schedules Twilio Inbound SMS
    """

    try:
        id = request.args[0]
    except:
        session.error = T("Source not specified!")
        redirect(URL(f="twilio_inbound_channel"))

    ttable = s3db.msg_twilio_inbound_channel
    record = db(table.id == id).select(table.account_name,
                                       limitby=(0, 1)).first()
    s3task.schedule_task("msg_twilio_poll",
                         vars={"account": record.account_name},
                         period=300,  # seconds
                         timeout=300, # seconds
                         repeats=0    # unlimited
                         )

    redirect(URL(f="twilio_inbound_channel"))

# -----------------------------------------------------------------------------
def disable_parser():
    """
        Disables different parsing workflows.
    """

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

# -----------------------------------------------------------------------------
def disable_email():
    """
        Disables different Email Sources.
    """

    try:
        id = request.args[0]
    except:
        session.error = T("Source not specified!")
        redirect(URL(f="email_inbound_channel"))

    stable = s3db.scheduler_task
    table = s3db.msg_email_inbound_channel

    settings = db(table.id == id).select(table.username,
                                         limitby=(0, 1)).first()
    records = db(stable.id > 0).select(stable.id,
                                       stable.vars)
    for record in records:
        if "username" in record.vars:
            r = record.vars.split("\"username\":")[1]
            s = r.split("}")[0]
            s = s.split("\"")[1].split("\"")[0]

            if (s == settings.username) :
                db(stable.id == record.id).update(enabled = False)

    redirect(URL(f="email_inbound_channel"))

# -----------------------------------------------------------------------------
def disable_mcommons_sms():
    """
        Disables Mobile Commons Inbound SMS
    """

    try:
        id = request.args[0]
    except:
        session.error = T("Source not specified!")
        redirect(URL(f="mcommons_channel"))

    stable = s3db.scheduler_task
    table = s3db.msg_mcommons_channel

    settings = db(table.id == id).select(table.campaign_id,
                                         limitby=(0, 1)).first()
    records = db(stable.id > 0).select(stable.id,
                                       stable.vars)
    for record in records:
        if "account" in record.vars:
            r = record.vars.split("\"account\":")[1]
            s = r.split("}")[0]
            s = s.split("\"")[1].split("\"")[0]

            if (s == settings.campaign_id) :
                db(stable.id == record.id).update(enabled = False)

    redirect(URL(f="mcommons_channel"))

# -----------------------------------------------------------------------------
def disable_twilio_sms():
    """
        Disables Twilio Inbound SMS
    """

    try:
        id = request.args[0]
    except:
        session.error = T("Source not specified!")
        redirect(URL(f="twilio_inbound_channel"))

    stable = s3db.scheduler_task
    table = s3db.msg_twilio_inbound_channel

    settings = db(table.id == id).select(table.account_name,
                                         limitby=(0, 1)).first()
    records = db(stable.id > 0).select(stable.id,
                                       stable.vars)
    for record in records:
        if "account" in record.vars:
            r = record.vars.split("\"account\":")[1]
            s = r.split("}")[0]
            s = s.split("\"")[1].split("\"")[0]

            if (s == settings.account_name) :
                db(stable.id == record.id).update(enabled = False)

    redirect(URL(f="twilio_inbound_channel"))

# -----------------------------------------------------------------------------
def enable_email():
    """
        Enables different Email Sources.
    """

    try:
        id = request.args[0]
    except:
        session.error = T("Source not specified!")
        redirect(URL(f="email_inbound_channel"))

    stable = s3db.scheduler_task
    table = s3db.msg_email_inbound_channel

    settings = db(table.id == id).select(table.username,
                                         limitby=(0, 1)).first()
    records = db(stable.id > 0).select(stable.id,
                                       stable.vars)
    for record in records:
        if "username" in record.vars:
            r = record.vars.split("\"username\":")[1]
            s = r.split("}")[0]
            s = s.split("\"")[1].split("\"")[0]

            if (s == settings.username) :
                db(stable.id == record.id).update(enabled = True)

    redirect(URL(f="email_inbound_channel"))

# -----------------------------------------------------------------------------
def enable_mcommons_sms():
    """
        Enable Mobile Commons Inbound SMS
    """

    try:
        id = request.args[0]
    except:
        session.error = T("Source not specified!")
        redirect(URL(f="mcommons_channel"))

    stable = s3db.scheduler_task
    table = s3db.msg_mcommons_channel

    settings = db(table.id == id).select(table.campaign_id,
                                         limitby=(0, 1)).first()
    records = db(stable.id > 0).select(stable.id,
                                       stable.vars)
    for record in records:
        if "account" in record.vars:
            r = record.vars.split("\"account\":")[1]
            s = r.split("}")[0]
            s = s.split("\"")[1].split("\"")[0]

            if (s == settings.campaign_id) :
                db(stable.id == record.id).update(enabled = True)

    redirect(URL(f="mcommons_channel"))

# -----------------------------------------------------------------------------
def enable_twilio_sms():
    """
        Enable Twilio Inbound SMS
    """

    try:
        id = request.args[0]
    except:
        session.error = T("Source not specified!")
        redirect(URL(f="twilio_inbound_channel"))

    stable = s3db.scheduler_task
    table = s3db.msg_twilio_inbound_channel

    settings = db(table.id == id).select(table.account_name,
                                         limitby=(0, 1)).first()
    records = db(stable.id > 0).select(stable.id,
                                       stable.vars)
    for record in records:
        if "account" in record.vars:
            r = record.vars.split("\"account\":")[1]
            s = r.split("}")[0]
            s = s.split("\"")[1].split("\"")[0]

            if (s == settings.account_name) :
                db(stable.id == record.id).update(enabled = True)

    redirect(URL(f="twilio_inbound_channel"))

# -----------------------------------------------------------------------------
def enable_parser():
    """
        Enables different parsing workflows.
    """

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
def inbox():
    """
        RESTful CRUD controller for the Inbox
        - all Inbound Messages will go here
        @ToDo: Complete (currently just MobileCommons) 
    """

    if not auth.s3_logged_in():
        session.error = T("Requires Login!")
        redirect(URL(c="default", f="user", args="login"))

    tablename = "msg_inbox"
    table = s3db[tablename]

    # CRUD Strings
    s3.crud_strings[tablename] = Storage(
        title_display = T("Inbox"),
        title_list = T("Inbox"),
        title_update = T("Edit Message"),
        title_search = T("Search Inbox"),
        label_list_button = T("View Messages"),
        msg_record_deleted = T("Message deleted"),
        msg_list_empty = T("Inbox empty"),
        msg_record_modified = T("Message updated")
        )

    s3db.configure(tablename, listadd=False)
    return s3_rest_controller(module, "")

# -----------------------------------------------------------------------------
def email_inbox():
    """
        RESTful CRUD controller for the Email Inbox
        - all Inbound Email Messages go here
        @ToDo: Deprecate
    """

    if not auth.s3_logged_in():
        session.error = T("Requires Login!")
        redirect(URL(c="default", f="user", args="login"))

    tablename = "msg_email_inbox"
    s3db.configure(tablename, listadd=False)
    return s3_rest_controller()

# -----------------------------------------------------------------------------
def twilio_inbox():
    """
        RESTful CRUD controller for the Twilio SMS Inbox
        - all Inbound SMS Messages from Twilio go here
    """

    if not auth.s3_logged_in():
        session.error = T("Requires Login!")
        redirect(URL(c="default", f="user", args="login"))

    tablename = "msg_twilio_inbox"
    table = s3db[tablename]

    # CRUD Strings
    s3.crud_strings[tablename] = Storage(
        title_display = T("Twilio SMS Inbox"),
        title_list = T("Twilio SMS Inbox"),
        title_update = T("Edit SMS Message"),
        title_search = T("Search Twilio SMS Inbox"),
        label_list_button = T("View Twilio SMS"),
        msg_record_deleted = T("Twilio SMS deleted"),
        msg_list_empty = T("Twilio SMS Inbox empty"),
        msg_record_modified = T("Twilio SMS updated")
        )

    s3db.configure(tablename, listadd=False)
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
    ADD_SETTING = T("Add Setting")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_SETTING,
        title_display = T("Setting Details"),
        title_list = T("Settings"),
        title_update = T("Edit Modem Settings"),
        title_search = T("Search Settings"),
        label_list_button = T("View Settings"),
        label_create_button = ADD_SETTING,
        msg_record_created = T("Setting added"),
        msg_record_modified = T("Modem settings updated"),
        msg_record_deleted = T("Setting deleted"),
        msg_list_empty = T("No Settings currently defined")
    )

    s3db.configure(tablename,
                    #deletable=False,
                    #listadd=False,
                    #update_next = URL(args=[1, "update"])
                    )
    #response.menu_options = admin_menu_options
    return s3_rest_controller()


#------------------------------------------------------------------------------
@auth.s3_requires_membership(1)
def sms_smtp_channel():
    """
        RESTful CRUD controller for SMTP to SMS Outbound channels
        - appears in the administration menu
        Only 1 of these normally in existence
            @ToDo: Don't enforce
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
    s3.crud_strings[tablename] = Storage(
        title_update = T("Edit SMTP to SMS Settings"),
        msg_record_modified = T("SMTP to SMS settings updated"),
    )

    s3db.configure(tablename,
                    deletable=False,
                    listadd=False,
                    update_next = URL(args=[1, "update"]))

    return s3_rest_controller()

#------------------------------------------------------------------------------
@auth.s3_requires_membership(1)
def sms_webapi_channel():
    """
        RESTful CRUD controller for Web API channels
        - appears in the administration menu
        Only 1 of these normally in existence
            @ToDo: Don't enforce
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
        title_update = T("Edit Web API Settings"),
        msg_record_modified = T("Web API settings updated"),
    )

    s3db.configure(tablename,
                   deletable=False,
                   listadd=False,
                   update_next = URL(args=[1, "update"]))

    return s3_rest_controller()

# -----------------------------------------------------------------------------
@auth.s3_requires_membership(1)
def tropo_channel():
    """
        RESTful CRUD controller for Tropo channels
        - appears in the administration menu
        Only 1 of these normally in existence
            @ToDo: Don't enforce
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
        title_update = T("Edit Tropo Settings"),
        msg_record_modified = T("Tropo settings updated"),
    )

    s3db.configure(tablename,
                    deletable=False,
                    listadd=False,
                    update_next = URL(args=[1, "update"]))

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

    try:
        import tweepy
    except:
        session.error = T("tweepy module not available within the running Python - this needs installing for non-Tropo Twitter support!")
        redirect(URL(c="admin", f="index"))

    tablename = "%s_%s" % (module, resourcename)
    table = s3db[tablename]

    # CRUD Strings
    s3.crud_strings[tablename] = Storage(
        title_update = T("Authenticate system's Twitter account"),
        msg_record_modified = T("System's Twitter account updated"),
    )

    def prep(r):
        oauth_consumer_key = settings.msg.twitter_oauth_consumer_key
        oauth_consumer_secret = settings.msg.twitter_oauth_consumer_secret
        if not (oauth_consumer_key and oauth_consumer_secret):
            session.error = T("You should edit Twitter settings in models/000_config.py")
            return True
        oauth = tweepy.OAuthHandler(oauth_consumer_key,
                                    oauth_consumer_secret)

        #tablename = "%s_%s" % (module, resourcename)
        #table = db[tablename]
        table = r.table

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
            table.pin.readable = True
            table.pin.label = T("PIN number from Twitter (leave empty to detach account)")
            table.pin.value = ""
            table.twitter_account.label = T("Current Twitter account")
            return True
        else:
            # Not showing form, no need for pin
            table.pin.readable = False
            table.pin.label = T("PIN") # won't be seen
            table.pin.value = ""       # but let's be on the safe side
        return True
    s3.prep = prep

    # Post-process
    def user_postp(r, output):
        if r.interactive and isinstance(output, dict):
            if r.http == "GET" and r.method in ("create", "update"):
                rheader = A(T("Collect PIN from Twitter"),
                            _href=session.s3.twitter_oauth_url,
                            _target="_blank")
                output["rheader"] = rheader
        return output
    s3.postp = user_postp

    s3db.configure(tablename,
                   listadd=False,
                   deletable=False)

    return s3_rest_controller(deduplicate="", list_btn="")

# -----------------------------------------------------------------------------
def basestation():
    """ RESTful CRUD controller for Base Stations """

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

    return s3_rest_controller(module, resourcename, rheader=s3db.pr_rheader)

# -----------------------------------------------------------------------------
def group_membership():
    """ RESTful CRUD controller """

    if auth.is_logged_in() or auth.basic():
        pass
    else:
        redirect(URL(c="default", f="user", args="login",
        vars={"_next":URL(c="msg", f="group_membership")}))

    table = s3db.pr_group_membership

    # Hide unnecessary fields
    table.description.readable = table.description.writable = False
    table.comments.readable = table.comments.writable = False
    table.group_head.readable = table.group_head.writable = False

    return s3_rest_controller("pr", resourcename)

# -----------------------------------------------------------------------------
def contact():
    """ Allows the user to add, update and delete their contacts """

    table = s3db.pr.contact
    ptable = s3db.pr_person

    if auth.is_logged_in() or auth.basic():
        s3.filter = (table.pe_id == auth.user.pe_id)
    else:
        redirect(URL(c="default", f="user", args="login",
            vars={"_next":URL(c="msg", f="contact")}))

    # These fields will be populated automatically
    table.name.writable = table.name.readable = False
    table.pe_id.writable = table.pe_id.readable = False
    table.person_name.writable = table.person_name.readable = False
    table.id.writable = False
    #table.id.readable = False

    def msg_contact_onvalidation(form):
        """ This onvalidation method adds the person id to the record """
        if auth.user:
            form.vars.pe_id = auth.user.pe_id

    s3db.configure(table._tablename,
                    onvalidation=msg_contact_onvalidation)

    def msg_contact_restrict_access(r):
        """ The following restricts update and delete access to contacts not owned by the user """
        if r.id :
            pe_id = r.record.pe_id
            if auth.user and auth.user.pe_id == pe_id:
                return True
            else:
                session.error = T("Access denied")
                return dict(bypass = True, output = redirect(URL(r=request)))
        else:
            return True
    s3.prep = msg_contact_restrict_access

    response.menu_options = []
    return s3_rest_controller("pr", resourcename)

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
    type = request.get_vars.get("type", None)
    if value:
        # Call the search function
        if type:
            items = person_search(value, type)
        else:
            items = person_search(value)
        # Encode in JSON
        item = json.dumps(items)
        response.headers["Content-Type"] = "application/json"
        return item
    return

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

# =============================================================================
# Enabled only for testing:
#
@auth.s3_requires_membership(1)
def tag():
    """ RESTful CRUD controller """

    tablename = "%s_%s" % (module, resourcename)
    table = s3db[tablename]

    # Load all models
    s3db.load_all_models()
    table.resource.requires = IS_IN_SET(db.tables)

    s3db.configure(tablename, listadd=False)
    return s3_rest_controller()

# -----------------------------------------------------------------------------
# Send Outbound Messages (was for being called via cron, now useful for debugging)
# -----------------------------------------------------------------------------
def process_email_outbox():
    """ Send Pending Email Messages """

    msg.process_outbox(contact_method = "EMAIL")
    return

# -----------------------------------------------------------------------------
def process_sms_outbox():
    """ Send Pending SMS Messages """

    msg.process_outbox(contact_method = "SMS")
    return

# -----------------------------------------------------------------------------
def process_twitter_outbox():
    """ Send Pending Twitter Messages """

    msg.process_outbox(contact_method = "TWITTER")
    return

# -----------------------------------------------------------------------------
# Collect Inbound Messages
# -----------------------------------------------------------------------------
def poll_mcommons_inbox():
    """ Collect Inbound Mobile Commons Messages """

    try:
        campaign_id = request.args[0]
    except:
        session.error = T("Need to specify campaign_id")
        redirect(URL(f="mcommons_channel"))

    msg.mcommons_poll(campaign_id = campaign_id)

    redirect(URL(f="inbox"))

# -----------------------------------------------------------------------------
def poll_twilio_inbox():
    """ Collect Inbound Twilio Messages """

    try:
        account_name = request.args[0]
    except:
        session.error = T("Need to specify account name")
        redirect(f="")

    msg.twilio_poll(account_name = account_name)

    redirect(URL(f="twilio_inbox"))

# END ================================================================================
