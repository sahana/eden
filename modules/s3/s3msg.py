# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

""" Messaging API

    API to send messages:
        - currently SMS, Email & Twitter

    Messages get sent to the Outbox (& Log)
    From there, Cron tasks collect them & send them

    @author: Praneeth Bodduluri <lifeeth[at]gmail.com>
    @author: Fran Boon <fran[at]aidiq.com>

    @copyright: 2009-2011 (c) Sahana Software Foundation
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

__all__ = ["S3Msg"]

import sys
import datetime
import string
import urllib
from urllib2 import urlopen
from s3utils import s3_debug

from gluon import current

IDENTITYTRANS = ALLCHARS = string.maketrans("", "")
NOTPHONECHARS = ALLCHARS.translate(IDENTITYTRANS, string.digits)
NOTTWITTERCHARS = ALLCHARS.translate(IDENTITYTRANS, string.digits + string.letters + "_")

TWITTER_MAX_CHARS = 140
TWITTER_HAS_NEXT_SUFFIX = u' \u2026'
TWITTER_HAS_PREV_PREFIX = u'\u2026 '

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
        # NB Coded into hrm controller (map_popup) & _compose view
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
    def sanitise_phone(self, phone):
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
                clean = str(default_country_code) + clean
            else:
                clean = str(default_country_code) + string.lstrip(clean, "0")

        return clean

    # =========================================================================
    # Inbound Messages
    # =========================================================================
    def receive_msg(self,
                    subject="",
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

        try:
            message_log_id = db.msg_log.insert(inbound = True,
                                               subject = subject,
                                               message = message,
                                               sender  = sender,
                                               fromaddress = fromaddress,
                                               )
        except:
            return False
            #2) This is not transaction safe - power failure in the middle will cause no message in the outbox
        try:
            db.msg_channel.insert(message_id = message_log_id,
                                  pr_message_method = pr_message_method)
        except:
            return False
        # Explicitly commit DB operations when running from Cron
        db.commit()
        return True

    # -------------------------------------------------------------------------
    def parse_message(self, message=""):
        """
            Parse Incoming Message

            Check for OpenGeoSMS
                route SI to IRS

            @ToDo: Move Parserdooth here from controllers/msg.py?
        """

        if not message:
            return None

        return

    # =========================================================================
    # Outbound Messages
    # =========================================================================
    def send_by_pe_id(self,
                      pe_id,
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
        current.manager.load("msg_log")

        # Put the Message in the Log
        table = db.msg_log
        try:
            message_log_id = table.insert(pe_id = sender_pe_id,
                                          subject = subject,
                                          message = message,
                                          sender  = sender,
                                          fromaddress = fromaddress)
        except:
            return False

        # Place the Message in the OutBox
        table = db.msg_outbox
        if isinstance(pe_id, list):
            listindex = 0
            for prpeid in pe_id:
                try:
                    table.insert(message_id = message_log_id,
                                 pe_id = prpeid,
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
        current.manager.load("msg_outbox")

        if contact_method == "SMS":
            table = db.msg_setting
            settings = db(table.id > 0).select(table.outgoing_sms_handler,
                                               limitby=(0, 1)).first()
            if not settings:
                raise ValueError("No SMS handler defined!")
            outgoing_sms_handler = settings.outgoing_sms_handler

        def dispatch_to_pe_id(pe_id):
            table = db.pr_contact
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

        table = db.msg_outbox
        ltable = db.msg_log
        ptable = db.pr_person
        petable = db.pr_pentity

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
                table3 = db.pr_group
                query = (table3.pe_id == entity)
                group_id = db(query).select(table3.id,
                                            limitby=(0, 1)).first().id
                table4 = db.pr_group_membership
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
                table3 = db.org_organisation
                query = (table3.pe_id == entity)
                org_id = db(query).select(table3.id, limitby=(0, 1)).first().id
                table4 = db.hrm_human_resource
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
            current.manager.load("msg_outbox")
            db = current.db
            table = db.msg_limit
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
    def prepare_opengeosms(self, location_id, code="S", map="google", text=""):
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
        table = db.gis_location
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
        current.manager.load("msg_api_settings")
        table = db.msg_api_settings

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
        current.manager.load("msg_smtp_to_sms_settings")
        table = db.msg_smtp_to_sms_settings

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
        current.manager.load("msg_tropo_settings")
        table = db.msg_tropo_settings

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
            db.msg_tropo_scratch.insert(row_id = row_id,
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
    def sanitise_twitter_account(self, account):
        """
            Only keep characters that are legal for a twitter account:
            letters, digits, and _
        """

        return account.translate(IDENTITYTRANS, NOTTWITTERCHARS)

    # -------------------------------------------------------------------------
    def break_to_chunks(self, text,
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
        manager = current.manager
        settings = current.deployment_settings

        manager.load("msg_twitter_settings")
        query = (db.msg_twitter_settings.id > 0)
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
        current.manager.load("msg_twitter_search")
        table = db.msg_twitter_search
        rows = db().select(table.ALL)

        results_table = db.msg_twitter_search_results

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

# END -------------------------------------------------------------------------

