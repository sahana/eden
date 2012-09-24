# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

""" Message Parsing API

    API to parse Inbound Messages.

    Message Parsing subroutines are defined here.
    These subroutines define different sets of parsing rules.
    Imported by private/templates/<template>
    where <template> is the "default" template by default.

    @copyright: 2012 (c) Sahana Software Foundation
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

__all__ = ["S3Parsing"]

#import re
import string
import sys

#import pyparsing
try:
    import nltk
    from nltk.corpus import wordnet as wn
    NLTK = True
except:
    NLTK = False

from gluon import current
from gluon.tools import fetch

from s3.s3utils import s3_debug, soundex
                
# =============================================================================
class S3Parsing(object):
    """
       Message Parsing Template.
    """
  
    # -------------------------------------------------------------------------
    @staticmethod
    def filter(message="", sender="", service="", coordinates=""):
        """
            Filter unstructured data (e.g. Tweets)
        """

        db = current.db
        s3db = current.s3db
        cache = s3db.cache
        
        # Start with a base priority
        priority = 0

        # Default Category
        category = "Unknown"

        if service == "twitter":
            priority -= 1
        elif service == "sms":
            priority += 1

        # Lookup trusted senders
        # - these could be trained or just trusted
        table = s3db.msg_sender
        ctable = s3db.pr_contact
        query = (table.deleted == False) & \
                (ctable.pe_id == table.pe_id) & \
                (ctable.contact_method == "TWITTER")
        senders = db(query).select(table.priority,
                                   ctable.value,
                                   cache=cache)
        for s in senders:
            if sender == s[ctable].value:
                priority += s[table].priority
                break
        
        # If Anonymous, check their history
        # - within our database
        # if service == "twitter":
        #     # Check Followers
        #     # Check Retweets
        #     # Check when account was created
        # (Note that it is still possible to game this - plausible accounts can be purchased)

        ktable = s3db.msg_keyword
        keywords = db(ktable.deleted == False).select(ktable.id,
                                                      ktable.keyword,
                                                      ktable.incident_type_id,
                                                      cache=cache)
        incident_type_represent = s3db.event_incident_type_represent
        if NLTK:
            # Lookup synonyms
            # @ToDo: Cache
            synonyms = {}
            for kw in keywords:
                syns = []
                try:
                    synsets = wn.synsets(kw.keyword)
                    for synset in synsets:
                        syns += [lemma.name for lemma in synset.lemmas]
                except LookupError:
                    nltk.download("wordnet")
                    synsets = wn.synsets(kw.keyword)
                    for synset in synsets:
                        syns += [lemma.name for lemma in synset.lemmas]
                synonyms[kw.keyword.lower()] = syns

        ltable = s3db.gis_location
        query = (ltable.deleted != True) & \
                (ltable.name != None)
        locs = db(query).select(ltable.id,
                                ltable.name,
                                cache=cache)
        lat = lon = None
        location_id = None
        loc_matches = 0

        # Split message into words
        words = message.split(" ")

        index = 0
        max_index = len(words) - 1
        for word in words:
            word = word.lower()
            if word.endswith(".") or \
               word.endswith(":") or \
               word.endswith(","):
                word = word[:-1]

            skip = False

            if word in ("safe", "ok"):
                priority -= 1
            elif word in ("help"):
                priority += 1
            elif service == "twitter" and \
                 word == "RT":
                # @ToDo: Increase priority of the original message
                priority -= 1
                skip = True

            # Look for URL
            if word.startswith("http://"):
                priority += 1
                skip = True
                # @ToDo: Follow URL to see if we can find an image
                #try:
                #    page = fetch(word)
                #except urllib2.HTTPError:
                #    pass
                # Check returned str for image like IS_IMAGE()

            if (index < max_index):
                if word == "lat":
                    skip = True
                    try:
                        lat = words[index + 1]
                        lat = float(lat)
                    except:
                        pass
                elif word == "lon":
                    skip = True
                    try:
                        lon = words[index + 1]
                        lon = float(lon)
                    except:
                        pass

            if not skip:
                for kw in keywords:
                    _word = kw.keyword.lower()
                    if _word == word:
                        # Check for negation
                        if index and words[index - 1].lower() == "no":
                            pass
                        else:
                            category = incident_type_represent(kw.incident_type_id)
                            break
                    elif NLTK:
                        # Synonyms
                        if word in synonyms[_word]:
                            # Check for negation
                            if index and words[index - 1].lower() == "no":
                                pass
                            else:
                                category = incident_type_represent(kw.incident_type_id)
                                break
                # Check for Location
                for loc in locs:
                    name = loc.name.lower()
                    if word == name:
                        if not loc_matches:
                            location_id = loc.id
                            priority += 1
                        loc_matches += 1
                    elif (index < max_index) and \
                         ("%s %s" % (word, words[index + 1]) == name):
                        # Try names with 2 words
                        if not loc_matches:
                            location_id = loc.id
                            priority += 1
                        loc_matches += 1

            index += 1

        # @ToDo: Prioritise reports from people located where they are reporting from
        # if coordinates:
        
        if not loc_matches or loc_matches > 1:
            if lat and lon:
                location_id = ltable.insert(lat = lat,
                                            lon = lon)
            elif coordinates:
                # Use Geolocation of Tweet
                location_id = ltable.insert(lat = coordinates[0],
                                            lon = coordinates[1])
            
        # @ToDo: Image
        return category, priority, location_id

    # -------------------------------------------------------------------------
    @staticmethod
    def keyword_search(message="", sender=""):
        """
            1st Pass Parser for searching people, 
            hospitals and organisations.
        """

        if not message:
            return None

        # Equivalent keywords in one list
        primary_keywords = ["get", "give", "show"] 
        contact_keywords = ["email", "mobile", "facility", "clinical",
                            "security", "phone", "status", "hospital",
                            "person", "organisation"]

        pkeywords = primary_keywords + contact_keywords
        keywords = string.split(message)
        pquery = []
        name = ""
        reply = ""
        for word in keywords:
            match = None
            for key in pkeywords:
                if soundex(key) == soundex(word):
                    match = key
                    break
            if match:
                pquery.append(match)
            else:
                name = word

        parser = S3Parsing()                
        if "person" in pquery:
            reply = parser.parse_person(pquery, name, sender)
        elif "hospital" in pquery:
            reply = parser.parse_hospital(pquery, name, sender)
        elif "organisation" in pquery:
            reply = parser.parse_org(pquery, name, sender)
        else:
            reply = False
        return reply

    # -------------------------------------------------------------------------
    def parse_person(self, pquery="", name="", sender=""):
        """
            Search for People
        """

        T = current.T
        db = current.db
        s3db = current.s3db

        result = []
        reply = ""

        # Person Search [get name person phone email]
        s3_accessible_query = current.auth.s3_accessible_query
        table = s3db.pr_person
        query = (table.deleted == False) & \
                (s3_accessible_query("read", table))
        rows = db(query).select(table.pe_id,
                                table.first_name,
                                table.middle_name,
                                table.last_name)
        _name = soundex(str(name))
        for row in rows:
            if (_name == soundex(row.first_name)) or \
               (_name == soundex(row.middle_name)) or \
               (_name == soundex(row.last_name)):
                presult = dict(name = row.first_name, id = row.pe_id)
                result.append(presult)

        if len(result) == 0:
            return T("No Match")

        elif len(result) > 1:
            return T("Multiple Matches")
            
        else:
            # Single Match
            reply = result[0]["name"]
            table = s3db.pr_contact
            if "email" in pquery:
                query = (table.pe_id == result[0]["id"]) & \
                        (table.contact_method == "EMAIL") & \
                        (s3_accessible_query("read", table))
                recipient = db(query).select(table.value,
                                             orderby = table.priority,
                                             limitby=(0, 1)).first()
                if recipient:
                    reply = "%s Email->%s" % (reply, recipient.value)
                else:
                    reply = "%s 's Email Not available!" % reply
            if "phone" in pquery:
                query = (table.pe_id == result[0]["id"]) & \
                        (table.contact_method == "SMS") & \
                        (s3_accessible_query("read", table))
                recipient = db(query).select(table.value,
                                             orderby = table.priority,
                                             limitby=(0, 1)).first()
                if recipient:
                    reply = "%s Mobile->%s" % (reply,
                                               recipient.value)
                else:
                    reply = "%s 's Mobile Contact Not available!" % reply

        return reply
    
    # ---------------------------------------------------------------------
    def parse_hospital(self, pquery="", name="", sender=""):
        """
           Search for Hospitals
        """

        T = current.T
        db = current.db
        s3db = current.s3db

        result = []
        reply = ""

        #  Hospital Search [example: get name hospital facility status ]
        table = s3db.hms_hospital
        stable = s3db.hms_status
        query = (table.deleted == False) & \
                (current.auth.s3_accessible_query("read", table))
        rows = db(query).select(table.id,
                                table.name,
                                table.aka1,
                                table.aka2,
                                table.phone_emergency
                                )
        _name = soundex(str(name))
        for row in rows:
            if (_name == soundex(row.name)) or \
               (_name == soundex(row.aka1)) or \
               (_name == soundex(row.aka2)):
                result.append(row)

        if len(result) == 0:
            return T("No Match")

        elif len(result) > 1:
            return T("Multiple Matches")

        else:
            # Single Match
            hospital = result[0]
            status = db(stable.hospital_id == hospital.id).select(stable.facility_status,
                                                                  stable.clinical_status,
                                                                  stable.security_status,
                                                                  limitby=(0, 1)
                                                                  ).first()
            reply = "%s %s (%s) " % (reply, hospital.name,
                                     T("Hospital"))
            if "phone" in pquery:
                reply = reply + "Phone->" + str(hospital.phone_emergency)
            if "facility" in pquery:
                 reply = reply + "Facility status " + \
                    str(stable.facility_status.represent\
                                            (status.facility_status))
            if "clinical" in pquery:
                reply = reply + "Clinical status " + \
                    str(stable.clinical_status.represent\
                                            (status.clinical_status))
            if "security" in pquery:
                reply = reply + "Security status " + \
                    str(stable.security_status.represent\
                                            (status.security_status))

        return reply

    # ---------------------------------------------------------------------
    def parse_org(self, pquery="", name="", sender=""):
        """
           Search for Organisations
        """

        T = current.T
        db = current.db
        s3db = current.s3db

        result = []
        reply = ""

        # Organization search [example: get name organisation phone]
        s3_accessible_query = current.auth.s3_accessible_query
        table = s3db.org_organisation
        query = (table.deleted == False) & \
                (s3_accessible_query("read", table))
        rows = db(query).select(table.id,
                                table.name,
                                table.donation_phone,
                                table.acronym)
        _name = soundex(str(name))
        for row in rows:
            if (_name == soundex(row.name)) or \
               (_name == soundex(row.acronym)):
                result.append(row)

        if len(reply) == 0:
            return T("No Match")

        elif len(result) > 1:
            return T("Multiple Matches")

        else:
            # Single Match
            org = result[0]
            reply = "%s %s (%s) " % (reply, org.name,
                                     T("Organization"))
            if "phone" in pquery:
                reply = reply + "Phone->" + str(org.donation_phone)
            if "office" in pquery:
                otable = s3db.org_office
                query = (otable.organisation_id == org.id) & \
                        (s3_accessible_query("read", otable))
                office = db(query).select(otable.address,
                                          limitby=(0, 1)).first()
                reply = reply + "Address->" + office.address

        return reply

    # -------------------------------------------------------------------------
    @staticmethod
    def parse_ireport(message="", sender=""):
        """
            Parse Messages directed to the IRS Module.
        """

        if not message:
            return None

        parser = S3Parsing()

        (lat, lon, code, text) = current.msg.parse_opengeosms(message)

        if code == "SI":
            # OpenGeoSMS
            reply = parser.parse_opengeosms(lat, lon, text, message, sender)
        else:
            words = string.split(message)
            message = ""
            reponse = ""
            ireport = False
            comments = False
            for word in words:
                if "SI#" in word and not ireport:
                    report = word.split("#")[1]
                    report = int(report)
                    ireport = True
                elif (soundex(word) == soundex("Yes")) and ireport \
                                                        and not comments:
                    response = True
                    comments = True
                elif soundex(word) == soundex("No") and ireport \
                                                    and not comments:
                    response = False
                    comments = True
                elif comments:
                    message += word + " "

            if ireport:
                reply = parser.parse_drequest(report, response, message, sender)
            else:
                reply = False
                       
        return reply				    

    # -------------------------------------------------------------------------
    def parse_opengeosms(self, lat="", lon="", text="", message="", sender=""):
        """
            Parse OpenGeoSMS formatted messages.
        """

        s3db = current.s3db
        rtable = s3db.irs_ireport
        gtable = s3db.gis_location
        info = string.split(text)
        name = info[len(info) - 1]
        category = ""
        for a in range(0, len(info) - 1):
            category = category + info[a] + " "
            
        #@ToDo: Check for an existing location in DB
        #records = db(gtable.id>0).select(gtable.id, \
        #                                 gtable.lat,
        #                                 gtable.lon)
        #for record in records:
        #   try:
        #	    if "%.6f"%record.lat == str(lat) and \
        #	        "%.6f"%record.lon == str(lon):
        #	        location_id = record.id
        #	        break
        #   except:
        #	    pass

        location_id = gtable.insert(name="Incident:%s" % name,
                                    lat=lat,
                                    lon=lon)
        rtable.insert(name=name,
                      message="",
                      category=category,
                      location_id=location_id)			

        current.db.commit()
        return "Incident Report Logged!"
	                    
    # -------------------------------------------------------------------------
    def parse_drequest(self, report, response, message="", sender=""):
        """
            Parse Replies To Deployment Request.
        """
        
        db = current.db
        s3db = current.s3db
        rtable = s3db.irs_ireport_human_resource
        ctable = s3db.pr_contact
        htable = s3db.hrm_human_resource
        ptable = s3db.pr_person_user
        reply = ""        
        
        query = (ctable.contact_method == "EMAIL") & \
                (ctable.value == sender)
        responder = db(query).select(ctable.pe_id, limitby=(0, 1)).first()
        if responder:
            query = (ptable.pe_id == responder.pe_id)
            human_resource = db(query).select(ptable.id,
                                              limitby=(0, 1)).first()
            
            if human_resource:
                query = (htable.person_id == human_resource.id)
                person = db(query).select(htable.id, limitby=(0, 1)).first()
                if person:
                    query = (rtable.ireport_id == report) & \
                            (rtable.human_resource_id == person.id)
                    db(query).update(reply=message,
                                     response=response)
                    reply = "Response Logged in the Report (Id: %d )" % report

        db.commit()
        return reply

# END =========================================================================
