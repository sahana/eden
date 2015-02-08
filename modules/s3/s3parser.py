# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

"""
   This file imports the Message parsers from the core code
   and links them with the respective parsing tasks defined in msg_parser

   @copyright: 2012-13 (c) Sahana Software Foundation
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

#import inspect
import string
import sys

from gluon import current

# =============================================================================
class S3Parsing(object):
    """
       Core Message Parsing Framework
       - reusable functions
    """

    # -------------------------------------------------------------------------
    @static_method
    def parser(function_name, message_id, **kwargs):
        """
           1st Stage Parser
           - called by msg.parse()

           Sets the appropriate Authorisation level and then calls the
           parser function from the template
        """

        reply = None
        s3db = current.s3db

        # Retrieve Message
        table = s3db.msg_message
        message = current.db(table.message_id == message_id).select(limitby=(0, 1)
                                                                    ).first()

        from_address = message.from_address
        if "<" in from_address:
            from_address = from_address.split("<")[1].split(">")[0]
        email = S3Parsing.is_session_alive(from_address)
        if email:
            current.auth.s3_impersonate(email)
        else:
            (email, password) = S3Parsing.parse_login(message)
            if email and password:
                current.auth.login_bare(email, password)
                expiration = current.session.auth["expiration"]
                table = s3db.msg_session
                table.insert(email = email,
                             expiration_time = expiration,
                             from_address = from_address)
                reply = "Login succesful"
                # The message may have multiple purposes
                #return reply

        # Load the Parser template for this deployment
        template = current.deployment_settings.get_msg_parser()
        module_name = "applications.%s.private.templates.%s.parser" \
            % (current.request.application, template)
        __import__(module_name)
        mymodule = sys.modules[module_name]
        S3Parsing = mymodule.S3Parsing()

        # Pass the message to the parser
        try:
            fn = getattr(S3Parsing, function_name)
        except:
            s3_debug("Parser not found: %s" % function_name)
            return None

        reply = fn(message, **kwargs) or reply
        if not reply:
            return None

        # Send Reply
        current.msg.send(from_address, reply)

    # -------------------------------------------------------------------------
    @staticmethod
    def parse_login(message):
        """
            Authenticate a login request
        """

        if not message:
            return None, None

        words = string.split(message.body)
        login = False
        email = None
        password = None
        
        if "LOGIN" in [word.upper() for word in words]:
            login = True 
        if len(words) == 2 and login:
            password = words[1]
        elif len(words) == 3 and login:
            email = words[1]
            password = words[2]
        if login:    
            if password and not email:
                email = message.from_address
            return email, password
        else:
            return None, None

    # ---------------------------------------------------------------------
    @staticmethod
    def is_session_alive(from_address):
        """
            Check whether there is an alive sessions from the same sender
        """

        email = None
        now = current.request.utcnow
        stable = current.s3db.msg_session
        query = (stable.is_expired == False) & \
                (stable.from_address == from_address)
        records = current.db(query).select(stable.id,
                                           stable.created_datetime,
                                           stable.expiration_time,
                                           stable.email,
                                           )
        for record in records:
            time = record.created_datetime
            time = time - now
            time = time.total_seconds()
            if time < record.expiration_time:
                email = record.email
                break
            else:
                record.update_record(is_expired = True) 

        return email

# END =========================================================================
