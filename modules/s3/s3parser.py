# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

"""
   This file imports the Message parsers from the core code
   and links them with the respective parsing tasks defined in msg_workflow.

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

from gluon import current
from s3utils import soundex
import string

class S3Parsing(object):
    """
       Message Parsing Framework.
    """

    # ---------------------------------------------------------------------
    @staticmethod
    def parser(workflow, message = "", sender=""):
        """
           Parsing Workflow Filter.
           Called by parse_import() in s3msg.py.
        """
        settings = current.deployment_settings
	auth = current.auth
	session = current.session
	s3db = current.s3db
        T = current.T
	db = current.db
        msg = current.msg
        rtable = s3db.irs_ireport_human_resource
        ctable = s3db.pr_contact
        htable = s3db.hrm_human_resource
        ptable = s3db.pr_person_user
	stable = s3db.msg_session
	
	Parse = AuthParse()
	check_login = Parse.parse_login
	check_session = Parse.is_session_alive
	
	is_session_alive = check_session(sender)
	if is_session_alive:
	    email = is_session_alive
	    auth.s3_impersonate(email)
	else:
	    if check_login(message, sender):
		(email,password) = check_login(message, sender)
		auth.login_bare(email,password)
		expiration = session.auth["expiration"]
		stable.insert(email = email, expiration_time = expiration, \
		              sender = sender)
		return "Authenticated!"
	
        import sys
        parser = settings.get_msg_parser()
        application = current.request.application
        module_name = 'applications.%s.private.templates.%s.parser' \
            %(application, parser)
        __import__(module_name)
        mymodule = sys.modules[module_name]
        S3Parsing = mymodule.S3Parsing()
        
        import inspect
        parsers = inspect.getmembers(S3Parsing, predicate=inspect.isfunction)
        parse_opts = []
        for parser in parsers:
            parse_opts += [parser[0]]

        for parser in parse_opts:
            if parser == workflow :
                parse = False
		    
                # Equivalent keywords in one list
                primary_keywords = ["get", "give", "show"] 
                contact_keywords = ["email", "mobile", "facility", "clinical",
		                    "security", "phone", "status", "hospital",
		                    "person", "organisation"]
		
                pkeywords = primary_keywords + contact_keywords
                keywords = string.split(message)
                pquery = []
                name = ""
		
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
		
                if workflow == "parse_ireport":
                    (lat, lon, code, text) = msg.parse_opengeosms(message)
                    if code == "SI":
                        result = getattr(S3Parsing, parser)
                        return result(lat, lon, text, message, sender)
                    else:
                        result = getattr(S3Parsing, parser)
                        return result(message=message, sender=sender)
				    
                # --------------------------------------------------------------
                # Person Search [get name person phone email]
                elif "person" in pquery and workflow == "parse_person":
                    parse = True
    
                # --------------------------------------------------------------
                #  Hospital Search [example: get name hospital facility status ]
                elif "hospital" in pquery and workflow == "parse_hospital":
                    parse = True
                # --------------------------------------------------------------
                # Organization search [example: get name organisation phone]
                elif "organisation" in pquery and workflow == "parse_org":
                    parse = True
		
		
		    
                if parse:
                    result = getattr(S3Parsing, parser)
                    return result(pquery, name, sender)
                else:
                    return "Please provide one of the keywords \
		    - person, hospital, organisation"
			    
# =============================================================================
class AuthParse(object): 
    """
       Parser Authorising Framework.
    """

    # ---------------------------------------------------------------------
    
    @staticmethod
    def parse_login(message="", sender=""):
	"""
	    Function to call to authenticate a login request
	"""
    
	if not message:
	    return None
	
	T = current.T
	db = current.db
	s3db = current.s3db
	session = current.session
	request = current.request
	import string
	
	words = string.split(message)
	login = False
	email = ""
	password = ""
	reply = ""
	
	if "LOGIN" in [word.upper() for word in words]:
	    login = True 
	if len(words) == 2 and login:
	    password = words[1]
	elif len(words) == 3 and login:
	    email = words[1]
	    password = words[2]
	if login:    
	    if password and not email:
		email = sender
	    return email, password
	else:
	    return False
	
    # ---------------------------------------------------------------------
    
    @staticmethod
    def is_session_alive(sender=""):
	"""
	    Function to check alive sessions from the same sender (if any)
	"""
	
	db = current.db
	s3db = current.s3db
	stable = s3db.msg_session
	request = current.request
	now = request.utcnow
	email = ""
	
	query = (stable.is_expired == False) & (stable.sender == sender)
	records = db(query).select()
	for record in records:
	    time = record.created_datetime
	    time = time - now
	    time = time.total_seconds()
	    if time < record.expiration_time:
		email = record.email
		break
	    else:
		record.update(is_expired = True) 
	
	
	return email

# END =========================================================================
