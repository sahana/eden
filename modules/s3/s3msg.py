# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

""" Messaging API

    API to send messages:
        - currently SMS, Email & Twitter

    Messages get sent to the Outbox (& Log)
    From there, Cron tasks collect them & send them

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

__all__ = ["S3Msg",
           "S3Compose",
           ]

import base64
import datetime
import string
import urllib
import urllib2

try:
    import json # try stdlib (Python 2.6)
except ImportError:
    try:
        import simplejson as json # try external module
    except:
        import gluon.contrib.simplejson as json # fallback to pure-Python module

try:
    from lxml import etree
except ImportError:
    print >> sys.stderr, "ERROR: lxml module needed for XML handling"
    raise

from gluon import current, redirect
from gluon.html import *
# @ToDo: deprecate these 2
from gluon.sqlhtml import SQLTABLE
from gluon.tools import Crud

from s3codec import S3Codec
from s3crud import S3CRUD
from s3forms import S3SQLDefaultForm
from s3utils import s3_debug
from s3validators import IS_IN_SET, IS_ONE_OF, IS_ONE_OF_EMPTY

IDENTITYTRANS = ALLCHARS = string.maketrans("", "")
NOTPHONECHARS = ALLCHARS.translate(IDENTITYTRANS, string.digits)
NOTTWITTERCHARS = ALLCHARS.translate(IDENTITYTRANS,
                                     "%s%s_" % (string.digits, string.letters))

TWITTER_MAX_CHARS = 140
TWITTER_HAS_NEXT_SUFFIX = u' \u2026'
TWITTER_HAS_PREV_PREFIX = u'\u2026 '

# =============================================================================
class S3Msg(object):
    """ Messaging framework """

    def __init__(self,
                 modem=None):

        T = current.T
        self.modem = modem

        # http://docs.oasis-open.org/emergency/edxl-have/cs01/xPIL-types.xsd
        # <xs:simpleType name="CommunicationMediaTypeList">
        #  <xs:enumeration value="Cellphone"/>
        #  <xs:enumeration value="Fax"/>
        #  <xs:enumeration value="Pager"/>
        #  <xs:enumeration value="Telephone"/>
        #  <xs:enumeration value="VOIP"/>
        # <xs:simpleType name="ElectronicAddressIdentifierTypeList">
        #  <xs:enumeration value="AIM"/>
        #  <xs:enumeration value="EMAIL"/>
        #  <xs:enumeration value="GOOGLE"/>
        #  <xs:enumeration value="GIZMO"/>
        #  <xs:enumeration value="ICQ"/>
        #  <xs:enumeration value="JABBER"/>
        #  <xs:enumeration value="MSN"/>
        #  <xs:enumeration value="SIP"/>
        #  <xs:enumeration value="SKYPE"/>
        #  <xs:enumeration value="URL"/>
        #  <xs:enumeration value="XRI"/>
        #  <xs:enumeration value="YAHOO"/>

        # @ToDo: Remove the T from the init() & T upon usage instead

        MOBILE = current.deployment_settings.get_ui_label_mobile_phone()
        # Full range of contact options
        self.CONTACT_OPTS = {
                "EMAIL":       T("Email"),
                "FACEBOOK":    T("Facebook"),
                "FAX":         T("Fax"),
                "HOME_PHONE":  T("Home phone"),
                "RADIO":       T("Radio Callsign"),
                "RSS":         T("RSS Feed"),
                "SKYPE":       T("Skype"),
                "SMS":         MOBILE,
                "TWITTER":     T("Twitter"),
                #"XMPP":       "XMPP",
                #"WEB":        T("Website"),
                "WORK_PHONE":  T("Work phone"),
                "OTHER":       T("other")
            }

        # Those contact options to which we can send notifications
        # NB Coded into hrm_map_popup & s3.msg.js
        self.MSG_CONTACT_OPTS = {
                "EMAIL":   T("Email"),
                "SMS":     MOBILE,
                "TWITTER": T("Twitter"),
                #"XMPP":   "XMPP",
            }

        # SMS Gateways
        self.GATEWAY_OPTS = {
                "MODEM":   T("Modem"),
                "SMTP":    T("SMTP"),
                "TROPO":   T("Tropo"),
                # Currently only available for Inbound
                #"TWILIO":  T("Twilio"),
                "WEB_API": T("Web API"),
            }

    # -------------------------------------------------------------------------
    @staticmethod
    def sanitise_phone(phone):
        """
            Strip out unnecessary characters from the string:
            +()- & space
        """

        settings = current.deployment_settings
        default_country_code = settings.get_L10n_default_country_code()

        clean = phone.translate(IDENTITYTRANS, NOTPHONECHARS)

        # If number starts with a 0 then need to remove this & add the country code in
        if clean[0] == "0":
            # Add default country code
            if default_country_code == 39:
                # Italy keeps 0 after country code
                clean = "%s%s" % (default_country_code, clean)
            else:
                clean = "%s%s" % (default_country_code,
                                  string.lstrip(clean, "0"))

        return clean

    # =========================================================================
    # Inbound Messages
    # =========================================================================
    @staticmethod
    def receive_msg(subject="",
                    message="",
                    sender="",
                    fromaddress="",
                    system_generated = False,
                    pr_message_method = "EMAIL",
                   ):
        """
            Function to call to drop incoming messages into msg_log
        """

        db = current.db
        s3db = current.s3db

        try:
            message_log_id = s3db.msg_log.insert(inbound = True,
                                                 subject = subject,
                                                 message = message,
                                                 sender  = sender,
                                                 fromaddress = fromaddress,
                                                )
        except:
            return False
            #2) This is not transaction safe - power failure in the middle will cause no message in the outbox
        try:
            s3db.msg_channel.insert(message_id = message_log_id,
                                    pr_message_method = pr_message_method)
        except:
            return False
        # Explicitly commit DB operations when running from Cron
        db.commit()
        return True

    # -------------------------------------------------------------------------
    @staticmethod
    def parse_import(workflow, source):
        """
           Parse Inbound Messages
        """

        from s3parser import S3Parsing

        db = current.db
        s3db = current.s3db
        ptable = s3db.msg_parsing_status
        mtable = s3db.msg_message
        wtable = s3db.msg_workflow
        otable = s3db.msg_outbox
        ctable = s3db.pr_contact
        parser = S3Parsing.parser
        linsert = ltable.insert
        oinsert = otable.insert
        contact_method = ctable.contact_method
        value = ctable.value
        lid = ltable.id

        query = (wtable.workflow_task_id == workflow) & \
                (wtable.source_task_id == source)
        records = db(query).select(wtable.source_task_id)
        reply = ""
        wflow = ""
        contact = ""
        for record in records:
            query = (ptable.is_parsed == False) & \
                    (ptable.source_task_id == record.source_task_id)
            rows = db(query).select()

            for row in rows:
                messages = db(mtable.id == row.message_id).select()
                message = row.body
                try:
                    contact = row.sender.split("<")[1].split(">")[0]
                    query = (contact_method == "EMAIL") & \
                            (value == contact)
                    pe_ids = db(query).select(ctable.pe_id)
                    if not pe_ids:
                        query = (contact_method == "SMS") & \
                                (value == contact)
                        pe_ids = db(query).select(ctable.pe_id)

                except:
                    raise ValueError("Source not defined!")

                reply = parser(workflow, message, contact)
                if reply:
                    db(lid == row.id).update(reply = reply,
                                                   is_parsed = True)
                else:
                    flow = db(lid == row.id).select(ltable.reply,
                                                    limitby=(0, 1)).first()
                    try:
                        wflow = flow.reply.split("Workflow:")[1].split(".")[0]
                    except:
                        pass
                    if wflow == workflow:
                        reply = "Send help to see how to respond!"
                        db(lid == row.id).update(reply = reply,
                                                 is_parsed = True)
                    else:
                        reply = "Workflow:%s. Send help to see how to respond!" \
                                % workflow
                        db(lid == row.id).update(reply = flow.reply + reply)
                        db.commit()
                        return
                reply = linsert(recipient = row.sender,
                                      subject ="Parsed Reply",
                                      message = reply)

                if pe_ids:
                    for pe_id in pe_ids:
                        oinsert(message_id = reply.id,
                                      address = contact, pe_id = pe_id.pe_id)
                db.commit()

        return

    # =========================================================================
    # Outbound Messages
    # =========================================================================
    def compose(self,
                type = "SMS",
                recipient_type = None,
                recipient = None,
                #hide = True,
                subject = "",
                message = "",
                url = None,
                formid = None,
                ):
        """
            Form to Compose a Message

            @param type: The default message type: None, EMAIL, SMS or TWITTER
            @param recipient_type: Send to Persons or Groups? (pr_person or pr_group)
            @param recipient: The pe_id of the person/group to send the message to
                              - this can also be set by setting one of
                                (in priority order, if multiple found):
                                request.vars.pe_id
                                request.vars.person_id @ToDo
                                request.vars.group_id  @ToDo
                                request.vars.hrm_id    @ToDo
            @param subject: The default subject text (for Emails)
            @param message: The default message text
            @param url: Redirect to the specified URL() after message sent
            @param formid: If set, allows multiple forms open in different tabs
        """

        T = current.T
        request = current.request
        vars = request.vars
        db = current.db
        s3db = current.s3db
        ltable = s3db.msg_log
        otable = s3db.msg_outbox

        if not url:
            url = URL(c="msg", f="compose")

        auth = current.auth
        if auth.is_logged_in() or auth.basic():
            pass
        else:
            redirect(URL(c="default", f="user", args="login",
                         vars={"_next" : url}))

        ltable.subject.default = subject
        ltable.message.default = message

        otable.pr_message_method.default = type

        ltable.pe_id.writable = ltable.pe_id.readable = False
        ltable.sender.writable = ltable.sender.readable = False
        ltable.fromaddress.writable = ltable.fromaddress.readable = False
        ltable.verified.writable = ltable.verified.readable = False
        ltable.verified_comments.writable = ltable.verified_comments.readable = False
        ltable.actioned.writable = ltable.actioned.readable = False
        ltable.actionable.writable = ltable.actionable.readable = False
        ltable.actioned_comments.writable = ltable.actioned_comments.readable = False
        ltable.inbound.writable = ltable.inbound.readable = False
        ltable.is_parsed.writable = ltable.is_parsed.readable = False
        ltable.reply.writable = ltable.reply.readable = False
        ltable.source_task_id.writable = ltable.source_task_id.readable = False

        ltable.subject.label = T("Subject")
        ltable.message.label = T("Message")
        #ltable.priority.label = T("Priority")

        if not recipient:
            if "pe_id" in vars:
                recipient = vars.pe_id
            elif "person_id" in vars:
                # @ToDo
                pass
            elif "group_id" in vars:
                # @ToDo
                pass
            elif "human_resource.id" in vars:
                # @ToDo
                pass

        if recipient:
            otable.pe_id.default = recipient
            ltable.pe_id.default = recipient
            ltable.pe_id.requires = IS_ONE_OF_EMPTY(db,
                                                    "pr_pentity.pe_id",
                                                    multiple=True)
            # Restrict message options to those available for the entity
            petable = s3db.pr_pentity
            entity_type = db(petable.pe_id == recipient).select(petable.instance_type,
                                                                limitby=(0, 1)
                                                                ).first().instance_type
            if entity_type == "pr_person":
                all_contact_opts = self.MSG_CONTACT_OPTS
                contact_method_opts = {}
                ctable = s3db.pr_contact
                query = (ctable.deleted != True) & \
                        (ctable.pe_id == recipient)
                rows = db(query).select(ctable.contact_method)
                for row in rows:
                    if row.contact_method in all_contact_opts:
                        contact_method_opts[row.contact_method] = all_contact_opts[row.contact_method]
                if not contact_method_opts:
                    current.session.error = T("There are no contacts available for this person!")
                    controller = request.controller
                    vars = request.get_vars
                    if controller == "hrm":
                        url = URL(c="hrm", f="person", args="contacts",
                                  vars={"group": "staff",
                                        "human_resource.id": vars.get("human_resource.id")})
                    elif controller == "vol":
                        url = URL(c="vol", f="person", args="contacts",
                                  vars={"group": "volunteer",
                                        "human_resource.id": vars.get("human_resource.id")})
                    elif controller == "member":
                        url = URL(c="member", f="person", args="contacts",
                                  vars={"membership.id": vars.get("membership.id")})
                    else:
                        # @ToDo: Lookup the type
                        url = URL(f="index")
                    redirect(url)
                otable.pr_message_method.requires = IS_IN_SET(contact_method_opts,
                                                              zero=None)
                if type not in contact_method_opts:
                    otable.pr_message_method.default = contact_method_opts.popitem()[0]
            #elif entity_type = "pr_group":
                # @ToDo: Loop through members
        else:
            if recipient_type:
                # Filter by Recipient Type
                otable.pe_id.requires = IS_ONE_OF(db,
                                                  "pr_pentity.pe_id",
                                                  # Breaks PG
                                                  #orderby="instance_type",
                                                  filterby="instance_type",
                                                  filter_opts=(recipient_type,))
            otable.pe_id.comment = DIV(_class="tooltip",
                                       _title="%s|%s" % \
                (T("Recipients"),
                 T("Please enter the first few letters of the Person/Group for the autocomplete.")))
        otable.pe_id.writable = True
        otable.pe_id.label = T("Recipient(s)")

        def compose_onvalidation(form):
            """
                Set the sender
                Route the message
            """

            if not vars.pe_id:
                current.session.error = T("Please enter the recipient(s)")
                redirect(url)
            if auth.user:
                sender_pe_id = auth.user.pe_id
            else:
                return
            if self.send_by_pe_id(vars.pe_id,
                                  vars.subject,
                                  vars.message,
                                  sender_pe_id,
                                  vars.pr_message_method):
                current.session.confirmation = T("Check outbox for the message status")
                redirect(url)
            else:
                current.session.error = T("Error in message:%s") % \
                                            current.session.error
                redirect(url)

        # Source forms
        sqlform = S3SQLDefaultForm()
        logform = sqlform(request=request,
                          resource=s3db.resource("msg_log"),
                          onvalidation=compose_onvalidation,
                          message="Message Sent",
                          format="html")
        outboxform = sqlform(request=request,
                             resource=s3db.resource("msg_outbox"),
                             message="Message Sent",
                             format="html")

        # Shortcuts
        lcustom = logform.custom
        ocustom = outboxform.custom

        pe_row = TR(TD(LABEL(ocustom.label.pe_id)),
                    _id="msg_outbox_pe_id__row")
        if recipient:
            ocustom.widget.pe_id["_class"] = "hide"
            pe_row.append(TD(ocustom.widget.pe_id,
                             s3db.pr_pentity_represent(recipient)))
        else:
            pe_row.append(TD(INPUT(_id="dummy", _class="ac_input", _size="50"),
                             ocustom.widget.pe_id))
            pe_row.append(TD(ocustom.comment.pe_id))

        # Build a custom form from the 2 source forms
        form = DIV( lcustom.begin,
                    TABLE(
                        TBODY(
                            TR(TD(LABEL(ocustom.label.pr_message_method)),
                               TD(ocustom.widget.pr_message_method),
                               TD(ocustom.comment.pr_message_method),
                               _id="msg_outbox_pr_message_method__row"
                            ),
                            pe_row,
                            TR(TD(LABEL(lcustom.label.subject)),
                               TD(lcustom.widget.subject),
                               TD(lcustom.comment.subject),
                               _id="msg_log_subject__row"
                            ),
                            TR(TD(LABEL(lcustom.label.message)),
                               TD(lcustom.widget.message),
                               TD(lcustom.comment.message),
                               _id="msg_log_message__row"
                            ),
                            # TR(TD(LABEL(lcustom.label.priority)),
                               # TD(lcustom.widget.priority),
                               # TD(lcustom.comment.priority),
                               # _id="msg_log_priority__row"
                            # ),
                            TR(TD(),
                               TD(INPUT(_type="submit",
                                        _value=T("Send message"),
                                        _id="dummy_submit")),
                               _id="submit_record__row"
                            ),
                        )
                    ),
                    lcustom.end)

        # Control the Javascript in static/scripts/S3/s3.msg.js
        if not recipient:
            s3 = current.response.s3
            if recipient_type:
                s3.js_global.append('''S3.msg_search_url="%s"''' % \
                                    URL(c="msg", f="search",
                                        vars={"type":recipient_type}))
            else:
                s3.js_global.append('''S3.msg_search_url="%s"''' % \
                                    URL(c="msg", f="search"))

            s3.jquery_ready.append('''s3_msg_ac_pe_input()''')

        # Default title
        # - can be overridden by the calling function
        title = T("Send Message")

        return dict(form = form,
                    title = title)

    # -------------------------------------------------------------------------
    @staticmethod
    def send_by_pe_id(pe_id,
                      subject="",
                      message="",
                      sender_pe_id = None,
                      pr_message_method = "EMAIL",
                      sender="",
                      fromaddress="",
                      system_generated = False):
        """
            Send a single message to a Person Entity (or list thereof)

            @ToDo: pr_message_method = ALL
                - look up the pr_contact options available for the pe & send via all

            @ToDo: This is not transaction safe
              - power failure in the middle will cause no message in the outbox
        """

        db = current.db
        s3db = current.s3db

        # Put the Message in the Log
        table = s3db.msg_log
        try:
            message_log_id = table.insert(pe_id = sender_pe_id,
                                          subject = subject,
                                          message = message,
                                          sender  = sender,
                                          fromaddress = fromaddress)
        except:
            return False

        # Place the Message in the OutBox
        table = s3db.msg_outbox
        if isinstance(pe_id, list):
            listindex = 0
            for id in pe_id:
                try:
                    table.insert(message_id = message_log_id,
                                 pe_id = id,
                                 pr_message_method = pr_message_method,
                                 system_generated = system_generated)
                    listindex = listindex + 1
                except:
                    return listindex
        else:
            try:
                table.insert(message_id = message_log_id,
                             pe_id = pe_id,
                             pr_message_method = pr_message_method,
                             system_generated = system_generated)
            except:
                return False

        # Process OutBox async
        current.s3task.async("msg_process_outbox",
                             args=[pr_message_method])

        if current.session.error:
            return False
        else:
            return True

    # -------------------------------------------------------------------------
    def process_outbox(self,
                       contact_method="EMAIL"):
        """
            Send Pending Messages from Outbox.
            If succesful then move from Outbox to Sent.
            Can be called from Cron

            @ToDo: contact_method = "ALL"
        """

        db = current.db
        s3db = current.s3db

        if contact_method == "SMS":
            table = s3db.msg_sms_outbound_gateway
            settings = db(table.id > 0).select(table.outgoing_sms_handler,
                                               limitby=(0, 1)).first()
            if not settings:
                raise ValueError("No SMS handler defined!")
            outgoing_sms_handler = settings.outgoing_sms_handler

        def dispatch_to_pe_id(pe_id):
            table = s3db.pr_contact
            query = (table.pe_id == pe_id) & \
                    (table.contact_method == contact_method) & \
                    (table.deleted == False)
            recipient = db(query).select(table.value,
                                         orderby = table.priority,
                                         limitby=(0, 1)).first()
            if recipient:
                if contact_method == "EMAIL":
                    return self.send_email(recipient.value,
                                           subject,
                                           message)
                elif contact_method == "SMS":
                    if outgoing_sms_handler == "WEB_API":
                        return self.send_sms_via_api(recipient.value,
                                                     message)
                    elif outgoing_sms_handler == "SMTP":
                        return self.send_sms_via_smtp(recipient.value,
                                                       message)
                    elif outgoing_sms_handler == "MODEM":
                        return self.send_sms_via_modem(recipient.value,
                                                       message)
                    elif outgoing_sms_handler == "TROPO":
                        # NB This does not mean the message is sent
                        return self.send_text_via_tropo(row.id,
                                                        message_id,
                                                        recipient.value,
                                                        message)
                    else:
                        return False

                elif contact_method == "TWITTER":
                    return self.send_tweet(message, recipient.value)
            return False

        table = s3db.msg_outbox
        ltable = s3db.msg_log
        ptable = s3db.pr_person
        petable = s3db.pr_pentity

        query = (table.status == 1) & \
                (table.pr_message_method == contact_method)
        rows = db(query).select()
        chainrun = False # Used to fire process_outbox again - Used when messages are sent to groups
        for row in rows:
            status = True
            message_id = row.message_id
            query = (ltable.id == message_id)
            logrow = db(query).select(limitby=(0, 1)).first()
            if not logrow:
                s3_debug("s3msg", "logrow not found")
                continue
            # Get message from msg_log
            message = logrow.message
            subject = logrow.subject
            sender_pe_id = logrow.pe_id
            # Determine list of users
            entity = row.pe_id
            query = petable.id == entity
            entity_type = db(query).select(petable.instance_type,
                                           limitby=(0, 1)).first()
            if entity_type:
                entity_type = entity_type.instance_type
            else:
                s3_debug("s3msg", "Entity type unknown")

            if entity_type == "pr_group":
                # Take the entities of it and add in the messaging queue - with
                # sender as the original sender and marks group email processed
                # Set system generated = True
                table3 = s3db.pr_group
                query = (table3.pe_id == entity)
                group_id = db(query).select(table3.id,
                                            limitby=(0, 1)).first().id
                table4 = s3db.pr_group_membership
                query = (table4.group_id == group_id)
                recipients = db(query).select(table4.person_id)
                for recipient in recipients:
                    person_id = recipient.person_id
                    query = (ptable.id == person_id)
                    pe_id = db(query).select(ptable.pe_id,
                                             limitby=(0, 1)).first().pe_id
                    table.insert(message_id = message_id,
                                 pe_id = pe_id,
                                 pr_message_method = contact_method,
                                 system_generated = True)
                status = True
                chainrun = True

            elif entity_type == "org_organisation":
                # Take the entities of it and add in the messaging queue - with
                # sender as the original sender and marks group email processed
                # Set system generated = True
                table3 = s3db.org_organisation
                query = (table3.pe_id == entity)
                org_id = db(query).select(table3.id,
                                          limitby=(0, 1)).first().id
                table4 = s3db.hrm_human_resource
                query = (table4.organisation_id == org_id)
                recipients = db(query).select(table4.person_id)
                for recipient in recipients:
                    person_id = recipient.person_id
                    uery = (ptable.id == person_id)
                    pe_id = db(query).select(ptable.pe_id,
                                             limitby=(0, 1)).first().pe_id
                    table.insert(message_id = message_id,
                                 pe_id = pe_id,
                                 pr_message_method = contact_method,
                                 system_generated = True)
                status = True
                chainrun = True

            if entity_type == "pr_person":
                # Person
                status = dispatch_to_pe_id(entity)

            if status:
                # Update status to sent in Outbox
                db(table.id == row.id).update(status=2)
                # Set message log to actioned
                db(ltable.id == message_id).update(actioned=True)
                # Explicitly commit DB operations when running from Cron
                db.commit()

        if chainrun :
            self.process_outbox(contact_method)

        return


    # -------------------------------------------------------------------------
    # Send Email
    # -------------------------------------------------------------------------
    def send_email(self,
                   to,
                   subject,
                   message,
                   attachments=None,
                   cc=None,
                   bcc=None,
                   reply_to=None,
                   sender="%(sender)s",
                   encoding="utf-8"):
        """
            Function to send Email
            - simple Wrapper over Web2Py's Email API
        """

        if not to:
            return False

        settings = current.deployment_settings
        default_sender = settings.get_mail_sender()
        if not default_sender:
            s3_debug("Email sending disabled until the Sender address has been set in models/000_config.py")
            return False

        limit = settings.get_mail_limit()
        if limit:
            # Check whether we've reached our daily limit
            day = datetime.timedelta(hours=24)
            cutoff = current.request.utcnow - day
            table = current.s3db.msg_limit
            check = current.db(table.created_on > cutoff).count()
            if check >= limit:
                return False
            # Log the sending
            table.insert()

        result = current.mail.send(to,
                                   subject=subject,
                                   message=message,
                                   attachments=attachments,
                                   cc=cc,
                                   bcc=bcc,
                                   reply_to=reply_to,
                                   # @ToDo: Once more people have upgrade their web2py
                                   #sender=sender,
                                   encoding=encoding
                                   )
        if not result:
            current.session.error = current.mail.error
        else:
            current.session.error = None

        return result

    # -------------------------------------------------------------------------
    def send_email_by_pe_id(self,
                            pe_id,
                            subject="",
                            message="",
                            sender_pe_id=None,  # s3_logged_in_person() is useful here
                            sender="",
                            fromaddress="",
                            system_generated=False):
        """
            API wrapper over send_by_pe_id
        """

        return self.send_by_pe_id(pe_id,
                                  subject,
                                  message,
                                  sender_pe_id,
                                  "EMAIL",
                                  sender,
                                  fromaddress,
                                  system_generated)

    # =========================================================================
    # SMS
    # =========================================================================

    # -------------------------------------------------------------------------
    # OpenGeoSMS
    # -------------------------------------------------------------------------
    @staticmethod
    def prepare_opengeosms(location_id, code="S", map="google", text=""):
        """
            Function to create an OpenGeoSMS

            @param: location_id - reference to record in gis_location table
            @param: code - the type of OpenGeoSMS:
                S = Sahana
                SI = Incident Report
                ST = Task Dispatch
            @param: map: "google" or "osm"
            @param: text - the rest of the message

            Returns the formatted OpenGeoSMS or None if it can't find
                an appropriate location
        """

        if not location_id:
            return text

        db = current.db
        s3db = current.s3db
        table = s3db.gis_location
        query = (table.id == location_id)
        location = db(query).select(table.lat,
                                    table.lon,
                                    #table.path,
                                    #table.parent,
                                    limitby=(0, 1)).first()
        if not location:
            return text
        lat = location.lat
        lon = location.lon
        if lat is None or lon is None:
            # @ToDo: Should we try parents? Or would that not be granular enough anyway?
            return text

        code = "GeoSMS=%s" % code

        if map == "google":
            url = "http://maps.google.com/?q=%f,%f" % (lat, lon)
        elif map == "osm":
            # NB Not sure how this will work in OpenGeoSMS client
            url = "http://openstreetmap.org?mlat=%f&mlon=%f&zoom=14" % (lat, lon)

        opengeosms = "%s&%s\n%s" % (url, code, text)

        return opengeosms

    # -------------------------------------------------------------------------
    @staticmethod
    def parse_opengeosms(message):
        """
           Function to parse an OpenGeoSMS
           @param: message - Inbound message to be parsed for OpenGeoSMS.
           Returns the lat, lon, code and text contained in the message.
        """

        lat = ""
        lon = ""
        code = ""
        text = ""

        s3db = current.s3db
        words = string.split(message)
        if "http://maps.google.com/?q" in words[0]:
            # Parse OpenGeoSMS
            pwords = words[0].split("?q=")[1].split(",")
            lat = pwords[0]
            lon = pwords[1].split("&")[0]
            code = pwords[1].split("&")[1].split("=")[1]
            text = ""
            for a in range(1, len(words)):
                text = text + words[a] + " "


        return lat, lon, code, text

    # -------------------------------------------------------------------------
    # Send SMS
    # -------------------------------------------------------------------------
    def send_sms_via_modem(self, mobile, text=""):
        """
            Function to send SMS via locally-attached Modem
            - needs to have the cron/sms_handler_modem.py script running
        """

        mobile = self.sanitise_phone(mobile)

        # Add '+' before country code
        mobile = "+%s" % mobile

        try:
            self.modem.send_sms(mobile, text)
            return True
        except KeyError:
            s3_debug("s3msg", "Modem not available: need to have the cron/sms_handler_modem.py script running")
            return False

    # -------------------------------------------------------------------------
    def send_sms_via_api(self, mobile, text=""):
        """
            Function to send SMS via Web API
        """

        db = current.db
        s3db = current.s3db
        table = s3db.msg_sms_webapi_channel

        # Get Configuration
        query = (table.enabled == True)
        sms_api = db(query).select(limitby=(0, 1)).first()
        if not sms_api:
            return False

        sms_api_post_config = {}

        tmp_parameters = sms_api.parameters.split("&")
        for tmp_parameter in tmp_parameters:
            sms_api_post_config[tmp_parameter.split("=")[0]] = \
                                        tmp_parameter.split("=")[1]

        mobile = self.sanitise_phone(mobile)

        sms_api_post_config[sms_api.message_variable] = text
        sms_api_post_config[sms_api.to_variable] = str(mobile)

        request = urllib2.Request(sms_api.url)
        query = urllib.urlencode(sms_api_post_config)
        if sms_api.username and sms_api.password:
            base64string = base64.encodestring("%s:%s" % (sms_api.username, sms_api.password)).replace("\n", "")
            request.add_header("Authorization", "Basic %s" % base64string)
        try:
            result = urllib2.urlopen(request, query)
            output = result.read()
        except urllib2.HTTPError, e:
            return False
        else:
            # @ToDo: parse result
            # if service == MobileCommons:
            # Good = <response success="true"></response>
            # Bad = <response success="false"><errror id="id" message="message"></response>
            # http://www.mobilecommons.com/mobile-commons-api/rest/#errors
            return True

    # -------------------------------------------------------------------------
    def send_sms_via_smtp(self, mobile, text=""):
        """
            Function to send SMS via SMTP

            NB Different Gateways have different requirements for presence/absence of International code

            http://en.wikipedia.org/wiki/List_of_SMS_gateways
            http://www.obviously.com/tech_tips/SMS_Text_Email_Gateway.html
        """

        table = current.s3db.msg_sms_smtp_channel
        query = (table.enabled == True)
        settings = current.db(query).select(limitby=(0, 1)
                                            ).first()
        if not settings:
            return False

        mobile = self.sanitise_phone(mobile)

        to = "%s@%s" % (mobile,
                        settings.address)

        try:
            result = self.send_email(to=to,
                                     subject="",
                                     message= text)
            return result
        except:
            return False

    #-------------------------------------------------------------------------------------------------
    def send_text_via_tropo(self,
                            row_id,
                            message_id,
                            recipient,
                            message,
                            network = "SMS"):
        """
            Send a URL request to Tropo to pick a message up
        """

        db = current.db
        s3db = current.s3db
        table = s3db.msg_tropo_channel

        base_url = "http://api.tropo.com/1.0/sessions"
        action = "create"

        query = (table.id == 1)
        tropo_settings = db(query).select(table.token_messaging,
                                          limitby=(0, 1)).first()
        if tropo_settings:
            tropo_token_messaging = tropo_settings.token_messaging
            #tropo_token_voice = tropo_settings.token_voice
        else:
            return

        if network == "SMS":
            recipient = self.sanitise_phone(recipient)

        try:
            s3db.msg_tropo_scratch.insert(row_id = row_id,
                                          message_id = message_id,
                                          recipient = recipient,
                                          message = message,
                                          network = network)
            params = urllib.urlencode([("action", action),
                                       ("token", tropo_token_messaging),
                                       ("outgoing", "1"),
                                       ("row_id", row_id)
                                      ])
            xml = urllib2.urlopen("%s?%s" % (base_url, params)).read()
            # Parse Response (actual message is sent as a response to the POST which will happen in parallel)
            #root = etree.fromstring(xml)
            #elements = root.getchildren()
            #if elements[0].text == "false":
            #    session.error = T("Message sending failed! Reason:") + " " + elements[2].text
            #    redirect(URL(f='index'))
            #else:
            #    session.flash = T("Message Sent")
            #    redirect(URL(f='index'))
        except:
            pass
        return False # Returning False because the API needs to ask us for the messsage again.

    # -------------------------------------------------------------------------
    def send_sms_by_pe_id(self,
                          pe_id,
                          message="",
                          sender_pe_id=None,  # s3_logged_in_person() is useful here
                          sender="",
                          fromaddress="",
                          system_generated=False):
        """
            API wrapper over send_by_pe_id
        """

        return self.send_by_pe_id(pe_id,
                                  message,
                                  sender_pe_id,
                                  "SMS",
                                  sender,
                                  fromaddress,
                                  system_generated,
                                  subject=""
                                 )

    # -------------------------------------------------------------------------
    # Twitter
    # -------------------------------------------------------------------------
    @staticmethod
    def sanitise_twitter_account(account):
        """
            Only keep characters that are legal for a twitter account:
            letters, digits, and _
        """

        return account.translate(IDENTITYTRANS, NOTTWITTERCHARS)

    # -------------------------------------------------------------------------
    @staticmethod
    def break_to_chunks(text,
                        chunk_size=TWITTER_MAX_CHARS,
                        suffix = TWITTER_HAS_NEXT_SUFFIX,
                        prefix = TWITTER_HAS_PREV_PREFIX):
        """
            Breaks text to <=chunk_size long chunks. Tries to do this at a space.
            All chunks, except for last, end with suffix.
            All chunks, except for first, start with prefix.
        """

        res = []
        current_prefix = "" # first chunk has no prefix
        while text:
            if len(current_prefix + text) <= chunk_size:
                res.append(current_prefix + text)
                return res
            else: # break a chunk
                c = text[:chunk_size - len(current_prefix) - len(suffix)]
                i = c.rfind(" ")
                if i > 0: # got a blank
                    c = c[:i]
                text = text[len(c):].lstrip()
                res.append((current_prefix + c.rstrip() + suffix))
                current_prefix = prefix # from now on, we want a prefix

    # -------------------------------------------------------------------------
    def get_twitter_api(self):
        """
            Initialize Twitter API
        """

        try:
            import tweepy
        except ImportError:
            s3_debug("s3msg", "Tweepy not available, so non-Tropo Twitter support disabled")
            return None
        else:
            self.tweepy = tweepy

        table = current.s3db.msg_twitter_channel
        # @ToDo: Don't assume that we only have a single record
        twitter_settings = current.db(table.id > 0).select(table.oauth_key,
                                                           table.oauth_secret,
                                                           table.twitter_account,
                                                           limitby=(0, 1)
                                                           ).first()
        if twitter_settings and twitter_settings.twitter_account:
            settings = current.deployment_settings.msg
            try:
                oauth = tweepy.OAuthHandler(settings.twitter_oauth_consumer_key,
                                            settings.twitter_oauth_consumer_secret)
                oauth.set_access_token(twitter_settings.oauth_key,
                                       twitter_settings.oauth_secret)
                twitter_api = tweepy.API(oauth)
                twitter_account = twitter_settings.twitter_account
                return dict(twitter_api=twitter_api,
                            twitter_account=twitter_account)
            except:
                pass

        return None

    # -------------------------------------------------------------------------
    def send_tweet(self, text="", recipient=None):
        """
            Function to tweet.
            If a recipient is specified then we send via direct message if the recipient follows us.
            - falls back to @mention (leaves less characters for the message).
            Breaks long text to chunks if needed.

            @ToDo: Option to Send via Tropo
        """

        # Initialize Twitter API
        twitter_settings = self.get_twitter_api()
        if not twitter_settings:
            # Abort
            return False
        tweepy = self.tweepy

        twitter_api = None
        if twitter_settings:
            twitter_api = twitter_settings["twitter_api"]
            twitter_account = twitter_settings["twitter_account"]

        if not twitter_api and text:
            # Abort
            return False

        if recipient:
            recipient = self.sanitise_twitter_account(recipient)
            try:
                can_dm = twitter_api.exists_friendship(recipient, twitter_account)
            except tweepy.TweepError: # recipient not found
                return False
            if can_dm:
                chunks = self.break_to_chunks(text, TWITTER_MAX_CHARS)
                for c in chunks:
                    try:
                        # Note: send_direct_message() requires explicit kwargs (at least in tweepy 1.5)
                        # See http://groups.google.com/group/tweepy/msg/790fcab8bc6affb5
                        twitter_api.send_direct_message(screen_name=recipient,
                                                        text=c)
                    except tweepy.TweepError:
                        s3_debug("Unable to Tweet DM")
            else:
                prefix = "@%s " % recipient
                chunks = self.break_to_chunks(text,
                                              TWITTER_MAX_CHARS - len(prefix))
                for c in chunks:
                    try:
                        twitter_api.update_status(prefix + c)
                    except tweepy.TweepError:
                        s3_debug("Unable to Tweet @mention")
        else:
            chunks = self.break_to_chunks(text, TWITTER_MAX_CHARS)
            for c in chunks:
                try:
                    twitter_api.update_status(c)
                except tweepy.TweepError:
                    s3_debug("Unable to Tweet")

        return True

    #-------------------------------------------------------------------------
    def receive_subscribed_tweets(self):
        """
            Function  to call to drop the tweets into search_results table
            - called via cron or twitter_search_results controller
        """

        # Initialize Twitter API
        twitter_settings = self.get_twitter_api()
        if not twitter_settings:
            # Abort
            return False

        tweepy = self.tweepy
        twitter_api = None
        if twitter_settings:
            twitter_api = twitter_settings["twitter_api"]

        if not twitter_api:
            # Abort
            return False

        from s3parser import S3Parsing
        parser = S3Parsing.parser

        db = current.db
        s3db = current.s3db
        results_table = s3db.msg_twitter_search_results
        table = s3db.msg_twitter_search
        rows = db(table.id > 0).select(table.id,
                                       table.search_query)

        # Get the latest updated post time to use it as since_id in twitter search
        recent_time = results_table.posted_at.max()

        for row in rows:
            query = row.search_query
            try:
                if recent_time:
                    search_results = twitter_api.search(query,
                                                        result_type="recent",
                                                        show_user=True,
                                                        since_id=recent_time)
                else:
                    search_results = twitter_api.search(query,
                                                        result_type="recent",
                                                        show_user=True)

                search_results.reverse()

                id = row.id
                for result in search_results:
                    # Check if the tweet already exists in the table
                    query = (results_table.posted_by == result.from_user) & \
                            (results_table.posted_at == result.created_at)
                    tweet_exists = db(query).select(results_table.id,
                                                    limitby=(0, 1)
                                                    ).first()

                    if tweet_exists:
                        continue
                    else:
                        tweet = result.text
                        posted_by = result.from_user
                        if result.geo:
                            coordinates = result.geo["coordinates"]
                        else:
                            coordinates = None
                        category, priority, location_id = parser("filter",
                                                                 tweet,
                                                                 posted_by,
                                                                 service="twitter",
                                                                 coordinates=coordinates)
                        results_table.insert(tweet = tweet,
                                             category = category,
                                             priority = priority,
                                             location_id = location_id,
                                             posted_by = posted_by,
                                             posted_at = result.created_at,
                                             twitter_search = id
                                             )
            except tweepy.TweepError:
                s3_debug("Unable to get the Tweets for the user search query.")
                return False

            # Explicitly commit DB operations when running from Cron
            db.commit()

        return True

    # -------------------------------------------------------------------------
    def fetch_inbound_email(self, username, server):
        """
            This is a simple mailbox polling script for the Messaging Module.
            It is called from the scheduler.
            @param username: email address of the email source to read from.
            This uniquely identifies one inbound email task.
        """
        # This is the former cron/email_receive.py.
        #
        # @ToDo: If delete_from_server is false, we don't want to download the
        # same messages repeatedly.  Perhaps record time of fetch runs (or use
        # info from the scheduler_run table), compare w/ message timestamp, as
        # a filter.  That may not be completely accurate, so could check
        # msg_log for messages close to the last fetch time.  Or just advise
        # people to have a dedicated account to which email is sent, that does
        # not also need to be read by humans.  Or don't delete the fetched mail
        # until the next run.  Or...
        #
        # ToDos from the original version:
        # @ToDo: If there is a need to collect from non-compliant mailers then
        # suggest using the robust Fetchmail to collect & store in a more
        # compliant mailer!
        # @ToDo: This doesn't handle MIME attachments.

        import socket, email

        db = current.db
        s3db = current.s3db

        inbound_status_table = s3db.msg_email_inbound_status
        inbox_table = s3db.msg_email
        parsing_table = s3db.msg_parsing_status
        source_task_id = username
        setting_table = s3db.msg_email_inbound_channel

        # Read-in configuration from Database
        query = (setting_table.username == username) & (setting_table.server == server)
        settings = db(query).select(limitby=(0, 1)).first()
        if not settings:
            return "Username %s (%s) not scheduled." % username % server

        host = server
        protocol = settings.protocol
        ssl = settings.use_ssl
        port = settings.port
        username = settings.username
        password = settings.password
        delete = settings.delete_from_server

        if protocol == "pop3":
            import poplib
            # http://docs.python.org/library/poplib.html
            try:
                if ssl:
                    p = poplib.POP3_SSL(host, port)
                else:
                    p = poplib.POP3(host, port)
            except socket.error, e:
                error = "Cannot connect: %s" % e
                print error
                # Store status in the DB
                try:
                    id = db().select(inbound_status_table.id, limitby=(0, 1)).first().id
                    db(inbound_status_table.id == id).update(status=error)
                except:
                    inbound_status_table.insert(status=error)
                # Explicitly commit DB operations when running from Cron
                db.commit()
                return True

            try:
                # Attempting APOP authentication...
                p.apop(username, password)
            except poplib.error_proto:
                # Attempting standard authentication...
                try:
                    p.user(username)
                    p.pass_(password)
                except poplib.error_proto, e:
                    print "Login failed:", e
                    # Store status in the DB
                    try:
                        id = db().select(inbound_status_table.id, limitby=(0, 1)).first().id
                        db(inbound_status_table.id == id).update(status="Login failed: %s" % e)
                    except:
                        inbound_status_table.insert(status="Login failed: %s" % e)
                    # Explicitly commit DB operations when running from Cron
                    db.commit()
                    return True

            dellist = []
            mblist = p.list()[1]
            update_super = s3db.update_super
            for item in mblist:
                number, octets = item.split(" ")
                # Retrieve the message (storing it in a list of lines)
                lines = p.retr(number)[1]
                # Create an e-mail object representing the message
                msg = email.message_from_string("\n".join(lines))
                # Parse out the 'From' Header
                sender = msg["from"]
                # Parse out the 'Subject' Header
                if "subject" in msg:
                    subject = msg["subject"]
                else:
                    subject = ""
                # Parse out the 'Body'
                textParts = msg.get_payload()
                body = textParts[0]
                # Store in DB
                id = inbox_table.insert(from_address=sender, subject=subject, \
                                        body=body, inbound=True)
                query = (inbox_table.id == id)
                record = db(query).select(inbox_table.message_id, \
                                          limitby=(0, 1)).first()
                update_super(inbox_table, record)
                parsing_table.insert(message_id = record.message_id, \
                                     source_task_id = source_task_id, \
                                     is_parsed = False)

                if delete:
                    # Add it to the list of messages to delete later
                    dellist.append(number)
            # Explicitly commit DB operations when running from Cron.
            # @ToDo:  Still needed when running under Scheduler?
            db.commit()
            # Iterate over the list of messages to delete
            for number in dellist:
                p.dele(number)
            p.quit()

        elif protocol == "imap":
            import imaplib
            # http://docs.python.org/library/imaplib.html
            try:
                if ssl:
                    M = imaplib.IMAP4_SSL(host, port)
                else:
                    M = imaplib.IMAP4(host, port)
            except socket.error, e:
                error = "Cannot connect: %s" % e
                print error
                # Store status in the DB
                try:
                    id = db().select(inbound_status_table.id, limitby=(0, 1)).first().id
                    db(inbound_status_table.id == id).update(status=error)
                except:
                    inbound_status_table.insert(status=error)
                # Explicitly commit DB operations when running from Cron
                # @ToDo:  Still needed when running under Scheduler?
                db.commit()
                return True

            try:
                M.login(username, password)
            except M.error, e:
                error = "Login failed: %s" % e
                print error
                # Store status in the DB
                try:
                    id = db().select(inbound_status_table.id, limitby=(0, 1)).first().id
                    db(inbound_status_table.id == id).update(status=error)
                except:
                    inbound_status_table.insert(status=error)
                # Explicitly commit DB operations when running from Cron
                db.commit()
                return True

            dellist = []
            # Select inbox
            M.select()
            # Search for Messages to Download
            typ, data = M.search(None, "ALL")
            update_super = s3db.update_super

            for num in data[0].split():
                typ, msg_data = M.fetch(num, "(RFC822)")
                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        msg = email.message_from_string(response_part[1])
                        # Parse out the 'From' Header
                        sender = msg["from"]
                        # Parse out the 'Subject' Header
                        if "subject" in msg:
                            subject = msg["subject"]
                        else:
                            subject = ""
                        # Parse out the 'Body'
                        textParts = msg.get_payload()
                        body = textParts[0]
                        # Store in DB
                        id = inbox_table.insert(from_address=sender, \
                                                subject=subject, body=body, \
                                                inbound=True)
                        query = (inbox_table.id == id)
                        record = db(query).select(inbox_table.message_id, \
                                                  limitby=(0, 1)).first()
                        update_super(inbox_table, record)
                        parsing_table.insert(message_id = record.message_id, \
                                             source_task_id = source_task_id, \
                                             is_parsed = False)

                        if delete:
                            # Add it to the list of messages to delete later
                            dellist.append(num)
            # Explicitly commit DB operations when running from Cron
            db.commit()
            # Iterate over the list of messages to delete
            for number in dellist:
                typ, response = M.store(number, "+FLAGS", r"(\Deleted)")
            M.close()
            M.logout()

    # -------------------------------------------------------------------------
    @staticmethod
    def source_id(username):
        """ Extracts the source_task_id from a given message. """

        db = current.db
        table = db.scheduler_task
        records = db(table.id > 0).select(table.id,
                                          table.vars)
        for record in records:
            if record.vars.split(":") == ["{\"username\""," \"%s\"}" % username] :
                return record.id

    # -------------------------------------------------------------------------
    @staticmethod
    def mcommons_poll(campaign_id):
        """
            Fetches the inbound SMS from Mobile Commons API
            http://www.mobilecommons.com/mobile-commons-api/rest/#ListIncomingMessages
        """

        db = current.db
        s3db = current.s3db
        table = s3db.msg_mcommons_channel
        query = (table.campaign_id == campaign_id)
        account = db(query).select(limitby=(0, 1)).first()
        if account:
            url = account.url
            username = account.username
            password = account.password
            _query = account.query
            timestamp = account.timestmp

            url = "%s?campaign_id=%s" % (url, campaign_id)
            if timestamp:
                url = "%s&start_time=%s" % (url, timestamp)
            if _query:
                url = "%s&query=%s" % (url, _query)

            # Create a password manager
            passman = urllib2.HTTPPasswordMgrWithDefaultRealm()
            passman.add_password(None, url, username, password)

            # Create the AuthHandler
            authhandler = urllib2.HTTPBasicAuthHandler(passman)
            opener = urllib2.build_opener(authhandler)
            urllib2.install_opener(opener)

            # Update the timestamp
            # NB Ensure MCommons account is in UTC
            db(query).update(timestmp = current.request.utcnow)

            table = s3db.msg_inbox
            try:
                _response = urllib2.urlopen(url)
                sms_xml = _response.read()
                tree = etree.XML(sms_xml)
                messages = tree.findall(".//message")
                iinsert = table.insert
                decode = S3Codec.decode_iso_datetime
                for message in messages:
                    sender_phone = message.find("phone_number").text
                    body = message.find("body").text
                    received_on = decode(message.find("received_at").text)
                    iinsert(channel = "MCommons: %s" % campaign_id,
                            sender_phone = sender_phone,
                            body = body,
                            received_on = received_on,
                            )

            except urllib2.HTTPError, e:
                return "Error:" + str(e.code)
            return

    # -------------------------------------------------------------------------
    @staticmethod
    def twilio_poll(account_name):
        """ Fetches the inbound SMS from Twilio API."""

        db = current.db
        s3db = current.s3db
        ttable = s3db.msg_twilio_inbound_channel
        query = (ttable.account_name == account_name) & \
                (ttable.deleted == False)
        account = db(query).select(limitby=(0, 1)).first()
        if account:
            url = account.url
            account_sid = account.account_sid
            auth_token = account.auth_token

            # @ToDo: Do we really have to download *all* messages every time
            # & then only import the ones we don't yet have?
            url += "/%s/SMS/Messages.json" % str(account_sid)

            # Create a password manager
            passman = urllib2.HTTPPasswordMgrWithDefaultRealm()
            passman.add_password(None, url, account_sid, auth_token)

            # Create the AuthHandler
            authhandler = urllib2.HTTPBasicAuthHandler(passman)
            opener = urllib2.build_opener(authhandler)
            urllib2.install_opener(opener)

            itable = s3db.msg_twilio_inbox
            mtable = s3db.msg_message
            query = itable.deleted == False
            messages = db(query).select(itable.sid)
            downloaded_sms = [message.sid for message in messages]
            try:
                smspage = urllib2.urlopen(url)
                minsert = itable.insert
                sms_list = json.loads(smspage.read())
                update_super = s3db.update_super

                for sms in  sms_list["sms_messages"]:
                    if (sms["direction"] == "inbound") and \
                       (sms["sid"] not in downloaded_sms):
                        sender = "<" + sms["from"] + ">"
                        id = minsert(sid=sms["sid"],body=sms["body"], \
                                status=sms["status"],from_address=sender, \
                                received_on=sms["date_sent"])
                        query = (itable.id == id)
                        record = db(query).select(itable.message_id, \
                                                  limitby=(0, 1)).first()
                        update_super(itable, record)
                        message_id = record.message_id
                        ptable.insert(message_id = message_id, \
                                      source_task_id = sender)

            except urllib2.HTTPError, e:
                return "Error:" + str(e.code)
            return

    # -------------------------------------------------------------------------
    @staticmethod
    def rss_poll():
        """ Fetches RSS Feeds."""

        import gluon.contrib.feedparser as feedparser

        request = current.request
        s3db = current.s3db
        db = current.db
        ctable = s3db.msg_rss_channel
        ftable = s3db.msg_rss_feed
        ptable = s3db.msg_parsing_status

        query = (ctable.deleted == False) & (ctable.subscribed == True)
        links = db(query).select(ctable.url)

        update_super = s3db.update_super

        for link in links:
            d = feedparser.parse(link.url)
            for entry in d.entries:
                id = ftable.insert(title = entry.title, \
                                   from_address = entry.link, \
                                   body = entry.description, \
                                   created_on = request.now)
                record = db(ftable.id == id).select(ftable.message_id, \
                                                     limitby=(0, 1)).first()
                update_super(ftable, record)
                message_id = records.message_id
                ptable.insert(message_id = message_id, \
                              source_task_id = entry.link)

        # Commit as this is a task normally run async
        db.commit()
        return

# =============================================================================
class S3Compose(S3CRUD):
    """ RESTful method for messaging """

    # -------------------------------------------------------------------------
    def apply_method(self, r, **attr):
        """
            API entry point

            @param r: the S3Request instance
            @param attr: controller attributes for the request
        """

        if r.http in ("GET", "POST"):
            output = self.compose(r, **attr)
        else:
            r.error(405, current.manager.ERROR.BAD_METHOD)
        return output

    # -------------------------------------------------------------------------
    def compose(self, r, **attr):
        """
            Generate a form to send a message

            @param r: the S3Request instance
            @param attr: controller attributes for the request
        """

        T = current.T
        auth = current.auth

        url = r.url()
        self.url = url

        # @ToDo: Use API
        if auth.is_logged_in() or auth.basic():
            pass
        else:
            redirect(URL(c="default", f="user", args="login",
                         vars={"_next" : url}))

        if not current.deployment_settings.has_module("msg"):
            current.session.error = T("Cannot send messages if Messaging module disabled")
            redirect(URL(f="index"))

        if not auth.permission.has_permission("update", c="msg"):
            current.session.error = T("You do not have permission to send messages")
            redirect(URL(f="index"))

        #_vars = r.get_vars

        self.recipients = None
        form = self._compose_form()
        # @ToDo: A 2nd Filter form
        # if form.accepts(r.post_vars, current.session,
                        # formname="compose",
                        # keepvalues=True):
            # query, errors = self._process_filter_options(form)
            # if r.http == "POST" and not errors:
                # self.resource.add_filter(query)
            # _vars = form.vars

        # Apply method
        resource = self.resource
        representation = r.representation

        if self.method == "compose":
            #output = dict(items=items)
            output = dict(form=form)
        else:
            r.error(501, current.manager.ERROR.BAD_METHOD)

        # Complete the page
        if representation == "html":
            title = self.crud_string(self.tablename, "title_compose")
            if not title:
                title = T("Send Message")

            # subtitle = self.crud_string(self.tablename, "subtitle_compose")
            # if not subtitle:
                # subtitle = ""

            # Maintain RHeader for consistency
            if attr.get("rheader"):
                rheader = attr["rheader"](r)
                if rheader:
                    output["rheader"] = rheader

            output["title"] = title
            #output["subtitle"] = subtitle
            #output["form"] = form
            #current.response.view = self._view(r, "list_create.html")
            current.response.view = self._view(r, "create.html")

        return output

    # -------------------------------------------------------------------------
    def _compose_onvalidation(self, form):
        """
            Set the sender
            Route the message
        """

        T = current.T
        auth = current.auth
        msg = current.msg
        session = current.session

        vars = current.request.post_vars

        recipients = self.recipients
        if not recipients:
            if not vars.pe_id:
                session.error = T("Please enter the recipient(s)")
                redirect(self.url)
            else:
                recipients = vars.pe_id

        table = current.s3db.pr_person
        if auth.user:
            sender_pe_id = auth.user.pe_id
        else:
            return
        if msg.send_by_pe_id(recipients,
                             vars.subject,
                             vars.message,
                             sender_pe_id,
                             vars.pr_message_method):
            session.confirmation = T("Check outbox for the message status")
            redirect(self.url)
        else:
            session.error = T("Error in message")
            redirect(self.url)

    # -------------------------------------------------------------------------
    def _compose_form(self):
        """ Creates the form for composing the message """

        resource = self.resource
        table = resource.table

        T = current.T
        db = current.db
        s3db = current.s3db
        s3 = current.response.s3

        ltable = s3db.msg_log
        otable = s3db.msg_outbox

        # @ToDo: read request.get_vars.message?
        #ltable.message.default = message

        # See if we have defined a custom recipient type for this table
        # pr_person or pr_group
        recipient_type = self._config("msg_recipient_type", None)

        # See if we have defined a custom default contact method for this table
        type = self._config("msg_contact_method", "SMS")
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

        recipients = []

        if "pe_id" in table:
            field = "pe_id"
        elif "person_id" in table:
            field = "person_id$pe_id"
        #elif "group_id" in table:
        #    # @ToDo
        #    field = "group_id$pe_id"
        else:
            field = None

        if field:
            records = resource.select([field], limit=None)["rows"]
            recipients = [record.values()[0] for record in records]

        if recipients:
            self.recipients = recipients
            ltable.pe_id.default = recipients
            otable.pe_id.default = recipients
            ltable.pe_id.requires = IS_ONE_OF_EMPTY(db, "pr_pentity.pe_id", multiple=True)
        else:
            if recipient_type:
                # Filter by Recipient Type
                otable.pe_id.requires = IS_ONE_OF(db, "pr_pentity.pe_id",
                                                  orderby="instance_type",
                                                  filterby="instance_type",
                                                  filter_opts=(recipient_type,))
            otable.pe_id.comment = DIV(_class="tooltip",
                                       _title="%s|%s" % \
                                        (T("Recipients"),
                                         T("Please enter the first few letters of the Person/Group for the autocomplete.")))
        otable.pe_id.writable = True
        otable.pe_id.label = T("Recipient(s)")

        # Source forms
        # @ToDo: Rewrite using SQLFORM or S3SQLCustomForm
        crud = CrudS3()
        crud.messages.submit_button = T("Save")
        crud.settings.formstyle = s3.crud.formstyle
        logform = crud.create(ltable,
                              onvalidation = self._compose_onvalidation)
        outboxform = crud.create(otable)

        # Shortcuts
        lcustom = logform.custom
        ocustom = outboxform.custom

        pe_row = TR(TD(LABEL("%s:" % ocustom.label.pe_id)),
                    _id="msg_outbox_pe_id__row")
        if recipients:
            if len(recipients) == 1:
                recipient = recipients[0]
                represent = s3db.pr_pentity_represent(recipient)
                # Restrict message options to those available for the entity
                # @ToDo: Support Groups, etc by looking up Entity Type
                ctable = s3db.pr_contact
                rows = db(ctable.pe_id == recipient).select(ctable.contact_method)
                contact_method_opts = [row.contact_method for row in rows]
                if not contact_method_opts:
                    current.session.error = T("There are no contacts available for this person!")
                    request = current.request
                    controller = request.controller
                    vars = request.get_vars
                    if controller == "hrm":
                        url = URL(c="hrm", f="person", args="contacts",
                                  vars={"group": "staff",
                                        "human_resource.id": vars.get("human_resource.id")})
                    elif controller == "vol":
                        url = URL(c="vol", f="person", args="contacts",
                                  vars={"group": "volunteer",
                                        "human_resource.id": vars.get("human_resource.id")})
                    elif controller == "member":
                        url = URL(c="member", f="person", args="contacts",
                                  vars={"membership.id": vars.get("membership.id")})
                    else:
                        # @ToDo: Lookup the type
                        url = URL(f="index")
                    redirect(url)
                otable.pr_message_method.requires = IS_IN_SET(contact_method_opts,
                                                              zero=None)
                if type not in contact_method_opts:
                    otable.pr_message_method.default = contact_method_opts[0]
            else:
                # @ToDo: This should display all the Recipients (truncated with option to see all)
                # - wait for pr_PersonEntityRepresent for bulk representation.
                represent = "%(number)s Recipients" % dict(number=len(recipients))
            pe_row.append(TD(represent))
        else:
            # @ToDo: This should be an S3Search form
            pe_row.append(TD(INPUT(_id="dummy", _class="ac_input", _size="50"),
                             ocustom.widget.pe_id))
            pe_row.append(TD(ocustom.comment.pe_id))

        # Build a custom form from the 2 source forms
        form = DIV( lcustom.begin,
                    TABLE(
                        TBODY(
                            TR(TD(LABEL("%s:" % \
                                ocustom.label.pr_message_method)),
                               TD(ocustom.widget.pr_message_method),
                               TD(ocustom.comment.pr_message_method),
                               _id="msg_outbox_pr_message_method__row"
                            ),
                            pe_row,
                            TR(TD(LABEL("%s:" % lcustom.label.subject)),
                               TD(lcustom.widget.subject),
                               TD(lcustom.comment.subject),
                               _id="msg_log_subject__row"
                            ),
                            TR(TD(LABEL("%s:" % lcustom.label.message)),
                               TD(lcustom.widget.message),
                               TD(lcustom.comment.message),
                               _id="msg_log_message__row"
                            ),
                            # TR(TD(LABEL("%s:" % lcustom.label.priority)),
                               # TD(lcustom.widget.priority),
                               # TD(lcustom.comment.priority),
                               # _id="msg_log_priority__row"
                            # ),
                            TR(TD(),
                               TD(INPUT(_type="submit",
                                        _value=T("Send message"),
                                        _id="dummy_submit")),
                               _id="submit_record__row"
                            ),
                        )
                    ),
                    lcustom.end)

        # Control the Javascript in static/scripts/S3/s3.msg.js
        if not recipients:
            if recipient_type:
                s3.js_global.append('''S3.msg_search_url="%s"''' % \
                                    URL(c="msg", f="search",
                                        vars={"type":recipient_type}))
            else:
                s3.js_global.append('''S3.msg_search_url="%s"''' % \
                                    URL(c="msg", f="search"))

            s3.jquery_ready.append('''s3_msg_ac_pe_input()''')

        return form

# =============================================================================
# @ToDo: Deprecate these classes once _compose_form() has been rewritten
#        - also used by project/comments()
# =============================================================================
class CrudS3(Crud):
    """
        S3 extension of the gluon.tools.Crud class
        - select() uses SQLTABLES3 (to allow different linkto construction)

        @todo: is this still used anywhere?
    """

    def __init__(self):
        """ Initialise parent class & make any necessary modifications """
        Crud.__init__(self, current.db)


    def select(
        self,
        table,
        query=None,
        fields=None,
        orderby=None,
        limitby=None,
        headers={},
        **attr):

        db = current.db
        request = current.request
        if not (isinstance(table, db.Table) or table in db.tables):
            raise HTTP(404)
        if not self.has_permission("select", table):
            redirect(current.auth.settings.on_failed_authorization)
        #if record_id and not self.has_permission("select", table):
        #    redirect(current.auth.settings.on_failed_authorization)
        if not isinstance(table, db.Table):
            table = db[table]
        if not query:
            query = table.id > 0
        if not fields:
            fields = [table.ALL]
        rows = db(query).select(*fields, **dict(orderby=orderby,
            limitby=limitby))
        if not rows:
            return None # Nicer than an empty table.
        if not "linkto" in attr:
            attr["linkto"] = self.url(args="read")
        if not "upload" in attr:
            attr["upload"] = self.url("download")
        if request.extension != "html":
            return rows.as_list()
        return SQLTABLES3(rows, headers=headers, **attr)

# =============================================================================
class SQLTABLES3(SQLTABLE):
    """
        S3 custom version of gluon.sqlhtml.SQLTABLE

        Given a SQLRows object, as returned by a db().select(), generates
        an html table with the rows.

            - we need a different linkto construction for our CRUD controller
            - we need to specify a different ID field to direct to for the M2M controller
            - used by S3Resource.sqltable

        Optional arguments:

        @keyword linkto: URL (or lambda to generate a URL) to edit individual records
        @keyword upload: URL to download uploaded files
        @keyword orderby: Add an orderby link to column headers.
        @keyword headers: dictionary of headers to headers redefinions
        @keyword truncate: length at which to truncate text in table cells.
            Defaults to 16 characters.

        Optional names attributes for passed to the <table> tag

        Simple linkto example::

            rows = db.select(db.sometable.ALL)
            table = SQLTABLES3(rows, linkto="someurl")

        This will link rows[id] to .../sometable/value_of_id

        More advanced linkto example::

            def mylink(field):
                return URL(args=[field])

            rows = db.select(db.sometable.ALL)
            table = SQLTABLES3(rows, linkto=mylink)

        This will link rows[id] to::

            current_app/current_controller/current_function/value_of_id
    """

    def __init__(self, sqlrows,
                 linkto=None,
                 upload=None,
                 orderby=None,
                 headers={},
                 truncate=16,
                 columns=None,
                 th_link="",
                 **attributes):

        # reverted since it causes errors (admin/user & manual importing of req/req/import)
        # super(SQLTABLES3, self).__init__(**attributes)
        TABLE.__init__(self, **attributes)

        self.components = []
        self.attributes = attributes
        self.sqlrows = sqlrows
        (components, row) = (self.components, [])
        if not columns:
            columns = sqlrows.colnames
        if headers=="fieldname:capitalize":
            headers = {}
            for c in columns:
                headers[c] = " ".join([w.capitalize() for w in c.split(".")[-1].split("_")])
        elif headers=="labels":
            headers = {}
            for c in columns:
                (t, f) = c.split(".")
                field = sqlrows.db[t][f]
                headers[c] = field.label

        if headers!=None:
            for c in columns:
                if orderby:
                    row.append(TH(A(headers.get(c, c),
                                    _href=th_link+"?orderby=" + c)))
                else:
                    row.append(TH(headers.get(c, c)))
            components.append(THEAD(TR(*row)))

        tbody = []
        table_field = re.compile("[\w_]+\.[\w_]+")
        for (rc, record) in enumerate(sqlrows):
            row = []
            if rc % 2 == 0:
                _class = "even"
            else:
                _class = "odd"
            for colname in columns:
                if not table_field.match(colname):
                    if "_extra" in record and colname in record._extra:
                        r = record._extra[colname]
                        row.append(TD(r))
                        continue
                    else:
                        raise KeyError("Column %s not found (SQLTABLE)" % colname)
                (tablename, fieldname) = colname.split(".")
                try:
                    field = sqlrows.db[tablename][fieldname]
                except (KeyError, AttributeError):
                    field = None
                if tablename in record \
                        and isinstance(record, Row) \
                        and isinstance(record[tablename], Row):
                    r = record[tablename][fieldname]
                elif fieldname in record:
                    r = record[fieldname]
                else:
                    raise SyntaxError("something wrong in Rows object")
                r_old = r
                if not field:
                    pass
                elif linkto and field.type == "id":
                    #try:
                        #href = linkto(r, "table", tablename)
                    #except TypeError:
                        #href = "%s/%s/%s" % (linkto, tablename, r_old)
                    #r = A(r, _href=href)
                    try:
                        href = linkto(r)
                    except TypeError:
                        href = "%s/%s" % (linkto, r)
                    r = A(r, _href=href)
                #elif linkto and field.type.startswith("reference"):
                    #ref = field.type[10:]
                    #try:
                        #href = linkto(r, "reference", ref)
                    #except TypeError:
                        #href = "%s/%s/%s" % (linkto, ref, r_old)
                        #if ref.find(".") >= 0:
                            #tref,fref = ref.split(".")
                            #if hasattr(sqlrows.db[tref],"_primarykey"):
                                #href = "%s/%s?%s" % (linkto, tref, urllib.urlencode({fref:r}))
                    #r = A(str(r), _href=str(href))
                elif linkto \
                     and hasattr(field._table, "_primarykey") \
                     and fieldname in field._table._primarykey:
                    # have to test this with multi-key tables
                    key = urllib.urlencode(dict([ \
                                ((tablename in record \
                                      and isinstance(record, Row) \
                                      and isinstance(record[tablename], Row)) \
                                      and (k, record[tablename][k])) \
                                      or (k, record[k]) \
                                    for k in field._table._primarykey]))
                    r = A(r, _href="%s/%s?%s" % (linkto, tablename, key))
                elif field.type.startswith("list:"):
                    r = field.represent(r or [])
                elif field.represent:
                    r = field.represent(r)
                elif field.type.startswith("reference"):
                    pass
                elif field.type == "blob" and r:
                    r = "DATA"
                elif field.type == "upload":
                    if upload and r:
                        r = A("file", _href="%s/%s" % (upload, r))
                    elif r:
                        r = "file"
                    else:
                        r = ""
                elif field.type in ["string", "text"]:
                    r = str(field.formatter(r))
                    ur = unicode(r, "utf8")
                    if truncate!=None and len(ur) > truncate:
                        r = ur[:truncate - 3].encode("utf8") + "..."
                row.append(TD(r))
            tbody.append(TR(_class=_class, *row))
        components.append(TBODY(*tbody))

# END =========================================================================
