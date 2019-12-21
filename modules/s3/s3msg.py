# -*- coding: utf-8 -*-

""" Messaging API

    API to send & receive messages:
    - currently SMS, Email, RSS & Twitter

    Messages get sent to the Outbox (& Log)
    From there, the Scheduler tasks collect them & send them

    @copyright: 2009-2019 (c) Sahana Software Foundation
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

__all__ = ("S3Msg",
           "S3Compose",
           )

import base64
import datetime
import json
import os
import re
import string
import sys

try:
    from lxml import etree
except ImportError:
    sys.stderr.write("ERROR: lxml module needed for XML handling\n")
    raise

from gluon import current, redirect
from gluon.html import *

from s3compat import HTTPError, PY2, StringIO, urlencode, urllib2, urlopen
#from .s3codec import S3Codec
from .s3crud import S3CRUD
from .s3datetime import s3_decode_iso_datetime
from .s3forms import S3SQLDefaultForm
from .s3utils import s3_str, s3_unicode
from .s3validators import IS_IN_SET, IS_ONE_OF
from .s3widgets import S3PentityAutocompleteWidget

PHONECHARS = string.digits
TWITTERCHARS = "%s%s_" % (string.digits, string.ascii_letters)
if PY2:
    # Inverted permitted character sets for use with str.translate
    # => faster, but not working for unicode and hence not supported in Py3
    IDENTITYTRANS = ALLCHARS = string.maketrans("", "")
    NOTPHONECHARS = ALLCHARS.translate(IDENTITYTRANS, PHONECHARS)
    NOTTWITTERCHARS = ALLCHARS.translate(IDENTITYTRANS, TWITTERCHARS)

TWITTER_MAX_CHARS = 140
TWITTER_HAS_NEXT_SUFFIX = u' \u2026'
TWITTER_HAS_PREV_PREFIX = u'\u2026 '

SENDER = re.compile(r"(.*)\s*\<(.+@.+)\>\s*")

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
        self.CONTACT_OPTS = {"EMAIL":       T("Email"),
                             "FACEBOOK":    T("Facebook"),
                             "FAX":         T("Fax"),
                             "HOME_PHONE":  T("Home Phone"),
                             "RADIO":       T("Radio Callsign"),
                             "RSS":         T("RSS Feed"),
                             "SKYPE":       T("Skype"),
                             "SMS":         MOBILE,
                             "TWITTER":     T("Twitter"),
                             "WHATSAPP":    T("WhatsApp"),
                             #"XMPP":       "XMPP",
                             #"WEB":        T("Website"),
                             "WORK_PHONE":  T("Work phone"),
                             "IRC":         T("IRC handle"),
                             "GITHUB":      T("Github Repo"),
                             "GCM":         T("Google Cloud Messaging"),
                             "LINKEDIN":    T("LinkedIn Profile"),
                             "BLOG":        T("Blog"),
                             "OTHER":       T("Other")
                             }

        # Those contact options to which we can send notifications
        # NB Coded into hrm_map_popup & s3.msg.js
        self.MSG_CONTACT_OPTS = {"EMAIL":   T("Email"),
                                 "SMS":     MOBILE,
                                 "TWITTER": T("Twitter"),
                                 "FACEBOOK": T("Facebook"),
                                 #"XMPP":   "XMPP",
                                 }

        # SMS Gateways
        self.GATEWAY_OPTS = {"MODEM":   T("Modem"),
                             "SMTP":    T("SMTP"),
                             "TROPO":   T("Tropo"),
                             # Currently only available for Inbound
                             #"TWILIO":  T("Twilio"),
                             "WEB_API": T("Web API"),
                             }

    # -------------------------------------------------------------------------
    @staticmethod
    def sanitise_phone(phone, channel_id=None):
        """
            Strip out unnecessary characters from the string:
            +()- & space
        """

        settings = current.deployment_settings
        table = current.s3db.msg_sms_outbound_gateway

        if channel_id:
            row = current.db(table.channel_id == channel_id) \
                         .select(limitby=(0, 1)).first()
            default_country_code = row["msg_sms_outbound_gateway.default_country_code"]
        else:
            default_country_code = settings.get_L10n_default_country_code()

        if PY2:
            clean = phone.translate(IDENTITYTRANS, NOTPHONECHARS)
        else:
            clean = "".join(c for c in phone if c in PHONECHARS)

        # If number starts with a 0 then need to remove this & add the country code in
        if clean[0] == "0":
            # Add default country code
            if default_country_code == 39:
                # Italy keeps 0 after country code
                clean = "%s%s" % (default_country_code, clean)
            else:
                clean = "%s%s" % (default_country_code,
                                  clean.lstrip("0"))

        return clean

    # -------------------------------------------------------------------------
    @staticmethod
    def decode_email(header):
        """
            Decode an RFC2047-encoded email header (e.g.
            "Dominic =?ISO-8859-1?Q?K=F6nig?=") and return it as unicode.

            @param header: the header
        """

        # Deal with missing word separation (thanks Ingmar Hupp)
        header = re.sub(r"(=\?.*\?=)(?!$)", r"\1 ", header)

        # Decode header
        from email.header import decode_header
        decoded = decode_header(header)

        # Build string
        return " ".join([s3_unicode(part[0], part[1] or "ASCII")
                         for part in decoded])

    # =========================================================================
    # Inbound Messages
    # =========================================================================
    @staticmethod
    def sort_by_sender(row):
        """
           Helper method to sort messages according to sender priority.
        """

        s3db = current.s3db
        db = current.db
        ptable = s3db.msg_parsing_status
        mtable = s3db.msg_message
        stable = s3db.msg_sender

        try:
            # @ToDo: Look at doing a Join?
            pmessage = db(ptable.id == row.id).select(ptable.message_id)
            m_id = pmessage.message_id

            message = db(mtable.id == m_id).select(mtable.from_address,
                                                   limitby=(0, 1)).first()
            sender = message.from_address

            srecord = db(stable.sender == sender).select(stable.priority,
                                                         limitby=(0, 1)).first()

            return srecord.priority
        except:
            # Return max value i.e. assign lowest priority
            return sys.maxsize

    # -------------------------------------------------------------------------
    @staticmethod
    def parse(channel_id, function_name):
        """
           Parse unparsed Messages from Channel with Parser
           - called from Scheduler

           @param channel_id: Channel
           @param function_name: Parser
        """

        from .s3parser import S3Parsing

        parser = S3Parsing.parser
        stable = current.s3db.msg_parsing_status
        query = (stable.channel_id == channel_id) & \
                (stable.is_parsed == False)
        messages = current.db(query).select(stable.id,
                                            stable.message_id)
        for message in messages:
            # Parse the Message
            reply_id = parser(function_name, message.message_id)
            # Update to show that we've parsed the message & provide a link to the reply
            message.update_record(is_parsed=True,
                                  reply_id=reply_id)
        return

    # =========================================================================
    # Outbound Messages
    # =========================================================================
    def compose(self,
                type = "SMS",
                recipient_type = None,
                recipient = None,
                #@ToDo:
                #sender = None,
                #hide = True,
                subject = "",
                message = "",
                url = None,
                # @ToDo: re-implement
                #formid = None,
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

        if not url:
            url = URL(c="msg", f="compose")

        # Unauthenticated users aren't allowed to Compose Messages
        auth = current.auth
        if auth.is_logged_in() or auth.basic():
            pass
        else:
            redirect(URL(c="default", f="user", args="login",
                         vars={"_next" : url}))

        # Authenticated users need to have update rights on the msg controller
        if not auth.permission.has_permission("update", c="msg"):
            current.session.error = current.T("You do not have permission to send messages")
            redirect(URL(f="index"))

        # Configure an instance of S3Compose
        instance = S3Compose()
        instance.contact_method = type
        instance.recipient = recipient
        instance.recipients = None
        instance.recipient_type = recipient_type
        instance.subject = subject
        instance.message = message
        #instance.formid = formid
        instance.resource = None
        instance.url = url

        # Generate the form
        form = instance._compose_form()

        # Default title
        # - can be overridden by the calling function
        title = current.T("Send Message")

        return dict(form = form,
                    title = title)

    # -------------------------------------------------------------------------
    @staticmethod
    def send(recipient, message, subject=None):
        """
            Send a single message to an Address

            @param recipient: "email@address", "+4412345678", "@nick"
            @param message: message body
            @param subject: message subject (Email only)
        """

        # Determine channel to send on based on format of recipient
        if recipient.startswith("@"):
            # Twitter
            tablename = "msg_twitter"
        elif "@" in recipient:
            # Email
            tablename = "msg_email"
        else:
            # SMS
            tablename = "msg_sms"

        # @ToDo: Complete this

    # -------------------------------------------------------------------------
    @staticmethod
    def send_by_pe_id(pe_id,
                      subject = "",
                      message = "",
                      contact_method = "EMAIL",
                      document_ids = None,
                      from_address = None,
                      system_generated = False,
                      **data):
        """
            Send a single message to a Person Entity (or list thereof)

            @ToDo: contact_method = ALL
                - look up the pr_contact options available for the pe & send via all

            @ToDo: This is not transaction safe
              - power failure in the middle will cause no message in the outbox
        """

        s3db = current.s3db

        # Place the Message in the appropriate Log
        if contact_method == "EMAIL":
            if not from_address:
                # Fallback to system default
                # @ToDo: Allow a multi-context lookup here for multi-tenancy?
                from_address = current.deployment_settings.get_mail_sender()

            table = s3db.msg_email
            _id = table.insert(body=message,
                               subject=subject,
                               from_address=from_address,
                               #to_address=pe_id,
                               inbound=False,
                               )
            record = dict(id=_id)
            s3db.update_super(table, record)
            message_id = record["message_id"]
            if document_ids:
                ainsert = s3db.msg_attachment.insert
                if not isinstance(document_ids, list):
                    document_ids = [document_ids]
                for document_id in document_ids:
                    ainsert(message_id=message_id,
                            document_id=document_id,
                            )

        elif contact_method == "SMS":
            table = s3db.msg_sms
            _id = table.insert(body=message,
                               from_address=from_address,
                               inbound=False,
                               )
            record = dict(id=_id)
            s3db.update_super(table, record)
            message_id = record["message_id"]
        elif contact_method == "TWITTER":
            table = s3db.msg_twitter
            _id = table.insert(body=message,
                               from_address=from_address,
                               inbound=False,
                               )
            record = dict(id=_id)
            s3db.update_super(table, record)
            message_id = record["message_id"]
        else:
            # @ToDo
            raise NotImplementedError

        # Place the Message in the main OutBox
        table = s3db.msg_outbox
        if isinstance(pe_id, list):
            # Add an entry per recipient
            listindex = 0
            insert = table.insert
            for _id in pe_id:
                try:
                    insert(message_id = message_id,
                           pe_id = _id,
                           contact_method = contact_method,
                           system_generated = system_generated)
                    listindex = listindex + 1
                except:
                    return listindex
        else:
            try:
                table.insert(message_id = message_id,
                             pe_id = pe_id,
                             contact_method = contact_method,
                             system_generated = system_generated)
            except:
                return False

        # Process OutBox async
        current.s3task.run_async("msg_process_outbox",
                                 args = [contact_method])

        # Perform post process after message sending
        postp = current.deployment_settings.get_msg_send_postprocess()
        if postp:
            postp(message_id, **data)

        return message_id

    # -------------------------------------------------------------------------
    def process_outbox(self, contact_method="EMAIL"):
        """
            Send pending messages from outbox (usually called from scheduler)

            @param contact_method: the output channel (see pr_contact.method)

            @todo: contact_method = "ALL"
        """

        db = current.db
        s3db = current.s3db

        lookup_org = False
        channels = {}
        outgoing_sms_handler = None
        channel_id = None

        if contact_method == "SMS":
            # Read all enabled Gateways
            # - we assume there are relatively few & we may need to decide which to use based on the message's organisation
            table = s3db.msg_sms_outbound_gateway
            etable = db.msg_channel
            query = (table.deleted == False) & \
                    (table.channel_id == etable.channel_id)
            rows = db(query).select(table.channel_id,
                                    table.organisation_id,
                                    etable.instance_type,
                                    )
            if not rows:
                # Raise exception here to make the scheduler
                # task fail permanently until manually reset
                raise ValueError("No SMS handler defined!")

            if len(rows) == 1:
                lookup_org = False
                row = rows.first()
                outgoing_sms_handler = row["msg_channel.instance_type"]
                channel_id = row["msg_sms_outbound_gateway.channel_id"]
            else:
                lookup_org = True
                org_branches = current.deployment_settings.get_org_branches()
                if org_branches:
                    org_parents = s3db.org_parents
                for row in rows:
                    channels[row["msg_sms_outbound_gateway.organisation_id"]] = \
                        dict(outgoing_sms_handler = row["msg_channel.instance_type"],
                             channel_id = row["msg_sms_outbound_gateway.channel_id"])

        elif contact_method == "TWITTER":
            twitter_settings = self.get_twitter_api()
            if not twitter_settings:
                # Raise exception here to make the scheduler
                # task fail permanently
                raise ValueError("No Twitter API available!")

        def dispatch_to_pe_id(pe_id,
                              subject,
                              message,
                              outbox_id,
                              message_id,
                              attachments = [],
                              organisation_id = None,
                              contact_method = contact_method,
                              channel_id = channel_id,
                              from_address = None,
                              outgoing_sms_handler = outgoing_sms_handler,
                              lookup_org = lookup_org,
                              channels = channels):
            """
                Helper method to send messages by pe_id

                @param pe_id: the pe_id
                @param subject: the message subject
                @param message: the message body
                @param outbox_id: the outbox record ID
                @param message_id: the message_id
                @param organisation_id: the organisation_id (for SMS)
                @param contact_method: the contact method
            """

            # Get the recipient's contact info
            table = s3db.pr_contact
            query = (table.pe_id == pe_id) & \
                    (table.contact_method == contact_method) & \
                    (table.deleted == False)
            contact_info = db(query).select(table.value,
                                            orderby=table.priority,
                                            limitby=(0, 1)).first()
            # Send the message
            if contact_info:
                address = contact_info.value
                if contact_method == "EMAIL":
                    return self.send_email(address,
                                           subject,
                                           message,
                                           sender = from_address,
                                           attachments = attachments,
                                           )
                elif contact_method == "SMS":
                    if lookup_org:
                        channel = channels.get(organisation_id)
                        if not channel and \
                            org_branches:
                            orgs = org_parents(organisation_id)
                            for org in orgs:
                                channel = channels.get(org)
                                if channel:
                                    break
                        if not channel:
                            # Look for an unrestricted channel
                            channel = channels.get(None)
                        if not channel:
                            # We can't send this message as there is no unrestricted channel & none which matches this Org
                            return False
                        outgoing_sms_handler = channel["outgoing_sms_handler"]
                        channel_id = channel["channel_id"]
                    if outgoing_sms_handler == "msg_sms_webapi_channel":
                        return self.send_sms_via_api(address,
                                                     message,
                                                     message_id,
                                                     channel_id)
                    elif outgoing_sms_handler == "msg_sms_smtp_channel":
                        return self.send_sms_via_smtp(address,
                                                      message,
                                                      channel_id)
                    elif outgoing_sms_handler == "msg_sms_modem_channel":
                        return self.send_sms_via_modem(address,
                                                       message,
                                                       channel_id)
                    elif outgoing_sms_handler == "msg_sms_tropo_channel":
                        # NB This does not mean the message is sent
                        return self.send_sms_via_tropo(outbox_id,
                                                       message_id,
                                                       address,
                                                       message,
                                                       channel_id)
                elif contact_method == "TWITTER":
                    return self.send_tweet(message, address)

            return False

        outbox = s3db.msg_outbox

        query = (outbox.contact_method == contact_method) & \
                (outbox.status == 1) & \
                (outbox.deleted == False)

        petable = s3db.pr_pentity
        left = [petable.on(petable.pe_id == outbox.pe_id)]

        fields = [outbox.id,
                  outbox.message_id,
                  outbox.pe_id,
                  outbox.retries,
                  petable.instance_type,
                  ]

        if contact_method == "EMAIL":
            mailbox = s3db.msg_email
            fields.extend([mailbox.subject, mailbox.body, mailbox.from_address])
            left.append(mailbox.on(mailbox.message_id == outbox.message_id))
        elif contact_method == "SMS":
            mailbox = s3db.msg_sms
            fields.append(mailbox.body)
            if lookup_org:
                fields.append(mailbox.organisation_id)
            left.append(mailbox.on(mailbox.message_id == outbox.message_id))
        elif contact_method == "TWITTER":
            mailbox = s3db.msg_twitter
            fields.append(mailbox.body)
            left.append(mailbox.on(mailbox.message_id == outbox.message_id))
        else:
            # @ToDo
            raise NotImplementedError

        rows = db(query).select(*fields,
                                left=left,
                                orderby=~outbox.retries)
        if not rows:
            return

        htable = s3db.table("hrm_human_resource")
        otable = s3db.org_organisation
        ptable = s3db.pr_person
        gtable = s3db.pr_group
        mtable = db.pr_group_membership
        ftable = s3db.pr_forum
        fmtable = db.pr_forum_membership

        # Left joins for multi-recipient lookups
        gleft = [mtable.on((mtable.group_id == gtable.id) & \
                           (mtable.person_id != None) & \
                           (mtable.deleted != True)),
                 ptable.on((ptable.id == mtable.person_id) & \
                           (ptable.deleted != True))
                 ]
        fleft = [fmtable.on((fmtable.forum_id == ftable.id) & \
                           (fmtable.person_id != None) & \
                           (fmtable.deleted != True)),
                 ptable.on((ptable.id == fmtable.person_id) & \
                           (ptable.deleted != True))
                 ]

        if htable:
            oleft = [htable.on((htable.organisation_id == otable.id) & \
                               (htable.person_id != None) & \
                               (htable.deleted != True)),
                     ptable.on((ptable.id == htable.person_id) & \
                               (ptable.deleted != True)),
                     ]

            etable = s3db.hrm_training_event
            ttable = s3db.hrm_training
            tleft = [ttable.on((ttable.training_event_id == etable.id) & \
                               (ttable.person_id != None) & \
                               (ttable.deleted != True)),
                     ptable.on((ptable.id == ttable.person_id) & \
                               (ptable.deleted != True)),
                     ]

            atable = s3db.table("deploy_alert")
            if atable:
                ltable = db.deploy_alert_recipient
                aleft = [ltable.on(ltable.alert_id == atable.id),
                         htable.on((htable.id == ltable.human_resource_id) & \
                                   (htable.person_id != None) & \
                                   (htable.deleted != True)),
                         ptable.on((ptable.id == htable.person_id) & \
                                   (ptable.deleted != True))
                         ]

        # chainrun: used to fire process_outbox again,
        # when messages are sent to groups or organisations
        chainrun = False

        # Set a default for non-SMS
        organisation_id = None
        attachment_table = s3db.msg_attachment
        document_table = s3db.doc_document
        file_field = document_table.file
        if file_field.custom_retrieve_file_properties:
            retrieve_file_properties = file_field.custom_retrieve_file_properties
        else:
            retrieve_file_properties = file_field.retrieve_file_properties
        mail_attachment = current.mail.Attachment

        for row in rows:
            attachments = []
            status = True
            message_id = row.msg_outbox.message_id

            if contact_method == "EMAIL":
                subject = row["msg_email.subject"] or ""
                message = row["msg_email.body"] or ""
                from_address = row["msg_email.from_address"] or ""
                query = (attachment_table.message_id == message_id) & \
                        (attachment_table.deleted != True) & \
                        (attachment_table.document_id == document_table.id) & \
                        (document_table.deleted != True)
                arows = db(query).select(file_field)
                for arow in arows:
                    file = arow.file
                    prop = retrieve_file_properties(file)
                    _file_path = os.path.join(prop["path"], file)
                    attachments.append(mail_attachment(_file_path))
            elif contact_method == "SMS":
                subject = None
                message = row["msg_sms.body"] or ""
                from_address = None
                if lookup_org:
                    organisation_id = row["msg_sms.organisation_id"]
            elif contact_method == "TWITTER":
                subject = None
                message = row["msg_twitter.body"] or ""
                from_address = None
            else:
                # @ToDo
                continue

            entity_type = row["pr_pentity"].instance_type
            if not entity_type:
                current.log.warning("s3msg", "Entity type unknown")
                continue

            row = row["msg_outbox"]
            pe_id = row.pe_id
            message_id = row.message_id

            if entity_type == "pr_person":
                # Send the message to this person
                try:
                    status = dispatch_to_pe_id(
                                    pe_id,
                                    subject,
                                    message,
                                    row.id,
                                    message_id,
                                    organisation_id = organisation_id,
                                    from_address = from_address,
                                    attachments = attachments,
                                    )
                except:
                    status = False

            elif entity_type == "pr_group":
                # Re-queue the message for each member in the group
                gquery = (gtable.pe_id == pe_id)
                recipients = db(gquery).select(ptable.pe_id, left=gleft)
                pe_ids = set(r.pe_id for r in recipients)
                pe_ids.discard(None)
                if pe_ids:
                    for pe_id in pe_ids:
                        outbox.insert(message_id=message_id,
                                      pe_id=pe_id,
                                      contact_method=contact_method,
                                      system_generated=True)
                    chainrun = True
                status = True

            elif entity_type == "pr_forum":
                # Re-queue the message for each member in the group
                fquery = (ftable.pe_id == pe_id)
                recipients = db(fquery).select(ptable.pe_id, left=fleft)
                pe_ids = set(r.pe_id for r in recipients)
                pe_ids.discard(None)
                if pe_ids:
                    for pe_id in pe_ids:
                        outbox.insert(message_id=message_id,
                                      pe_id=pe_id,
                                      contact_method=contact_method,
                                      system_generated=True)
                    chainrun = True
                status = True

            elif htable and entity_type == "org_organisation":
                # Re-queue the message for each HR in the organisation
                oquery = (otable.pe_id == pe_id)
                recipients = db(oquery).select(ptable.pe_id, left=oleft)
                pe_ids = set(r.pe_id for r in recipients)
                pe_ids.discard(None)
                if pe_ids:
                    for pe_id in pe_ids:
                        outbox.insert(message_id=message_id,
                                      pe_id=pe_id,
                                      contact_method=contact_method,
                                      system_generated=True)
                    chainrun = True
                status = True

            elif entity_type == "hrm_training_event":
                # Re-queue the message for each participant
                equery = (etable.pe_id == pe_id)
                recipients = db(equery).select(ptable.pe_id, left=tleft)
                pe_ids = set(r.pe_id for r in recipients)
                pe_ids.discard(None)
                if pe_ids:
                    for pe_id in pe_ids:
                        outbox.insert(message_id=message_id,
                                      pe_id=pe_id,
                                      contact_method=contact_method,
                                      system_generated=True)
                    chainrun = True
                status = True

            elif atable and entity_type == "deploy_alert":
                # Re-queue the message for each HR in the group
                aquery = (atable.pe_id == pe_id)
                recipients = db(aquery).select(ptable.pe_id, left=aleft)
                pe_ids = set(r.pe_id for r in recipients)
                pe_ids.discard(None)
                if pe_ids:
                    for pe_id in pe_ids:
                        outbox.insert(message_id=message_id,
                                      pe_id=pe_id,
                                      contact_method=contact_method,
                                      system_generated=True)
                    chainrun = True
                status = True

            else:
                # Unsupported entity type
                row.update_record(status = 4) # Invalid
                db.commit()
                continue

            if status:
                row.update_record(status = 2) # Sent
                db.commit()
            else:
                if row.retries > 0:
                    row.update_record(retries = row.retries - 1)
                    db.commit()
                elif row.retries is not None:
                    row.update_record(status = 5) # Failed

        if chainrun:
            self.process_outbox(contact_method)

    # -------------------------------------------------------------------------
    # Google Cloud Messaging Push
    # -------------------------------------------------------------------------
    def gcm_push(self, title=None, uri=None, message=None, registration_ids=None, channel_id=None):
        """
            Push the message relating to google cloud messaging server

            @param title: The title for notification
            @param message: The message to be sent to GCM server
            @param api_key: The API key for GCM server
            @param registration_ids: The list of id that will be notified
            @param channel_id: The specific channel_id to use for GCM push
        """

        if not title or not uri or not message or not len(registration_ids):
            return

        from gcm import GCM
        gcmtable = current.s3db.msg_gcm_channel
        if channel_id:
            query = (gcmtable.channel_id == channel_id)
        else:
            query = (gcmtable.enabled == True) & (gcmtable.deleted != True)

        row = current.db(query).select(gcmtable.api_key,
                                       limitby=(0, 1)).first()
        try:
            gcm = GCM(row.api_key)
        except Exception as e:
            current.log.error("No API Key configured for GCM: ", e)
        else:
            try:
                # @ToDo: Store notification in outbox if-required
                # @ToDo: Implement other methods for GCM as required
                # See: https://github.com/geeknam/python-gcm
                notification = {"title": title,
                                "message": message,
                                "uri": uri,
                                }
                response = gcm.json_request(registration_ids=registration_ids,
                                            data=notification)
            except Exception as e:
                current.log.error("Google Cloud Messaging Error", e)
            else:
                if "errors" in response:
                    for error, reg_ids in response["errors"].items():
                        for reg_id in reg_ids:
                            current.log.error("Google Cloud Messaging Error: %s for Registration ID %s" % (error, reg_id))
                # @ToDo: Handle for canonical when required
                #if "canonical" in response:
                #    for reg_id, canonical_id in response["canonical"].items():
                        # @ToDo: Replace registration_id with canonical_id
        return

    # -------------------------------------------------------------------------
    # Send Email
    # -------------------------------------------------------------------------
    def send_email(self,
                   to,
                   subject,
                   message,
                   attachments = None,
                   cc = None,
                   bcc = None,
                   reply_to = None,
                   sender = None,
                   encoding = "utf-8",
                   #from_address = None,
                   ):
        """
            Function to send Email
            - simple Wrapper over Web2Py's Email API
        """

        if not to:
            return False

        settings = current.deployment_settings

        default_sender = settings.get_mail_sender()
        if not default_sender:
            current.log.warning("Email sending disabled until the Sender address has been set in models/000_config.py")
            return False

        if not sender:
            sender = default_sender
        sender = self.sanitize_sender(sender)

        limit = settings.get_mail_limit()
        if limit:
            # Check whether we've reached our daily limit
            day = datetime.timedelta(hours=24)
            cutoff = current.request.utcnow - day
            table = current.s3db.msg_channel_limit
            # @ToDo: Include Channel Info
            check = current.db(table.created_on > cutoff).count()
            if check >= limit:
                return False
            # Log the sending
            table.insert()

        result = current.mail.send(to,
                                   subject = subject,
                                   message = message,
                                   attachments = attachments,
                                   cc = cc,
                                   bcc = bcc,
                                   reply_to = reply_to,
                                   sender = sender,
                                   encoding = encoding,
                                   # e.g. Return-Receipt-To:<user@domain>
                                   headers = {},
                                   # Added to Web2Py 2014-03-04
                                   # - defaults to sender
                                   #from_address = from_address,
                                   )
        if not result:
            current.session.error = current.mail.error
        else:
            current.session.error = None

        return result

    # -------------------------------------------------------------------------
    @staticmethod
    def sanitize_sender(sender):
        """
            Sanitize the email sender string to prevent MIME-encoding
            of the from-address (RFC2047)

            @param: the sender-string
            @returns: the sanitized sender-string
        """

        if not sender:
            return sender
        match = SENDER.match(sender)
        if match:
            sender_name, from_address = match.groups()
            if any(32 > ord(c) or ord(c) > 127 for c in sender_name):
                from email.header import Header
                sender_name = Header(sender_name.strip(), "utf-8")
            else:
                sender_name = sender_name.strip()
            sender = "%s <%s>" % (sender_name, from_address.strip())
        return sender

    # -------------------------------------------------------------------------
    def send_email_by_pe_id(self,
                            pe_id,
                            subject="",
                            message="",
                            from_address=None,
                            system_generated=False):
        """
            API wrapper over send_by_pe_id
        """

        return self.send_by_pe_id(pe_id,
                                  subject,
                                  message,
                                  "EMAIL",
                                  from_address,
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

        words = message.split(" ")
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
    def send_sms_via_api(self,
                         mobile,
                         text = "",
                         message_id = None,
                         channel_id = None,
                         ):
        """
            Function to send SMS via Web API
        """

        db = current.db
        s3db = current.s3db
        table = s3db.msg_sms_webapi_channel

        # Get Configuration
        if channel_id:
            sms_api = db(table.channel_id == channel_id).select(limitby=(0, 1)
                                                                ).first()
        else:
            # @ToDo: Check for Organisation-specific Gateway
            sms_api = db(table.enabled == True).select(limitby=(0, 1)).first()
        if not sms_api:
            return False

        post_data = {}

        parts = sms_api.parameters.split("&")
        for p in parts:
            post_data[p.split("=")[0]] = p.split("=")[1]

        mobile = self.sanitise_phone(mobile, channel_id)

        # To send non-ASCII characters in UTF-8 encoding, we'd need
        # to hex-encode the text and activate unicode=1, but this
        # would limit messages to 70 characters, and many mobile
        # phones can't display unicode anyway.

        # To be however able to send messages with at least special
        # European characters like á or ø,  we convert the UTF-8 to
        # the default ISO-8859-1 (latin-1) here:
        text_latin1 = s3_unicode(text).encode("utf-8") \
                                      .decode("utf-8") \
                                      .encode("iso-8859-1")

        post_data[sms_api.message_variable] = text_latin1
        post_data[sms_api.to_variable] = str(mobile)

        url = sms_api.url
        clickatell = "clickatell" in url
        if clickatell:
            text_len = len(text)
            if text_len > 480:
                current.log.error("Clickatell messages cannot exceed 480 chars")
                return False
            elif text_len > 320:
                post_data["concat"] = 3
            elif text_len > 160:
                post_data["concat"] = 2

        request = urllib2.Request(url)
        query = urlencode(post_data)
        if sms_api.username and sms_api.password:
            # e.g. Mobile Commons
            base64string = base64.encodestring("%s:%s" % (sms_api.username, sms_api.password)).replace("\n", "")
            request.add_header("Authorization", "Basic %s" % base64string)
        try:
            result = urlopen(request, query)
        except HTTPError as e:
            current.log.error("SMS message send failed: %s" % e)
            return False
        else:
            # Parse result
            output = result.read()
            if clickatell:
                if output.startswith("ERR"):
                    current.log.error("Clickatell message send failed: %s" % output)
                    return False
                elif message_id and output.startswith("ID"):
                    # Store ID from Clickatell to be able to followup
                    remote_id = output[4:]
                    db(s3db.msg_sms.message_id == message_id).update(remote_id=remote_id)
            elif "mcommons" in url:
                # http://www.mobilecommons.com/mobile-commons-api/rest/#errors
                # Good = <response success="true"></response>
                # Bad = <response success="false"><errror id="id" message="message"></response>
                if "error" in output:
                    current.log.error("Mobile Commons message send failed: %s" % output)
                    return False

            return True

    # -------------------------------------------------------------------------
    def send_sms_via_modem(self, mobile, text="", channel_id=None):
        """
            Function to send SMS via locally-attached Modem
            - needs to have the cron/sms_handler_modem.py script running
        """

        mobile = self.sanitise_phone(mobile, channel_id)

        # Add '+' before country code
        mobile = "+%s" % mobile

        try:
            self.modem.send_sms(mobile, text)
            return True
        except KeyError:
            current.log.error("s3msg", "Modem not available: need to have the cron/sms_handler_modem.py script running")
            return False

    # -------------------------------------------------------------------------
    def send_sms_via_smtp(self, mobile, text="", channel_id=None):
        """
            Function to send SMS via SMTP

            NB Different Gateways have different requirements for presence/absence of International code

            http://en.wikipedia.org/wiki/List_of_SMS_gateways
            http://www.obviously.com/tech_tips/SMS_Text_Email_Gateway.html
        """

        table = current.s3db.msg_sms_smtp_channel
        if channel_id:
            query = (table.channel_id == channel_id)
        else:
            query = (table.enabled == True)
        settings = current.db(query).select(limitby=(0, 1)
                                            ).first()
        if not settings:
            return False

        mobile = self.sanitise_phone(mobile, channel_id)

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
    def send_sms_via_tropo(self,
                           row_id,
                           message_id,
                           recipient,
                           message,
                           network = "SMS",
                           channel_id = None,
                           ):
        """
            Send a URL request to Tropo to pick a message up
        """

        db = current.db
        s3db = current.s3db
        table = s3db.msg_tropo_channel

        base_url = "http://api.tropo.com/1.0/sessions"
        action = "create"

        if channel_id:
            query = (table.channel_id == channel_id)
        else:
            query = (table.enabled == True)
        tropo_settings = db(query).select(table.token_messaging,
                                          limitby=(0, 1)).first()
        if tropo_settings:
            tropo_token_messaging = tropo_settings.token_messaging
            #tropo_token_voice = tropo_settings.token_voice
        else:
            return

        if network == "SMS":
            recipient = self.sanitise_phone(recipient, channel_id)

        try:
            s3db.msg_tropo_scratch.insert(row_id = row_id,
                                          message_id = message_id,
                                          recipient = recipient,
                                          message = message,
                                          network = network)
            params = urlencode([("action", action),
                                ("token", tropo_token_messaging),
                                ("outgoing", "1"),
                                ("row_id", row_id)
                                ])
            xml = urlopen("%s?%s" % (base_url, params)).read()
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

        # Return False because the API needs to ask us for the messsage again.
        return False

    # -------------------------------------------------------------------------
    def send_sms_by_pe_id(self,
                          pe_id,
                          message="",
                          from_address=None,
                          system_generated=False):
        """
            API wrapper over send_by_pe_id
        """

        return self.send_by_pe_id(pe_id,
                                  subject = "",
                                  message = message,
                                  contact_method = "SMS",
                                  from_address = from_address,
                                  system_generated = system_generated,
                                  )

    # -------------------------------------------------------------------------
    # Twitter
    # -------------------------------------------------------------------------
    @staticmethod
    def _sanitise_twitter_account(account):
        """
            Only keep characters that are legal for a twitter account:
            letters, digits, and _
        """

        if PY2:
            return account.translate(IDENTITYTRANS, NOTTWITTERCHARS)
        else:
            return "".join(c for c in account if c in TWITTERCHARS)

    # -------------------------------------------------------------------------
    @staticmethod
    def _break_to_chunks(text,
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
                res.append(current_prefix + c.rstrip() + s3_str(suffix))
                current_prefix = s3_str(prefix) # from now on, we want a prefix

    # -------------------------------------------------------------------------
    @staticmethod
    def get_twitter_api(channel_id=None):
        """
            Initialize Twitter API
        """

        try:
            import tweepy
        except ImportError:
            current.log.error("s3msg", "Tweepy not available, so non-Tropo Twitter support disabled")
            return None

        table = current.s3db.msg_twitter_channel
        if not channel_id:
            # Try the 1st enabled one in the DB
            query = (table.enabled == True)
            limitby = None
        else:
            query = (table.channel_id == channel_id)
            limitby = (0, 1)

        rows = current.db(query).select(table.login,
                                        table.twitter_account,
                                        table.consumer_key,
                                        table.consumer_secret,
                                        table.access_token,
                                        table.access_token_secret,
                                        limitby=limitby
                                        )
        if len(rows) == 1:
            c = rows.first()
        elif not len(rows):
            current.log.error("s3msg", "No Twitter channels configured")
            return None
        else:
            # Filter to just the login channel
            rows.exclude(lambda row: row.login != True)
            if len(rows) == 1:
                c = rows.first()
            elif not len(rows):
                current.log.error("s3msg", "No Twitter channels configured for login")
                return None

        if not c.consumer_key:
            current.log.error("s3msg", "Twitter channel has no consumer key")
            return None

        try:
            oauth = tweepy.OAuthHandler(c.consumer_key,
                                        c.consumer_secret)
            oauth.set_access_token(c.access_token,
                                   c.access_token_secret)
            twitter_api = tweepy.API(oauth)
            return (twitter_api, c.twitter_account)
        except:
            return None

    # -------------------------------------------------------------------------
    def send_tweet(self, text="", recipient=None, **data):
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

        import tweepy

        twitter_api = twitter_settings[0]
        twitter_account = twitter_settings[1]

        from_address = twitter_api.me().screen_name

        db = current.db
        s3db = current.s3db
        table = s3db.msg_twitter
        otable = s3db.msg_outbox

        message_id = None

        def log_tweet(tweet, recipient, from_address):
            # Log in msg_twitter
            _id = table.insert(body=tweet,
                               from_address=from_address,
                               )
            record = db(table.id == _id).select(table.id,
                                                limitby=(0, 1)
                                                ).first()
            s3db.update_super(table, record)
            message_id = record.message_id

            # Log in msg_outbox
            otable.insert(message_id = message_id,
                          address = recipient,
                          status = 2,
                          contact_method = "TWITTER",
                          )
            return message_id

        if recipient:
            recipient = self._sanitise_twitter_account(recipient)
            try:
                can_dm = recipient == twitter_account or \
                         twitter_api.get_user(recipient).id in twitter_api.followers_ids(twitter_account)
            except tweepy.TweepError:
                # recipient not found
                return False
            if can_dm:
                chunks = self._break_to_chunks(text)
                for c in chunks:
                    try:
                        # Note: send_direct_message() requires explicit kwargs (at least in tweepy 1.5)
                        # See http://groups.google.com/group/tweepy/msg/790fcab8bc6affb5
                        if twitter_api.send_direct_message(screen_name=recipient,
                                                           text=c):
                            message_id = log_tweet(c, recipient, from_address)

                    except tweepy.TweepError:
                        current.log.error("Unable to Tweet DM")
            else:
                prefix = "@%s " % recipient
                chunks = self._break_to_chunks(text,
                                               TWITTER_MAX_CHARS - len(prefix))
                for c in chunks:
                    try:
                        twitter_api.update_status("%s %s" % prefix, c)
                    except tweepy.TweepError:
                        current.log.error("Unable to Tweet @mention")
                    else:
                        message_id = log_tweet(c, recipient, from_address)
        else:
            chunks = self._break_to_chunks(text)
            for c in chunks:
                try:
                    twitter_api.update_status(c)
                except tweepy.TweepError:
                    current.log.error("Unable to Tweet")
                else:
                    message_id = log_tweet(c, recipient, from_address)

        # Perform post process after message sending
        if message_id:
            postp = current.deployment_settings.get_msg_send_postprocess()
            if postp:
                postp(message_id, **data)

        return True

    #------------------------------------------------------------------------------
    def post_to_facebook(self, text="", channel_id=None, recipient=None, **data):
        """
            Posts a message on Facebook

            https://developers.facebook.com/docs/graph-api
        """

        db = current.db
        s3db = current.s3db
        table = s3db.msg_facebook_channel
        if not channel_id:
            # Try the 1st enabled one in the DB
            query = (table.enabled == True)
        else:
            query = (table.channel_id == channel_id)

        c = db(query).select(table.app_id,
                             table.app_secret,
                             table.page_id,
                             table.page_access_token,
                             limitby=(0, 1)
                             ).first()

        import facebook

        try:
            app_access_token = facebook.get_app_access_token(c.app_id,
                                                             c.app_secret)
        except:
            message = sys.exc_info()[1]
            current.log.error("S3MSG: %s" % message)
            return

        table = s3db.msg_facebook
        otable = s3db.msg_outbox

        message_id = None

        def log_facebook(post, recipient, from_address):
            # Log in msg_facebook
            _id = table.insert(body=post,
                               from_address=from_address,
                               )
            record = db(table.id == _id).select(table.id,
                                                limitby=(0, 1)
                                                ).first()
            s3db.update_super(table, record)
            message_id = record.message_id

            # Log in msg_outbox
            otable.insert(message_id = message_id,
                          address = recipient,
                          status = 2,
                          contact_method = "FACEBOOK",
                          )
            return message_id

        graph = facebook.GraphAPI(app_access_token)

        page_id = c.page_id
        if page_id:
            graph = facebook.GraphAPI(c.page_access_token)
            graph.put_object(page_id, "feed", message=text)
        else:
            # FIXME user_id does not exist:
            #graph.put_object(user_id, "feed", message=text)
            raise NotImplementedError

        message_id = log_facebook(text, recipient, channel_id)

        # Perform post process after message sending
        if message_id:
            postp = current.deployment_settings.get_msg_send_postprocess()
            if postp:
                postp(message_id, **data)

    # -------------------------------------------------------------------------
    def poll(self, tablename, channel_id):
        """
            Poll a Channel for New Messages
        """

        channel_type = tablename.split("_", 2)[1]
        # Launch the correct Poller
        function_name = "poll_%s" % channel_type
        try:
            fn = getattr(S3Msg, function_name)
        except:
            error = "Unsupported Channel: %s" % channel_type
            current.log.error(error)
            return error

        result = fn(channel_id)
        return result

    # -------------------------------------------------------------------------
    @staticmethod
    def poll_email(channel_id):
        """
            This is a simple mailbox polling script for the Messaging Module.
            It is normally called from the scheduler.

            @ToDo: If there is a need to collect from non-compliant mailers
                   then suggest using the robust Fetchmail to collect & store
                   in a more compliant mailer!
            @ToDo: If delete_from_server is false, we don't want to download the
                   same messages repeatedly.  Perhaps record time of fetch runs
                   (or use info from the scheduler_run table), compare w/ message
                   timestamp, as a filter. That may not be completely accurate,
                   so could check msg_email for messages close to the last
                   fetch time. Or just advise people to have a dedicated account
                   to which email is sent, that does not also need to be read
                   by humans. Or don't delete the fetched mail until the next run.
        """

        db = current.db
        s3db = current.s3db

        table = s3db.msg_email_channel
        # Read-in configuration from Database
        query = (table.channel_id == channel_id)
        channel = db(query).select(table.username,
                                   table.password,
                                   table.server,
                                   table.protocol,
                                   table.use_ssl,
                                   table.port,
                                   table.delete_from_server,
                                   limitby=(0, 1)
                                   ).first()
        if not channel:
            return "No Such Email Channel: %s" % channel_id

        import email
        #import mimetypes
        import socket

        from dateutil import parser
        date_parse = parser.parse

        username = channel.username
        password = channel.password
        host = channel.server
        protocol = channel.protocol
        ssl = channel.use_ssl
        port = int(channel.port)
        delete = channel.delete_from_server

        mtable = db.msg_email
        minsert = mtable.insert
        stable = db.msg_channel_status
        sinsert = stable.insert
        atable = s3db.msg_attachment
        ainsert = atable.insert
        dtable = db.doc_document
        dinsert = dtable.insert
        store = dtable.file.store
        update_super = s3db.update_super
        # Is this channel connected to a parser?
        parser = s3db.msg_parser_enabled(channel_id)
        if parser:
            ptable = db.msg_parsing_status
            pinsert = ptable.insert

        # ---------------------------------------------------------------------
        def parse_email(message):
            """
                Helper to parse the mail
            """

            # Create a Message object
            msg = email.message_from_string(message)
            # Parse the Headers
            sender = msg["from"]
            subject = msg.get("subject", "")
            date_sent = msg.get("date", None)
            # Store the whole raw message
            raw = msg.as_string()
            # Parse out the 'Body'
            # Look for Attachments
            attachments = []
            # http://docs.python.org/2/library/email-examples.html
            body = ""
            for part in msg.walk():
                if part.get_content_maintype() == "multipart":
                    # multipart/* are just containers
                    continue
                filename = part.get_filename()
                if not filename:
                    # Assume this is the Message Body (plain text or HTML)
                    if not body:
                        # Plain text will come first
                        body = part.get_payload(decode=True)
                    continue
                attachments.append((filename, part.get_payload(decode=True)))

            # Store in DB
            data = {"channel_id": channel_id,
                    "from_address": sender,
                    "subject": subject[:78],
                    "body": body,
                    "raw": raw,
                    "inbound": True,
                    }
            if date_sent:
                data["date"] = date_parse(date_sent)
            _id = minsert(**data)
            record = {"id": _id}
            update_super(mtable, record)
            message_id = record["message_id"]
            for a in attachments:
                # Linux ext2/3 max filename length = 255
                # b16encode doubles length & need to leave room for doc_document.file.16charsuuid.
                # store doesn't support unicode, so need an ascii string
                filename = s3_unicode(a[0][:92]).encode("ascii", "ignore")
                fp = StringIO()
                fp.write(a[1])
                fp.seek(0)
                newfilename = store(fp, filename)
                fp.close()
                document_id = dinsert(name = filename,
                                      file = newfilename)
                update_super(dtable, {"id": document_id})
                ainsert(message_id = message_id,
                        document_id = document_id)
            if parser:
                pinsert(message_id = message_id,
                        channel_id = channel_id)

        dellist = []
        if protocol == "pop3":
            # http://docs.python.org/library/poplib.html
            import poplib
            # https://stackoverflow.com/questions/30976106/python-poplib-error-proto-line-too-long
            poplib._MAXLINE = 20480
            try:
                if ssl:
                    p = poplib.POP3_SSL(host, port)
                else:
                    p = poplib.POP3(host, port)
            except socket.error as e:
                error = "Cannot connect: %s" % e
                current.log.error(error)
                # Store status in the DB
                sinsert(channel_id = channel_id,
                        status = error)
                return error
            except poplib.error_proto as e:
                # Something else went wrong - probably transient (have seen '-ERR EOF' here)
                current.log.error("Email poll failed: %s" % e)
                return

            try:
                # Attempting APOP authentication...
                p.apop(username, password)
            except poplib.error_proto:
                # Attempting standard authentication...
                try:
                    p.user(username)
                    p.pass_(password)
                except poplib.error_proto as e:
                    error = "Login failed: %s" % e
                    current.log.error(error)
                    # Store status in the DB
                    sinsert(channel_id = channel_id,
                            status = error)
                    return error

            mblist = p.list()[1]
            for item in mblist:
                number, octets = item.split(" ")
                # Retrieve the message (storing it in a list of lines)
                lines = p.retr(number)[1]
                parse_email("\n".join(lines))
                if delete:
                    # Add it to the list of messages to delete later
                    dellist.append(number)
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
            except socket.error as e:
                error = "Cannot connect: %s" % e
                current.log.error(error)
                # Store status in the DB
                sinsert(channel_id = channel_id,
                        status = error)
                return error

            try:
                M.login(username, password)
            except M.error as e:
                error = "Login failed: %s" % e
                current.log.error(error)
                # Store status in the DB
                sinsert(channel_id = channel_id,
                        status = error)
                # Explicitly commit DB operations when running from Cron
                db.commit()
                return error

            # Select inbox
            M.select()
            # Search for Messages to Download
            typ, data = M.search(None, "ALL")
            mblist = data[0].split()
            for number in mblist:
                typ, msg_data = M.fetch(number, "(RFC822)")
                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        parse_email(response_part[1])
                        if delete:
                            # Add it to the list of messages to delete later
                            dellist.append(number)
            # Iterate over the list of messages to delete
            for number in dellist:
                typ, response = M.store(number, "+FLAGS", r"(\Deleted)")
            M.close()
            M.logout()

    # -------------------------------------------------------------------------
    @staticmethod
    def poll_mcommons(channel_id):
        """
            Fetches the inbound SMS from Mobile Commons API
            http://www.mobilecommons.com/mobile-commons-api/rest/#ListIncomingMessages
        """

        db = current.db
        s3db = current.s3db
        table = s3db.msg_mcommons_channel
        query = (table.channel_id == channel_id)
        channel = db(query).select(table.url,
                                   table.campaign_id,
                                   table.username,
                                   table.password,
                                   table.query,
                                   table.timestmp,
                                   limitby=(0, 1)).first()
        if not channel:
            return "No Such MCommons Channel: %s" % channel_id

        url = channel.url
        username = channel.username
        password = channel.password
        _query = channel.query
        timestamp = channel.timestmp

        url = "%s?campaign_id=%s" % (url, channel.campaign_id)
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

        try:
            _response = urlopen(url)
        except HTTPError as e:
            return "Error: %s" % e.code
        else:
            sms_xml = _response.read()
            tree = etree.XML(sms_xml)
            messages = tree.findall(".//message")

            mtable = s3db.msg_sms
            minsert = mtable.insert
            update_super = s3db.update_super
            decode = s3_decode_iso_datetime

            # Is this channel connected to a parser?
            parser = s3db.msg_parser_enabled(channel_id)
            if parser:
                ptable = db.msg_parsing_status
                pinsert = ptable.insert

            for message in messages:
                sender_phone = message.find("phone_number").text
                body = message.find("body").text
                received_on = decode(message.find("received_at").text)
                _id = minsert(channel_id = channel_id,
                              sender_phone = sender_phone,
                              body = body,
                              received_on = received_on,
                              )
                record = dict(id=_id)
                update_super(mtable, record)
                if parser:
                    pinsert(message_id = record["message_id"],
                            channel_id = channel_id)

        return "OK"

    # -------------------------------------------------------------------------
    @staticmethod
    def poll_twilio(channel_id):
        """
            Fetches the inbound SMS from Twilio API
            http://www.twilio.com/docs/api/rest
        """

        db = current.db
        s3db = current.s3db
        table = s3db.msg_twilio_channel
        query = (table.channel_id == channel_id)
        channel = db(query).select(table.account_sid,
                                   table.auth_token,
                                   table.url,
                                   limitby=(0, 1)).first()
        if not channel:
            return "No Such Twilio Channel: %s" % channel_id

        # @ToDo: Do we really have to download *all* messages every time
        # & then only import the ones we don't yet have?
        account_sid = channel.account_sid
        url = "%s/%s/SMS/Messages.json" % (channel.url, account_sid)

        # Create a password manager
        passman = urllib2.HTTPPasswordMgrWithDefaultRealm()
        passman.add_password(None, url, account_sid, channel.auth_token)

        # Create the AuthHandler
        authhandler = urllib2.HTTPBasicAuthHandler(passman)
        opener = urllib2.build_opener(authhandler)
        urllib2.install_opener(opener)

        try:
            smspage = urlopen(url)
        except HTTPError as e:
            error = "Error: %s" % e.code
            current.log.error(error)
            # Store status in the DB
            S3Msg.update_channel_status(channel_id,
                                        status=error,
                                        period=(300, 3600))
            return error
        else:
            sms_list = json.loads(smspage.read())
            messages = sms_list["sms_messages"]
            # Find all the SIDs we have already downloaded
            # (even if message was deleted)
            stable = db.msg_twilio_sid
            sids = db(stable.id > 0).select(stable.sid)
            downloaded_sms = [s.sid for s in sids]

            mtable = s3db.msg_sms
            minsert = mtable.insert
            sinsert = stable.insert
            update_super = s3db.update_super

            # Is this channel connected to a parser?
            parser = s3db.msg_parser_enabled(channel_id)
            if parser:
                ptable = db.msg_parsing_status
                pinsert = ptable.insert

            for sms in messages:
                if (sms["direction"] == "inbound") and \
                   (sms["sid"] not in downloaded_sms):
                    sender = "<" + sms["from"] + ">"
                    _id = minsert(channel_id=channel_id,
                                  body=sms["body"],
                                  status=sms["status"],
                                  from_address=sender,
                                  received_on=sms["date_sent"])
                    record = dict(id=_id)
                    update_super(mtable, record)
                    message_id = record["message_id"]
                    sinsert(message_id = message_id,
                            sid=sms["sid"])
                    if parser:
                        pinsert(message_id = message_id,
                                channel_id = channel_id)
        return "OK"

    # -------------------------------------------------------------------------
    @staticmethod
    def poll_rss(channel_id):
        """
            Fetches all new messages from a subscribed RSS Feed
        """

        db = current.db
        s3db = current.s3db
        table = s3db.msg_rss_channel
        query = (table.channel_id == channel_id)
        channel = db(query).select(table.date,
                                   table.etag,
                                   table.url,
                                   table.content_type,
                                   table.username,
                                   table.password,
                                   limitby=(0, 1)).first()
        if not channel:
            return "No Such RSS Channel: %s" % channel_id

        # http://pythonhosted.org/feedparser
        if PY2:
            # Use Stable v5.2.1
            # - current known reason is to prevent SSL: CERTIFICATE_VERIFY_FAILED
            import feedparser521 as feedparser
        else:
            # Python 3.x: Requires pip install sgmllib3k
            if sys.version_info[1] >= 7:
                # Use 6.0.0b1 which is required for Python 3.7
                import feedparser
            else:
                # Python 3.6 requires 5.2.1 with 2to3 run on it to prevent SSL: CERTIFICATE_VERIFY_FAILED
                import feedparser5213 as feedparser

        # Basic Authentication
        username = channel.username
        password = channel.password
        if username and password:
            # feedparser doesn't do pre-emptive authentication with urllib2.HTTPBasicAuthHandler() and throws errors on the 401
            base64string = base64.encodestring("%s:%s" % (username, password)).replace("\n", "")
            request_headers = {"Authorization": "Basic %s" % base64string}
        else:
            # Doesn't help to encourage servers to set correct content-type
            #request_headers = {"Accept": "application/xml"}
            request_headers = None

        if channel.content_type:
            # Override content-type (some feeds have text/html set which feedparser refuses to parse)
            response_headers = {"content-type": "application/xml"}
        else:
            response_headers = None

        if channel.etag:
            # http://pythonhosted.org/feedparser/http-etag.html
            # NB This won't help for a server like Drupal 7 set to not allow caching & hence generating a new ETag/Last Modified each request!
            d = feedparser.parse(channel.url,
                                 etag = channel.etag,
                                 request_headers = request_headers,
                                 response_headers = response_headers,
                                 )
        elif channel.date:
            d = feedparser.parse(channel.url,
                                 modified = channel.date.utctimetuple(),
                                 request_headers = request_headers,
                                 response_headers = response_headers,
                                 )
        else:
            # We've not polled this feed before
            d = feedparser.parse(channel.url,
                                 request_headers = request_headers,
                                 response_headers = response_headers,
                                 )
        if d.bozo:
            # Something doesn't seem right
            if PY2:
                status = "ERROR: %s" % d.bozo_exception.message
            else:
                status = "ERROR: %s" % d.bozo_exception
            S3Msg.update_channel_status(channel_id,
                                        status = status,
                                        period = (300, 3600),
                                        )
            return

        # Update ETag/Last-polled
        now = current.request.utcnow
        data = {"date": now}
        etag = d.get("etag", None)
        if etag:
            data["etag"] = etag
        db(query).update(**data)

        from time import mktime, struct_time
        gis = current.gis
        geocode_r = gis.geocode_r
        hierarchy_level_keys = gis.hierarchy_level_keys
        utcfromtimestamp = datetime.datetime.utcfromtimestamp
        gtable = db.gis_location
        ginsert = gtable.insert
        mtable = db.msg_rss
        minsert = mtable.insert
        ltable = db.msg_rss_link
        linsert = ltable.insert
        update_super = s3db.update_super

        # Is this channel connected to a parser?
        parser = s3db.msg_parser_enabled(channel_id)
        if parser:
            ptable = db.msg_parsing_status
            pinsert = ptable.insert

        entries = d.entries
        if entries:
            # Check how many we have already to see if any are new
            count_old = db(mtable.id > 0).count()
        for entry in entries:
            link = entry.get("link", None)

            # Check for duplicates
            # (ETag just saves bandwidth, doesn't filter the contents of the feed)
            exists = db(mtable.from_address == link).select(mtable.id,
                                                            mtable.location_id,
                                                            mtable.message_id,
                                                            limitby=(0, 1)
                                                            ).first()
            if exists:
                location_id = exists.location_id
            else:
                location_id = None

            title = entry.get("title")

            content = entry.get("content", None)
            if content:
                content = content[0].value
            else:
                content = entry.get("description", None)

            # Consider using dateutil.parser.parse(entry.get("published"))
            # http://www.deadlybloodyserious.com/2007/09/feedparser-v-django/
            date_published = entry.get("published_parsed", entry.get("updated_parsed"))
            if isinstance(date_published, struct_time):
                date_published = utcfromtimestamp(mktime(date_published))
            else:
                date_published = now

            tags = entry.get("tags", None)
            if tags:
                tags = [t.term.encode("utf-8") for t in tags]

            location = False
            lat = entry.get("geo_lat", None)
            lon = entry.get("geo_long", None)
            if lat is None or lon is None:
                # Try GeoRSS
                georss = entry.get("georss_point", None)
                if georss:
                    location = True
                    lat, lon = georss.split(" ")
            else:
                location = True
            if location:
                try:
                    query = (gtable.lat == lat) &\
                            (gtable.lon == lon)
                    lexists = db(query).select(gtable.id,
                                               limitby=(0, 1),
                                               orderby=gtable.level,
                                               ).first()
                    if lexists:
                        location_id = lexists.id
                    else:
                        data = dict(lat=lat,
                                    lon=lon,
                                    )
                        results = geocode_r(lat, lon)
                        if isinstance(results, dict):
                            for key in hierarchy_level_keys:
                                v = results.get(key, None)
                                if v:
                                    data[key] = v
                        #if location_id:
                        # Location has been changed
                        #db(gtable.id == location_id).update(**data)
                        location_id = ginsert(**data)
                        data["id"] = location_id
                        gis.update_location_tree(data)
                except:
                    # Don't die on badly-formed Geo
                    pass

            # Get links - these can be multiple with certain type
            links = entry.get("links", [])
            if exists:
                db(mtable.id == exists.id).update(channel_id = channel_id,
                                                  title = title,
                                                  from_address = link,
                                                  body = content,
                                                  author = entry.get("author", None),
                                                  date = date_published,
                                                  location_id = location_id,
                                                  tags = tags,
                                                  # @ToDo: Enclosures
                                                  )
                if links:
                    query_ = (ltable.rss_id == exists.id) & (ltable.deleted != True)
                    for link_ in links:
                        url_ = link_["url"]
                        type_ = link_["type"]
                        query = query_ & (ltable.url == url_) & \
                                (ltable.type == type_)
                        dbset = db(query)
                        row = dbset.select(ltable.id, limitby=(0, 1)).first()
                        if row:
                            dbset.update(rss_id = exists.id,
                                         url = url_,
                                         type = type_,
                                         )
                        else:
                            linsert(rss_id = exists.id,
                                    url = url_,
                                    type = type_,
                                    )
                if parser:
                    pinsert(message_id = exists.message_id,
                            channel_id = channel_id)

            else:
                _id = minsert(channel_id = channel_id,
                              title = title,
                              from_address = link,
                              body = content,
                              author = entry.get("author", None),
                              date = date_published,
                              location_id = location_id,
                              tags = tags,
                              # @ToDo: Enclosures
                              )
                record = dict(id=_id)
                update_super(mtable, record)
                for link_ in links:
                    linsert(rss_id = _id,
                            url = link_["url"],
                            type = link_["type"],
                            )
                if parser:
                    pinsert(message_id = record["message_id"],
                            channel_id = channel_id)

        if entries:
            # Check again to see if there were any new ones
            count_new = db(mtable.id > 0).count()
            if count_new == count_old:
                # No new posts?
                # Back-off in-case the site isn't respecting ETags/Last-Modified
                S3Msg.update_channel_status(channel_id,
                                            status="+1",
                                            period=(300, 3600))

        return "OK"

    #-------------------------------------------------------------------------
    @staticmethod
    def poll_twitter(channel_id):
        """
            Function  to call to fetch tweets into msg_twitter table
            - called via Scheduler or twitter_inbox controller

            http://tweepy.readthedocs.org/en/v3.3.0/api.html
        """

        try:
            import tweepy
        except ImportError:
            current.log.error("s3msg", "Tweepy not available, so non-Tropo Twitter support disabled")
            return False

        db = current.db
        s3db = current.s3db

        # Initialize Twitter API
        twitter_settings = S3Msg.get_twitter_api(channel_id)
        if twitter_settings:
            # This is an account with login info, so pull DMs
            dm = True
        else:
            # This is can account without login info, so pull public tweets
            dm = False
            table = s3db.msg_twitter_channel
            channel = db(table.channel_id == channel_id).select(table.twitter_account,
                                                                limitby=(0, 1)
                                                                ).first()
            screen_name = channel.twitter_account
            # Authenticate using login account
            twitter_settings = S3Msg.get_twitter_api()
            if twitter_settings is None:
                # Cannot authenticate
                return False

        twitter_api = twitter_settings[0]

        table = s3db.msg_twitter

        # Get the latest Twitter message ID to use it as since_id
        query = (table.channel_id == channel_id) & \
                (table.inbound == True)
        latest = db(query).select(table.msg_id,
                                  orderby=~table.date,
                                  limitby=(0, 1)
                                  ).first()

        try:
            if dm:
                if latest:
                    messages = twitter_api.direct_messages(since_id=latest.msg_id)
                else:
                    messages = twitter_api.direct_messages()
            else:
                if latest:
                    messages = twitter_api.user_timeline(screen_name=screen_name,
                                                         since_id=latest.msg_id)
                else:
                    messages = twitter_api.user_timeline(screen_name=screen_name)
        except tweepy.TweepError as e:
            error = e.message
            if isinstance(error, (tuple, list)):
                # Older Tweepy?
                error = e.message[0]["message"]
            current.log.error("Unable to get the Tweets for the user: %s" % error)
            return False

        messages.reverse()

        tinsert = table.insert
        update_super = s3db.update_super
        for message in messages:
            if dm:
                from_address = message.sender_screen_name
                to_address = message.recipient_screen_name
            else:
                from_address = message.author.screen_name
                to_address = message.in_reply_to_screen_name
            _id = tinsert(channel_id = channel_id,
                          body = message.text,
                          from_address = from_address,
                          to_address = to_address,
                          date = message.created_at,
                          inbound = True,
                          msg_id = message.id,
                          )
            update_super(table, dict(id=_id))

        return True

    # -------------------------------------------------------------------------
    @staticmethod
    def update_channel_status(channel_id, status, period=None):
        """
            Update the Status for a Channel
        """

        db = current.db

        # Read current status
        stable = current.s3db.msg_channel_status
        query = (stable.channel_id == channel_id)
        old_status = db(query).select(stable.status,
                                      limitby=(0, 1)
                                      ).first()
        if old_status:
            # Update
            if status and status[0] == "+":
                # Increment status if-numeric
                old_status = old_status.status
                try:
                    old_status = int(old_status)
                except (ValueError, TypeError):
                    new_status = status
                else:
                    new_status = old_status + int(status[1:])
            else:
                new_status = status
            db(query).update(status = new_status)
        else:
            # Initialise
            stable.insert(channel_id = channel_id,
                          status = status)
        if period:
            # Amend the frequency of the scheduled task
            ttable = db.scheduler_task
            args = '["msg_rss_channel", %s]' % channel_id
            query = ((ttable.function_name == "msg_poll") & \
                     (ttable.args == args) & \
                     (ttable.status.belongs(["RUNNING", "QUEUED", "ALLOCATED"])))
            exists = db(query).select(ttable.id,
                                      ttable.period,
                                      limitby=(0, 1)).first()
            if not exists:
                return
            old_period = exists.period
            max_period = period[1]
            if old_period < max_period:
                new_period = old_period + period[0]
                new_period = min(new_period, max_period)
                db(ttable.id == exists.id).update(period=new_period)

    # -------------------------------------------------------------------------
    @staticmethod
    def twitter_search(search_id):
        """
            Fetch Results for a Twitter Search Query
        """

        try:
            import TwitterSearch
        except ImportError:
            error = "Unresolved dependency: TwitterSearch required for fetching results from twitter keyword queries"
            current.log.error("s3msg", error)
            current.session.error = error
            redirect(URL(f="index"))

        db = current.db
        s3db = current.s3db

        # Read Settings
        table = s3db.msg_twitter_channel
        # Doesn't need to be enabled for Polling
        settings = db(table.id > 0).select(table.consumer_key,
                                           table.consumer_secret,
                                           table.access_token,
                                           table.access_token_secret,
                                           limitby=(0, 1)).first()

        if not settings:
            error = "Twitter Search requires an account configuring"
            current.log.error("s3msg", error)
            current.session.error = error
            redirect(URL(f="twitter_channel"))

        qtable = s3db.msg_twitter_search
        rtable = db.msg_twitter_result
        search_query = db(qtable.id == search_id).select(qtable.id,
                                                         qtable.keywords,
                                                         qtable.lang,
                                                         qtable.count,
                                                         qtable.include_entities,
                                                         limitby=(0, 1)).first()

        tso = TwitterSearch.TwitterSearchOrder()
        tso.set_keywords(search_query.keywords.split(" "))
        tso.set_language(search_query.lang)
        # @ToDo Handle more than 100 results per page
        # This may have to be changed upstream
        tso.set_count(int(search_query.count))
        tso.set_include_entities(search_query.include_entities)

        try:
            ts = TwitterSearch.TwitterSearch(
                consumer_key = settings.consumer_key,
                consumer_secret = settings.consumer_secret,
                access_token = settings.access_token,
                access_token_secret = settings.access_token_secret
                )
        except TwitterSearch.TwitterSearchException as e:
            return(str(e))

        from dateutil import parser
        date_parse = parser.parse

        gtable = db.gis_location
        # Disable validation
        rtable.location_id.requires = None
        update_super = s3db.update_super

        for tweet in ts.search_tweets_iterable(tso):
            user = tweet["user"]["screen_name"]
            body = tweet["text"]
            tweet_id = tweet["id_str"]
            lang = tweet["lang"]
            created_at = date_parse(tweet["created_at"])
            lat = None
            lon = None
            if tweet["coordinates"]:
                lat = tweet["coordinates"]["coordinates"][1]
                lon = tweet["coordinates"]["coordinates"][0]
                location_id = gtable.insert(lat=lat, lon=lon)
            else:
                location_id = None
            _id = rtable.insert(from_address = user,
                                search_id = search_id,
                                body = body,
                                tweet_id = tweet_id,
                                lang = lang,
                                date = created_at,
                                #inbound = True,
                                location_id = location_id,
                                )
            update_super(rtable, dict(id=_id))

        # This is simplistic as we may well want to repeat the same search multiple times
        db(qtable.id == search_id).update(is_searched = True)

        return "OK"

    # -------------------------------------------------------------------------
    @staticmethod
    def process_keygraph(search_id):
        """ Process results of twitter search with KeyGraph."""

        import subprocess
        import tempfile

        db = current.db
        s3db = current.s3db
        curpath = os.getcwd()
        preprocess = S3Msg.preprocess_tweet

        def generateFiles():

            dirpath = tempfile.mkdtemp()
            os.chdir(dirpath)

            rtable = s3db.msg_twitter_search_results
            tweets = db(rtable.deleted == False).select(rtable.body)
            tweetno = 1
            for tweet in tweets:
                filename = "%s.txt" % tweetno
                f = open(filename, "w")
                f.write(preprocess(tweet.body))
                tweetno += 1

            return dirpath

        tpath = generateFiles()
        jarpath = os.path.join(curpath, "static", "KeyGraph", "keygraph.jar")
        resultpath = os.path.join(curpath, "static", "KeyGraph", "results", "%s.txt" % search_id)
        return subprocess.call(["java", "-jar", jarpath, tpath, resultpath])

    # -------------------------------------------------------------------------
    @staticmethod
    def preprocess_tweet(tweet):
        """
            Preprocesses tweets to remove  URLs,
            RTs, extra whitespaces and replace hashtags
            with their definitions.
        """

        tagdef = S3Msg.tagdef
        tweet = tweet.lower()
        tweet = re.sub(r"((www\.[\s]+)|(https?://[^\s]+))", "", tweet)
        tweet = re.sub(r"@[^\s]+", "", tweet)
        tweet = re.sub(r"[\s]+", " ", tweet)
        tweet = re.sub(r"#([^\s]+)", lambda m:tagdef(m.group(0)), tweet)
        tweet = tweet.strip('\'"')

        return tweet

    # -------------------------------------------------------------------------
    @staticmethod
    def tagdef(hashtag):
        """
            Returns the definition of a hashtag.
        """

        hashtag = hashtag.split("#")[1]

        turl = "http://api.tagdef.com/one.%s.json" % hashtag
        try:
            hashstr = urlopen(turl).read()
            hashdef = json.loads(hashstr)
        except:
            return hashtag
        else:
            return hashdef["defs"]["def"]["text"]

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
            r.error(405, current.ERROR.BAD_METHOD)
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

        self.url = url = r.url()

        # @ToDo: Use API
        if auth.is_logged_in() or auth.basic():
            pass
        else:
            redirect(URL(c="default", f="user", args="login",
                         vars={"_next": url}))

        if not current.deployment_settings.has_module("msg"):
            current.session.error = T("Cannot send messages if Messaging module disabled")
            redirect(URL(f="index"))

        if not auth.permission.has_permission("update", c="msg"):
            current.session.error = T("You do not have permission to send messages")
            redirect(URL(f="index"))

        #_vars = r.get_vars

        # Set defaults for when not coming via msg.compose()
        self.contact_method = None
        self.recipient = None
        self.recipients = None
        self.recipient_type = None
        self.subject = None
        self.message = None
        #self.formid = None
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
        if self.method == "compose":
            output = dict(form=form)
        else:
            r.error(405, current.ERROR.BAD_METHOD)

        # Complete the page
        if r.representation == "html":
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
            #current.response.view = self._view(r, "list_filter.html")
            current.response.view = self._view(r, "create.html")

        return output

    # -------------------------------------------------------------------------
    def _compose_onvalidation(self, form):
        """
            Set the sender
            Route the message
        """

        post_vars = current.request.post_vars
        settings = current.deployment_settings

        if settings.get_mail_default_subject():
            system_name_short = "%s - " % settings.get_system_name_short()
        else:
            system_name_short = ""

        if settings.get_mail_auth_user_in_subject():
            user = current.auth.user
            if user:
                authenticated_user = "%s %s - " % (user.first_name,
                                                   user.last_name)
        else:
            authenticated_user = ""

        post_vars.subject = authenticated_user + system_name_short + post_vars.subject
        contact_method = post_vars.contact_method

        recipients = self.recipients
        if not recipients:
            if not post_vars.pe_id:
                if contact_method != "TWITTER":
                    current.session.error = current.T("Please enter the recipient(s)")
                    redirect(self.url)
                else:
                    # This must be a Status Update
                    if current.msg.send_tweet(post_vars.body):
                        current.session.confirmation = current.T("Check outbox for the message status")
                    else:
                        current.session.error = current.T("Error sending message!")
                    redirect(self.url)
            else:
                recipients = post_vars.pe_id

        if current.msg.send_by_pe_id(recipients,
                                     post_vars.subject,
                                     post_vars.body,
                                     contact_method):
            current.session.confirmation = current.T("Check outbox for the message status")
            redirect(self.url)
        else:
            if current.mail.error:
                # set by mail.error
                current.session.error = "%s: %s" % (current.T("Error sending message"),
                                                    current.mail.error)
            else:
                current.session.error = current.T("Error sending message!")
            redirect(self.url)

    # -------------------------------------------------------------------------
    def _compose_form(self):
        """ Creates the form for composing the message """

        T = current.T
        db = current.db
        s3db = current.s3db
        request = current.request
        get_vars = request.get_vars

        mtable = s3db.msg_message
        etable = s3db.msg_email
        otable = s3db.msg_outbox

        mtable.body.label = T("Message")
        mtable.body.default = self.message
        etable.subject.default = self.subject
        mtable.inbound.default = False
        mtable.inbound.writable = False

        resource = self.resource

        recipient_type = self.recipient_type # from msg.compose()
        if not recipient_type and resource:
            # See if we have defined a custom recipient type for this table
            # pr_person or pr_group
            recipient_type = self._config("msg_recipient_type", None)

        contact_method = self.contact_method # from msg.compose()
        if not contact_method and resource:
            # See if we have defined a custom default contact method for this table
            contact_method = self._config("msg_contact_method", "EMAIL")

        otable.contact_method.default = contact_method

        recipient = self.recipient # from msg.compose()
        if not recipient:
            if "pe_id" in get_vars:
                recipient = get_vars.pe_id
            elif "person_id" in get_vars:
                # @ToDo
                pass
            elif "group_id" in get_vars:
                # @ToDo
                pass
            elif "human_resource.id" in get_vars:
                # @ToDo
                pass

        if recipient:
            recipients = [recipient]
        else:
            recipients = []

            if resource:
                table = resource.table
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
                    recipients = [list(record.values())[0] for record in records]

        pe_field = otable.pe_id
        pe_field.label = T("Recipient(s)")
        pe_field.writable = True
        if recipients:
            # Don't download a SELECT
            pe_field.requires = None
            # Tell onvalidation about them
            self.recipients = recipients

            pe_field.default = recipients

            if len(recipients) == 1:
                recipient = recipients[0]
                represent = s3db.pr_PersonEntityRepresent(show_label=False)(recipient)
                # Restrict message options to those available for the entity
                petable = s3db.pr_pentity
                entity_type = db(petable.pe_id == recipient).select(petable.instance_type,
                                                                    limitby=(0, 1)
                                                                    ).first().instance_type
                if entity_type == "pr_person":
                    all_contact_opts = current.msg.MSG_CONTACT_OPTS
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
                        if controller == "hrm":
                            url = URL(c="hrm", f="person", args="contacts",
                                      vars={"group": "staff",
                                            "human_resource.id": get_vars.get("human_resource.id")})
                        elif controller == "vol":
                            url = URL(c="vol", f="person", args="contacts",
                                      vars={"group": "volunteer",
                                            "human_resource.id": get_vars.get("human_resource.id")})
                        elif controller == "member":
                            url = URL(c="member", f="person", args="contacts",
                                      vars={"membership.id": get_vars.get("membership.id")})
                        else:
                            # @ToDo: Lookup the type
                            url = URL(f="index")
                        redirect(url)
                    otable.contact_method.requires = IS_IN_SET(contact_method_opts,
                                                               zero=None)
                    if contact_method not in contact_method_opts:
                        otable.contact_method.default = contact_method_opts.popitem()[0]
                #elif entity_type = "pr_group":
                    # @ToDo: Loop through members
            else:
                # @ToDo: This should display all the Recipients (truncated with option to see all)
                # - use pr_PersonEntityRepresent for bulk representation
                represent = T("%(count)s Recipients") % dict(count=len(recipients))
        else:
            if recipient_type:
                # Filter by Recipient Type
                pe_field.requires = IS_ONE_OF(db,
                                              "pr_pentity.pe_id",
                                              # Breaks PG
                                              #orderby="instance_type",
                                              filterby="instance_type",
                                              filter_opts=(recipient_type,),
                                              )
                pe_field.widget = S3PentityAutocompleteWidget(types=(recipient_type,))
            else:
                # @ToDo A new widget (tree?) required to handle multiple persons and groups
                pe_field.widget = S3PentityAutocompleteWidget()

            pe_field.comment = DIV(_class="tooltip",
                                   _title="%s|%s" % \
                (T("Recipients"),
                 T("Please enter the first few letters of the Person/Group for the autocomplete.")))

        sqlform = S3SQLDefaultForm()

        s3resource = s3db.resource
        logform = sqlform(request = request,
                          resource = s3resource("msg_message"),
                          onvalidation = self._compose_onvalidation,
                          message = "Message Sent",
                          format = "html")

        outboxform = sqlform(request = request,
                             resource = s3resource("msg_outbox"),
                             message = "Message Sent",
                             format = "html")

        mailform = sqlform(request = request,
                           resource = s3resource("msg_email"),
                           message = "Message Sent",
                           format = "html")

        # Shortcuts
        lcustom = logform.custom
        ocustom = outboxform.custom
        mcustom = mailform.custom

        pe_row = TR(TD(LABEL(ocustom.label.pe_id)),
                    _id="msg_outbox_pe_id__row")
        if recipients:
            ocustom.widget.pe_id["_class"] = "hide"
            pe_row.append(TD(ocustom.widget.pe_id,
                             represent))
        else:
            pe_row.append(TD(ocustom.widget.pe_id))
            pe_row.append(TD(ocustom.comment.pe_id))

        # Build a custom form from the 3 source forms
        form = DIV(lcustom.begin,
                   TABLE(TBODY(TR(TD(LABEL(ocustom.label.contact_method)),
                                  TD(ocustom.widget.contact_method),
                                  TD(ocustom.comment.contact_method),
                                  _id="msg_outbox_contact_method__row"
                                  ),
                               pe_row,
                               TR(TD(LABEL(mcustom.label.subject)),
                                  TD(mcustom.widget.subject),
                                  TD(mcustom.comment.subject),
                                  _id="msg_log_subject__row"
                                  ),
                               TR(TD(LABEL(lcustom.label.body)),
                                  TD(lcustom.widget.body),
                                  TD(lcustom.comment.body),
                                  _id="msg_log_message__row"
                                  ),
                               #TR(TD(LABEL(lcustom.label.priority)),
                                  #TD(lcustom.widget.priority),
                                  #TD(lcustom.comment.priority),
                                  #_id="msg_log_priority__row"
                                  #),
                               TR(TD(),
                                  TD(INPUT(_type="submit",
                                           _value=T("Send message"),
                                           _id="dummy_submit"),
                                     ),
                                  _id="submit_record__row"
                                  ),
                               ),
                         ),
                   lcustom.end,
                   )

        s3 = current.response.s3
        if s3.debug:
            s3.scripts.append("/%s/static/scripts/S3/s3.msg.js" % request.application)
        else:
            s3.scripts.append("/%s/static/scripts/S3/s3.msg.min.js" % request.application)
        script = '''i18n.none_of_the_above="%s"''' % T("None of the above")
        s3.js_global.append(script)
        # @ToDo: Port SMS maxLength from alert_create_script() in controllers/deploy.py

        return form

# END =========================================================================
