# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

"""
   This file parses messages using functions defined in in the template's
   parser.py

   @copyright: 2012-2018 (c) Sahana Software Foundation
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

__all__ = ("S3Parsing",)

import sys

from gluon import current

# =============================================================================
class S3Parsing(object):
    """
       Core Message Parsing Framework
       - reusable functions
    """

    # -------------------------------------------------------------------------
    @staticmethod
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
        module_name = "applications.%s.modules.templates.%s.parser" \
            % (current.request.application, template)
        __import__(module_name)
        mymodule = sys.modules[module_name]
        S3Parser = mymodule.S3Parser()

        # Pass the message to the parser
        try:
            fn = getattr(S3Parser, function_name)
        except:
            current.log.error("Parser not found: %s" % function_name)
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

        if not message or not message.body:
            return None, None

        words = message.body.split(" ")
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
            Check whether there is an alive session from the same sender
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

    # ---------------------------------------------------------------------
    @staticmethod
    def lookup_person(address):
        """
            Lookup a Person from an Email Address
        """

        s3db = current.s3db

        if "<" in address:
            address = address.split("<")[1].split(">")[0]
        ptable = s3db.pr_person
        ctable = s3db.pr_contact
        query = (ctable.value == address) & \
                (ctable.contact_method == "EMAIL") & \
                (ctable.pe_id == ptable.pe_id) & \
                (ptable.deleted == False) & \
                (ctable.deleted == False)
        possibles = current.db(query).select(ptable.id,
                                             limitby=(0, 2))
        if len(possibles) == 1:
            return possibles.first().id

        return None

    # ---------------------------------------------------------------------
    @staticmethod
    def lookup_human_resource(address):
        """
            Lookup a Human Resource from an Email Address
        """

        db = current.db
        s3db = current.s3db

        if "<" in address:
            address = address.split("<")[1].split(">")[0]
        hrtable = s3db.hrm_human_resource
        ptable = db.pr_person
        ctable = s3db.pr_contact
        query = (ctable.value == address) & \
                (ctable.contact_method == "EMAIL") & \
                (ctable.pe_id == ptable.pe_id) & \
                (ptable.id == hrtable.person_id) & \
                (ctable.deleted == False) & \
                (ptable.deleted == False) & \
                (hrtable.deleted == False)
        possibles = db(query).select(hrtable.id,
                                     limitby=(0, 2))
        if len(possibles) == 1:
            return possibles.first().id

        return None

# END =========================================================================
