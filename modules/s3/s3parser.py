# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

""" Message Parsing API

    API to parse messages:
        - currently Email only.

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

from gluon import current

from s3utils import soundex

# =============================================================================
class S3Parsing(object):
    """
       Message Parsing Framework.
    """
  
    # -------------------------------------------------------------------------
    @staticmethod
    def parse_person(message=""):
        """
            Search for People
        """

        if not message:
            return None

        T = current.T
        db = current.db
        s3db = current.s3db

        primary_keywords = ["get", "give", "show"] # Equivalent keywords in one list
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

        # ---------------------------------------------------------------------
        # Person Search [get name person phone email]
        if "person" in pquery:

            table = s3db.pr_person
            rows = db(table.deleted ==False).select(table.pe_id,
                                                    table.first_name,
                                                    table.middle_name,
                                                    table.last_name)
            _name = soundex(str(name))
            for row in rows:
                result = []
                if (_name == soundex(row.first_name)) or \
                   (_name == soundex(row.middle_name)) or \
                   (_name == soundex(row.last_name)):
                    presult = dict(name = row.first_name, id = row.pe_id)
                    result.append(presult)
                    break

            if len(result) > 1:
                return T("Multiple Matches")
            if len(result) == 1:
                reply = result[0]["name"]
                table = s3db.pr_contact
                if "email" in pquery:
                    query = (table.pe_id == result[0]["id"]) & \
                        (table.contact_method == "EMAIL")
                    recipient = db(query).select(table.value,
                                                 orderby = table.priority,
                                                 limitby=(0, 1)).first()
                    if recipient:
                        reply = "%s Email->%s" % (reply, recipient.value)
                if "phone" in pquery:
                    query = (table.pe_id == result[0]["id"]) & \
                        (table.contact_method == "SMS")
                    recipient = db(query).select(table.value,
                                                 orderby = table.priority,
                                                 limitby=(0, 1)).first()
                    if recipient:
                        reply = "%s Mobile->%s" % (reply,
                                               recipient.value)

            if len(result) == 0:
                return T("No Match")

            return reply
        return "Please provide one of the keywords - person, hospital, organisation"
    
    # ---------------------------------------------------------------------
    @staticmethod
    def parse_hospital(message=""):
        """
           Search for Hospitals
        """

        if not message:
            return None

        T = current.T
        db = current.db
        s3db = current.s3db

        primary_keywords = ["get", "give", "show"] # Equivalent keywords in one list
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

        # ---------------------------------------------------------------------
        #  Hospital Search [example: get name hospital facility status ]
        if "hospital" in pquery:
            table = s3db.hms_hospital
            rows = db(table.deleted == False).select(table.id,
                                                     table.name,
                                                     table.aka1,
                                                     table.aka2,
                                                     table.phone_emergency,
                                                     table.clinical_status,
                                                     table.facility_status,
                                                     table.security_status,
                                                     )
            _name = soundex(str(name))
            for row in rows:
                result = []
                if (_name == soundex(row.name)) or \
                   (_name == soundex(row.aka1)) or \
                   (_name == soundex(row.aka2)):
                    result.append(row)
                    break

            if len(result) > 1:
                return T("Multiple Matches")

            if len(result) == 1:
                hospital = result[0]
                reply = "%s %s (%s) " % (reply, hospital.name,
                                         T("Hospital"))
                if "phone" in pquery:
                    reply = reply + "Phone->" + str(hospital.phone_emergency)
                if "facility" in pquery:
                    reply = reply + "Facility status " + \
                        str(table.facility_status.represent(hospital.facility_status))
                if "clinical" in pquery:
                    reply = reply + "Clinical status " + \
                        str(table.clinical_status.represent(hospital.clinical_status))
                if "security" in pquery:
                    reply = reply + "Security status " + \
                        str(table.security_status.represent(hospital.security_status))

            if len(result) == 0:
                return T("No Match")

            return reply

        return "Please provide one of the keywords - person, hospital, organisation"
    
    # ---------------------------------------------------------------------
    @staticmethod
    def parse_org(message=""):
        """
           Search for Organisations
        """

        if not message:
            return None

        T = current.T
        db = current.db
        s3db = current.s3db

        primary_keywords = ["get", "give", "show"] # Equivalent keywords in one list
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
                
        # ---------------------------------------------------------------------
        # Organization search [example: get name organisation phone]
        if "organisation" in pquery:
            table = s3db.org_organisation
            rows = db(table.deleted == False).select(table.id,
                                                     table.name,
                                                     table.donation_phone,
                                                     table.acronym)
            _name = soundex(str(name))
            for row in rows:
                result = []
                if (_name == soundex(row.name)) or \
                   (_name == soundex(row.acronym)):
                    result.append(row)
                    break

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
                    office = db(table.organisation_id == org.id).select(otable.address,
                                                                        limitby=(0, 1)).first()
                    reply = reply + "Address->" + office.address
            if len(reply) == 0:
                return T("No Match")

            return reply

        return "Please provide one of the keywords - person, hospital, organisation"
    
# END =========================================================================
