'''
This file contains the parsing workflows that define different parsing rules.
Copy this file to modules/parser.py
To add more workflows, define functions with a name "parse_%s" (%workflow_task_id)
==> workflow_task_id is defined in s3db.msg_workflow
(e.g. For workflow_task_id =1 ; we have parse_1() , for workflow_task_id =2 , we have 
parse_2() and so on.

@author: Ashwyn Sharma
'''
import datetime
import difflib
import string
import urllib
from urllib2 import urlopen
    
from gluon import current
from gluon.html import *
from gluon.http import redirect
    
from s3.s3utils import s3_debug,soundex




class S3Parsing(object):
    """
       Message Parsing Framework.
    """
  
    # -------------------------------------------------------------------------
    @staticmethod
    def parse_1(message=""):
            """
                Parsing Workflow 1.
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
    
            pkeywords = primary_keywords+contact_keywords
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
                rows = db(table.id > 0).select(table.pe_id,
                                               table.first_name,
                                               table.middle_name,
                                               table.last_name)
                for row in rows:
                    result = []
                    if (soundex(str(name)) == soundex(str(row.first_name))) or \
                       (soundex(str(name)) == soundex(str(row.middle_name))) or \
                       (soundex(str(name)) == soundex(str(row.last_name))):
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
                        reply = "%s Email->%s" % (reply, recipient.value)
                    if "phone" in pquery:
                        query = (table.pe_id == result[0]["id"]) & \
                            (table.contact_method == "SMS")
                        recipient = db(query).select(table.value,
                                                     orderby = table.priority,
                                                     limitby=(0, 1)).first()
                        reply = "%s Mobile->%s" % (reply,
                                                   recipient.value)
    
                if len(result) == 0:
                    return T("No Match")
    
                return reply
            return "Please provide one of the keywords - person, hospital, organisation"
    
    # ---------------------------------------------------------------------
    # ---------------------------------------------------------------------
    
    @staticmethod
    def parse_2(message=""):
            """
               Parsing Workflow 2. 
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
    
            pkeywords = primary_keywords+contact_keywords
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
                rows = db(table.id > 0).select(table.id,
                                               table.name,
                                               table.aka1,
                                               table.aka2)
                for row in rows:
                    result = []
                    if (soundex(str(name)) == soundex(str(row.name))) or \
                       (soundex(name) == soundex(str(row.aka1))) or \
                       (soundex(name) == soundex(str(row.aka2))):
                        result.append(row)
                        break
    
    
                if len(result) > 1:
                    return T("Multiple Matches")
    
                if len(result) == 1:
                    hospital = db(table.id == result[0].id).select().first()
                    reply = "%s %s (%s) " % (reply, hospital.name,
                                             T("Hospital"))
                    if "phone" in pquery:
                        reply = reply + "Phone->" + str(hospital.phone_emergency)
                    if "facility" in pquery:
                        reply = reply + "Facility status " + str(table.facility_status.represent(hospital.facility_status))
                    if "clinical" in pquery:
                        reply = reply + "Clinical status " + str(table.clinical_status.represent(hospital.clinical_status))
                    if "security" in pquery:
                        reply = reply + "Security status " + str(table.security_status.represent(hospital.security_status))
    
                if len(result) == 0:
                    return T("No Match")
    
                return reply
            return "Please provide one of the keywords - person, hospital, organisation"
    
    # ---------------------------------------------------------------------
    # ---------------------------------------------------------------------
    @staticmethod
    def parse_3(message=""):
            """
               Parsing Workflow 3.
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
    
            pkeywords = primary_keywords+contact_keywords
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
                rows = db(table.id > 0).select(table.id,
                                               table.name,
                                               table.acronym)
                for row in rows:
                    result = []
                    if (soundex(str(name)) == soundex(str(row.name))) or \
                       (soundex(str(name)) == soundex(str(row.acronym))):
                        result.append(row)
                        break
    
                if len(result) > 1:
                    return T("Multiple Matches")
    
                if len(result) == 1:
                    organisation = db(table.id == result[0].id).select().first()
                    reply = "%s %s (%s) " % (reply, organisation.name,
                                             T("Organization"))
                    if "phone" in pquery:
                        reply = reply + "Phone->" + str(organisation.donation_phone)
                    if "office" in pquery:
                        reply = reply + "Address->" + s3_get_db_field_value(tablename = "org_office",
                                                                            fieldname = "address",
                                                                            look_up_value = organisation.id)
                if len(reply) == 0:
                    return T("No Match")
    
                return reply
            return "Please provide one of the keywords - person, hospital, organisation"
    
    
    # ---------------------------------------------------------------------
    # ---------------------------------------------------------------------
    @staticmethod
    def parser(workflow, message = ""):
        """
           Parsing Workflow Filter.
           Called by parse_import() in s3msg.py.
        """
        
        if workflow == 1:
            return S3Parsing.parse_1(message)
        
        elif workflow == 2:
            return S3Parsing.parse_2(message)

        elif workflow == 3:
            return S3Parsing.parse_3(message)
        else:
            return None
    
# END =========================================================================
    
    
