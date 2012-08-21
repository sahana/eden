# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

""" Message Parsing API

    API to parse Inbound Messages.

    Message Parsing subroutines are defined here.
    These subroutines define different sets of parsing rules.
    Imported by private/templates/<template>
    where <template> is the "default" template by default.

    @author: Ashwyn Sharma <ashwyn1092[at]gmail.com>
    
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

import string
import sys

from gluon import current

from s3.s3utils import soundex
                
# =============================================================================
class S3Parsing(object):
    """
       Message Parsing Framework.
    """
  
    # -------------------------------------------------------------------------
    @staticmethod
    def keyword_search(message="", sender=""):
        """
            1st Pass Parser for searching people, 
            hospitals and organisations.
        """

        if not message:
            return None

        T = current.T
        db = current.db
        s3db = current.s3db
        
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

        if len(result) > 1:
            return T("Multiple Matches")
        if len(result) == 1:
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
                    reply = "%s 's Email Not available!"%reply
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
                    reply = "%s 's Mobile Contact Not available!"%reply

        if len(result) == 0:
            return T("No Match")

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

        if len(result) > 1:
            return T("Multiple Matches")

        if len(result) == 1:
            hospital = result[0]
            status = db(stable.hospital_id == hospital.id).\
                                                select(limitby=(0,1)).first()
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

        if len(result) == 0:
            return T("No Match")

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

        if len(result) > 1:
            return T("Multiple Matches")

        if len(result) == 1:
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
        if len(reply) == 0:
            return T("No Match")

        return reply

    # -------------------------------------------------------------------------
    @staticmethod
    def parse_ireport(message="", sender=""):
        """
            Parse Messages directed to the IRS Module.
        """

        if not message:
            return None

        T = current.T
        db = current.db
        s3db = current.s3db
        msg = current.msg
        parser = S3Parsing()

        (lat, lon, code, text) = msg.parse_opengeosms(message)
        if code == "SI":
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
    def parse_opengeosms(self,lat="", lon="", text="", message="", sender=""):
        """
            Parse OpenGeoSMS formatted messages.
        """

        db = current.db
        s3db = current.s3db
        rtable = s3db.irs_ireport
        gtable = s3db.gis_location
        info = string.split(text)
        name = info[len(info)-1]
        category = ""
        for a in range(0, len(info)-1):
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

        db.commit()
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
