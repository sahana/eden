# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

""" Messaging API

    API to send messages:
        - currently SMS, Email & Twitter

    Messages get sent to the Outbox (& Log)
    From there, Cron tasks collect them & send them

    @author: Praneeth Bodduluri <lifeeth[at]gmail.com>
    @author: Fran Boon <fran[at]aidiq.com>

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

__all__ = ["S3Msg",
           "S3Compose"]

import datetime
import difflib
import string
import urllib
from urllib2 import urlopen

from gluon import current
from gluon.html import *
from gluon.http import redirect

from s3crud import S3CRUD
from s3utils import s3_debug
from s3validators import IS_ONE_OF, IS_ONE_OF_EMPTY

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
        self.mail = current.mail
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

        # Full range of contact options
        self.CONTACT_OPTS = {
                "EMAIL":        T("Email"),
                "SMS": current.deployment_settings.get_ui_label_mobile_phone(),
                "HOME_PHONE":   T("Home phone"),
                "WORK_PHONE":   T("Work phone"),
                "FAX":          T("Fax"),
                "SKYPE":        T("Skype"),
                "TWITTER":      T("Twitter"),
                "FACEBOOK":     T("Facebook"),
                "RADIO":        T("Radio Callsign"),
                #"XMPP":        "XMPP",
                "OTHER":        T("other")
            }

        # Those contact options to which we can send notifications
        # NB Coded into hrm controller (map_popup) & s3.msg.js
        self.MSG_CONTACT_OPTS = {
                "EMAIL":    T("Email"),
                "SMS":      current.deployment_settings.get_ui_label_mobile_phone(),
                "TWITTER":  T("Twitter"),
                #"XMPP":    "XMPP",
            }

        self.GATEWAY_OPTS = {
                "MODEM":   T("Modem"),
                "SMTP":    T("SMTP"),
                "TROPO":   T("Tropo"),
                "WEB_API": T("Web API")
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
    # Parser for inbound messages
    # -----------------------------------------------------------------------------
    @staticmethod
    def parse_message(message=""):
        """
            Parse Incoming Message according to keyword

            @ToDo: Check for OpenGeoSMS
                    - route SI to IRS

            @ToDo: Allow this to be more easily customised by moving the
                   routing logic to a separate file (ideally web configurable)
        """

        if not message:
            return None

        T = current.T
        db = current.db
        s3db = current.s3db
        s3mgr = current.manager

        primary_keywords = ["get", "give", "show"] # Equivalent keywords in one list
        contact_keywords = ["email", "mobile", "facility", "clinical",
                            "security", "phone", "status", "hospital",
                            "person", "organisation"]

        keywords = string.split(message)
        query = []
        name = ""
        reply = ""
        for word in keywords:
            match = difflib.get_close_matches(word, primary_keywords + contact_keywords)
            if match:
                query.append(match[0])
            else:
                name = word

        # ---------------------------------------------------------------------
        # Person Search [get name person phone email]
        if "person" in query:
            result = person_search(name)

            if len(result) > 1:
                return T("Multiple Matches")
            if len(result) == 1:
                if "Person" in result[0]["name"]:
                    reply = result[0]["name"]
                    table = s3db.pr_contact
                    if "email" in query:
                        query = (table.pe_id == result[0]["id"]) & \
                                (table.contact_method == "EMAIL")
                        recipient = db(query).select(table.value,
                                                     orderby = table.priority,
                                                     limitby=(0, 1)).first()
                        reply = "%s Email->%s" % (reply, recipient.value)
                    if "mobile" in query:
                        query = (table.pe_id == result[0]["id"]) & \
                                (table.contact_method == "SMS")
                        recipient = db(query).select(table.value,
                                                     orderby = table.priority,
                                                     limitby=(0, 1)).first()
                        reply = "%s Mobile->%s" % (reply,
                                                   recipient.value)

            if len(reply) == 0:
                return T("No Match")

            return reply

        # ---------------------------------------------------------------------
        #  Hospital Search [example: get name hospital facility status ]
        if "hospital" in query:
            table = s3db.hms_hospital
            resource = s3mgr.define_resource("hms", "hospital")
            result = resource.search_simple(fields=["name"], label = str(name))
            if len(result) > 1:
                return T("Multiple Matches")

            if len(result) == 1:
                hospital = db(table.id == result[0]).select().first()
                reply = "%s %s (%s) " % (reply, hospital.name,
                                         T("Hospital"))
                if "phone" in query:
                    reply = reply + "Phone->" + str(hospital.phone_emergency)
                if "facility" in query:
                    reply = reply + "Facility status " + str(table.facility_status.represent(hospital.facility_status))
                if "clinical" in query:
                    reply = reply + "Clinical status " + str(table.clinical_status.represent(hospital.clinical_status))
                if "security" in query:
                    reply = reply + "Security status " + str(table.security_status.represent(hospital.security_status))

            if len(reply) == 0:
                return T("No Match")

            return reply

        # ---------------------------------------------------------------------
        # Organization search [example: get name organisation phone]
        if "organisation" in query:
            table = s3db.org_organisation
            resource = s3mgr.define_resource("org", "organisation")
            result = resource.search_simple(fields=["name"], label = str(name))
            if len(result) > 1:
                return T("Multiple Matches")

            if len(result) == 1:
                organisation = db(table.id == result[0]).select().first()
                reply = "%s %s (%s) " % (reply, organisation.name,
                                         T("Organization"))
                if "phone" in query:
                    reply = reply + "Phone->" + str(organisation.donation_phone)
                if "office" in query:
                    reply = reply + "Address->" + s3_get_db_field_value(tablename = "org_office",
                                                                        fieldname = "address",
                                                                        look_up_value = organisation.id)
            if len(reply) == 0:
                return T("No Match")

            return reply

        return "Please provide one of the keywords - person, hospital, organisation"

    # =========================================================================
    # Outbound Messages
    # =========================================================================
    def compose(self,
                type = "SMS",
                recipient_type = None,
                recipient = None,
                message = "",
                url = None,
               ):
        """
            Form to Compose a Message

            @param type: The default message type: None, EMAIL, SMS or TWITTER
            @param recipient_type: Send to Persons or Groups? (pr_person or pr_group)
            @param recipient: The pe_id of the person/group to send the message to
                              - this can also be set by setting one of
                                (in priority order, if multiple found):
                                request.vars.pe_id
                                request.vars.person_id
                                request.vars.group_id
                                request.vars.hrm_id
            @param message: The default message text
            @param url: Redirect to the specified URL() after message sent
        """

        T = current.T
        db = current.db
        s3db = current.s3db
        auth = current.auth
        crud = current.crud
        request = current.request
        session = current.session
        response = current.response
        s3 = response.s3
        vars = request.vars

        ltable = s3db.msg_log
        otable = s3db.msg_outbox

        if not url:
            url = URL(c="msg",
                      f="compose")

        if auth.is_logged_in() or auth.basic():
            pass
        else:
            redirect(URL(c="default", f="user", args="login",
                         vars={"_next" : url}))

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
            elif "hrm_id" in vars:
                # @ToDo
                pass

        if recipient:
            ltable.pe_id.default = recipient
            otable.pe_id.default = recipient
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

        def compose_onvalidation(form):
            """
                Set the sender
                Route the message
            """

            if not vars.pe_id:
                session.error = T("Please enter the recipient(s)")
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
                # Trigger a Process Outbox
                self.process_outbox(contact_method = vars.pr_message_method)
                session.confirmation = T("Check outbox for the message status")
                redirect(url)
            else:
                session.error = T("Error in message")
                redirect(url)

        # Source forms
        logform = crud.create(ltable,
                              onvalidation = compose_onvalidation)
        outboxform = crud.create(otable)

        # Shortcuts
        lcustom = logform.custom
        ocustom = outboxform.custom

        pe_row = TR(TD(LABEL("%s:" % ocustom.label.pe_id)),
                    _id="msg_outbox_pe_id__row")
        if recipient:
            ocustom.widget.pe_id["_class"] = "hidden"
            pe_row.append(TD(ocustom.widget.pe_id,
                             s3.pr_pentity_represent(recipient,
                                                     show_label=False)))
        else:
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
        if not recipient:
            if recipient_type:
                s3.js_global.append("S3.msg_search_url = '%s';" % \
                                    URL(c="msg", f="search",
                                        vars={"type":recipient_type}))
            else:
                s3.js_global.append("S3.msg_search_url = '%s';" % \
                                    URL(c="msg", f="search"))

            s3.jquery_ready.append("s3_msg_ac_pe_input();")

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
        # Explicitly commit DB operations when running from Cron
        db.commit()

        # @ToDo: Process Outbox (once this can be done async)
        # - or is this better to do in the wrapper script?

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
            table = s3db.msg_setting
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
                    return self.send_text_via_twitter(recipient.value,
                                                      message)
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
                   encoding="utf-8"):
        """
            Function to send Email
            - simple Wrapper over Web2Py's Email API

            @ToDo: Better Error checking:
                   http://eden.sahanafoundation.org/ticket/439
        """

        limit = current.deployment_settings.get_mail_limit()

        if limit:
            db = current.db
            s3db = current.db
            table = s3db.msg_limit
            # Check whether we've reached our daily limit
            day = datetime.timedelta(hours=24)
            cutoff = current.request.utcnow - day
            query = (table.created_on > cutoff)
            check = db(query).count()
            if check >= limit:
                return False
            # Log the sending
            table.insert()

        result = self.mail.send(to,
                                subject,
                                message,
                                attachments,
                                cc,
                                bcc,
                                reply_to,
                                encoding
                                )

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
            url = "http://maps.google.com/maps?q=%f,%f" % (lat, lon)
        elif map == "osm":
            # NB Not sure how this will work in OpenGeoSMS client
            url = "http://openstreetmap.org?mlat=%f&mlon=%f&zoom=14" % (lat, lon)

        opengeosms = "%s&%s\n%s" % (url, code, text)

        return opengeosms

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
        table = s3db.msg_api_settings

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

        try:
            sms_api_post_config[sms_api.message_variable] = text
            sms_api_post_config[sms_api.to_variable] = str(mobile)
            query = urllib.urlencode(sms_api_post_config)
            request = urllib.urlopen(sms_api.url, query)
            output = request.read()
            return True
        except:
            return False

    # -------------------------------------------------------------------------
    def send_sms_via_smtp(self, mobile, text=""):
        """
            Function to send SMS via SMTP

            NB Different Gateways have different requirements for presence/absence of International code

            http://en.wikipedia.org/wiki/List_of_SMS_gateways
            http://www.obviously.com/tech_tips/SMS_Text_Email_Gateway.html
        """

        db = current.db
        s3db = current.s3db
        table = s3db.msg_smtp_to_sms_settings

        query = (table.enabled == True)
        settings = db(query).select(limitby=(0, 1)).first()
        if not settings:
            return False

        mobile = self.sanitise_phone(mobile)

        to = "%s@%s" % (mobile,
                        settings.address)

        try:
            self.send_email(to=to,
                            subject="",
                            message= text)
            return True
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
        table = s3db.msg_tropo_settings

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
    @staticmethod
    def get_twitter_api():
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

        db = current.db
        s3db = current.db
        settings = current.deployment_settings

        table = s3db.msg_twitter_settings
        query = (table.id > 0)
        twitter_settings = db(query).select(limitby=(0, 1)).first()
        if twitter_settings and twitter_settings.twitter_account:
            try:
                oauth = tweepy.OAuthHandler(settings.twitter.oauth_consumer_key,
                                            settings.twitter.oauth_consumer_secret)
                oauth.set_access_token(twitter_settings.oauth_key,
                                       twitter_settings.oauth_secret)
                twitter_api = tweepy.API(oauth)
                twitter_account = tmp_twitter_settings.twitter_account
                return dict(twitter_api=twitter_api, twitter_account=twitter_account)
            except:
                pass

        return None

    # -------------------------------------------------------------------------
    def send_text_via_twitter(self, recipient, text=""):
        """
            Function to send text to recipient via direct message (if recipient follows us).
            Falls back to @mention (leaves less characters for the message).
            Breaks long text to chunks if needed.

            @ToDo: Option to Send via Tropo
        """

        # Initialize Twitter API
        twitter_settings = self.get_twitter_api()
        tweepy = self.tweepy

        twitter_api = None
        if twitter_settings:
            twitter_api = twitter_settings["twitter_api"]
            twitter_account = twitter_settings["twitter_account"]

        if not twitter_api and text:
            # Abort
            return False

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
        return True

    #-------------------------------------------------------------------------
    def receive_subscribed_tweets(self):
        """
            Function  to call to drop the tweets into search_results table - called via cron
        """

        # Initialize Twitter API
        twitter_settings = self.get_twitter_api()
        tweepy = self.tweepy

        twitter_api = None
        if twitter_settings:
            twitter_api = twitter_settings["twitter_api"]

        if not twitter_api:
            # Abort
            return False

        db = current.db
        s3db = current.s3db
        table = s3db.msg_twitter_search
        rows = db().select(table.ALL)

        results_table = s3db.msg_twitter_search_results

        # Get the latest updated post time to use it as since_id in twitter search
        recent_time = results_table.posted_by.max()

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

                for result in search_results:
                    # Check if the tweet already exists in the table
                    query = (results_table.posted_by == result.from_user) & \
                            (results_table.posted_at == result.created_at )
                    tweet_exists = db(query).select().first()

                    if tweet_exists:
                        continue
                    else:
                        results_table.insert(tweet = result.text,
                                             posted_by = result.from_user,
                                             posted_at = result.created_at,
                                             twitter_search = row.id
                                            )
            except tweepy.TweepError:
                s3_debug("Unable to get the Tweets for the user search query.")
                return False

            # Explicitly commit DB operations when running from Cron
            db.commit()

        return True

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

        manager = current.manager
        if r.http in ("GET", "POST"):
            output = self.compose(r, **attr)
        else:
            r.error(405, manager.ERROR.BAD_METHOD)
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
        manager = current.manager
        response = current.response
        session = current.session
        settings = current.deployment_settings

        url = r.url()
        self.url = url

        # @ToDo: Use API
        if auth.is_logged_in() or auth.basic():
            pass
        else:
            redirect(URL(c="default", f="user", args="login",
                         vars={"_next" : url}))

        if not settings.has_module("msg"):
            session.error = T("Cannot send messages if Messaging module disabled")
            redirect(URL(f="index"))

        #_vars = r.get_vars

        self.recipients = None
        form = self._compose_form()
        # @ToDo: A 2nd Filter form
        # if form.accepts(r.post_vars, session,
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
            r.error(501, manager.ERROR.BAD_METHOD)

        # Complete the page
        if representation == "html":
            title = self.crud_string(self.tablename, "title_compose")
            if not title:
                title = T("Send Message")

            # subtitle = self.crud_string(self.tablename, "subtitle_compose")
            # if not subtitle:
                # subtitle = ""

            # Maintain RHeader for consistency
            if "rheader" in attr:
                rheader = attr["rheader"](r)
                if rheader:
                    output["rheader"] = rheader

            output["title"] = title
            #output["subtitle"] = subtitle
            #output["form"] = form
            #response.view = self._view(r, "list_create.html")
            response.view = self._view(r, "create.html")

        return output

    # -------------------------------------------------------------------------
    def _compose_onvalidation(self, form):
        """
            Set the sender
            Route the message
        """

        T = current.T
        db = current.db
        s3db = current.s3db
        auth = current.auth
        msg = current.msg
        session = current.session

        vars = current.request.post_vars

        url = self.url

        recipients = self.recipients
        if not recipients:
            if not vars.pe_id:
                session.error = T("Please enter the recipient(s)")
                redirect(url)
            else:
                recipients = vars.pe_id

        table = s3db.pr_person
        if auth.user:
            sender_pe_id = auth.user.pe_id
        else:
            return
        if msg.send_by_pe_id(recipients,
                             vars.subject,
                             vars.message,
                             sender_pe_id,
                             vars.pr_message_method):
            # Trigger a Process Outbox
            msg.process_outbox(contact_method = vars.pr_message_method)
            session.confirmation = T("Check outbox for the message status")
            redirect(url)
        else:
            session.error = T("Error in message")
            redirect(url)

    # -------------------------------------------------------------------------
    def _compose_form(self):
        """ Creates the form for composing the message """

        resource = self.resource
        table = resource.table

        T = current.T
        db = current.db
        s3db = current.s3db
        crud = current.crud
        session = current.session
        response = current.response
        s3 = response.s3

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

        if "pe_id" in table:
            records = resource.sqltable(as_list=True, start=None, limit=None)
            if records and table.virtualfields:
                # Check for join
                tablename = table._tablename
                if tablename in records[0]:
                    recipients = []
                    for record in records:
                        pe_id = record[tablename]["pe_id"]
                        if pe_id:
                            recipients.append(pe_id)
                else:
                    # No join
                    recipients = [record["pe_id"] for record in records if record["pe_id"]]
            else:
                recipients = [record["pe_id"] for record in records if record["pe_id"]]
        elif "person_id" in table:
            # @ToDo: Optimise through a Join
            records = resource.sqltable(as_list=True, start=None, limit=None)
            if records and table.virtualfields:
                # Check for join
                tablename = table._tablename
                if tablename in records[0]:
                    persons = []
                    for record in records:
                        person_id = record[tablename]["person_id"]
                        if person_id:
                            persons.append(person_id)
                else:
                    # No join
                    persons = [record["person_id"] for record in records if record["person_id"]]
            else:
                persons = [record["person_id"] for record in records]
            table = s3db.pr_person
            records = db(table.id.belongs(persons)).select(table.pe_id)
            recipients = [record.pe_id for record in records]
        elif "group_id" in table:
            # @ToDo
            recipients = None
        else:
            recipients = None

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
                represent = s3.pr_pentity_represent(recipients[0],
                                                    show_label=False)
            else:
                # @ToDo: This should be the filter results
                represent = T("Multiple")
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
                s3.js_global.append("S3.msg_search_url = '%s';" % \
                                    URL(c="msg", f="search",
                                        vars={"type":recipient_type}))
            else:
                s3.js_global.append("S3.msg_search_url = '%s';" % \
                                    URL(c="msg", f="search"))

            s3.jquery_ready.append("s3_msg_ac_pe_input();")

        return form

# END =========================================================================
