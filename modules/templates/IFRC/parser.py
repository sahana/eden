# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

""" Message Parsing

    Template-specific Message Parsers are defined here.

    @copyright: 2013-2016 (c) Sahana Software Foundation
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

__all__ = ("S3Parser",)

import datetime

from gluon import current

from s3.s3parser import S3Parsing

# =============================================================================
class S3Parser(object):
    """
       Message Parsing Template.
    """

    # -------------------------------------------------------------------------
    @staticmethod
    def _parse_value(text, fieldname):
        """
            Parse a value from a piece of text
        """

        parts = text.split(":%s:" % fieldname, 1)
        parts = parts[1].split(":", 1)
        result = parts[0]
        return result

    # -------------------------------------------------------------------------
    @staticmethod
    def parse_email(message):
        """
            Parse Responses
                - reply to mails from the Monitor service
                - parse mails directed to the Deploy Module

            @ToDo: Use template for format of field/value encoding
        """

        db = current.db
        s3db = current.s3db
        reply = None

        # Need to use Raw currently as not showing in Body
        message_id = message.message_id
        table = s3db.msg_email
        record = db(table.message_id == message_id).select(table.raw,
                                                           limitby=(0, 1)
                                                           ).first()
        if not record:
            return reply

        message_body = record.raw
        if not message_body:
            return reply

        # What type of message is this?
        if ":run_id:" in message_body:
            # Monitor Check

            # Parse Mail
            try:
                run_id = S3Parser._parse_value(message_body, "run_id")
                run_id = int(run_id)
            except:
                return reply
            try:
                to = S3Parser._parse_value(message_body, "reply_to")
            except:
                return reply

            # Send Reply
            now = datetime.datetime.utcnow().isoformat()
            subject = "MONITOR REPLY: Mail Received and Parsed OK"
            message = """Test message sent to %s from :run_id:%s: arrived fine & was parsed at %s.""" % \
                (current.deployment_settings.get_base_public_url(), run_id, now)
            result = current.msg.send_email(to,
                                            subject,
                                            message)
            return reply
        elif ":mission_id:" in message_body:
            # Response to a Deployment Alert
            pass
        else:
            # Don't know what this is
            return reply

        try:
            mission_id = S3Parser._parse_value(message_body, "mission_id")
            mission_id = int(mission_id)
        except:
            return reply

        # Link Message to Mission
        data = dict(message_id=message_id,
                    mission_id=mission_id,
                    )

        # Can we identify the Member?
        person_id = S3Parsing().lookup_person(message.from_address)
        if person_id:
            # Sender identified => look up HR records
            atable = s3db.deploy_application
            htable = s3db.hrm_human_resource
            left = atable.on(htable.id == atable.human_resource_id)
            rows = db((htable.person_id == person_id) & \
                      (htable.deleted != True)).select(htable.id,
                                                       atable.id,
                                                       atable.active,
                                                       orderby=~htable.modified_on,
                                                       left=left,
                                                       )
            hr_id = None
            if len(rows) == 1:
                # Single profile
                hr_id = rows[0][htable.id]
            else:
                # Multiple profiles => prefer deployable
                rows = [row for row in rows
                            if row[atable.id] and row[atable.active]]
                if len(rows) == 1:
                    # Single deployable profile
                    hr_id = rows[0][htable.id]
            if hr_id:
                data["human_resource_id"] = hr_id

        table = s3db.deploy_response
        table.insert(**data)

        # Are there any attachments?
        atable = s3db.msg_attachment
        atts = db(atable.message_id == message_id).select(atable.document_id)
        if atts:
            dtable = db.doc_document
            ltable = s3db.deploy_mission_document
            if hr_id:
                # Set documents to the Member's doc_id
                hrtable = db.hrm_human_resource
                doc_id = db(hrtable.id == hr_id).select(hrtable.doc_id,
                                                        limitby=(0, 1)
                                                        ).first().doc_id
            for row in atts:
                # Link to Mission
                document_id = row.document_id
                ltable.insert(mission_id = mission_id,
                              message_id = message_id,
                              document_id = document_id)
                if hr_id:
                    db(dtable.id == document_id).update(doc_id = doc_id)

        # @ToDo: Reply?
        #reply = ...

        return reply

# END =========================================================================
