# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

""" Message Parsing API

    API to parse Inbound Messages.

    Message Parsing subroutines are defined here.
    These subroutines define different sets of parsing rules.
    Imported by private/templates/<template>
    where <template> is the "default" template by default.

    @copyright: 2013 (c) Sahana Software Foundation
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

__all__ = ["S3Parser"]

from gluon import current

# =============================================================================
class S3Parser(object):
    """
       Message Parsing Template.
    """

    # -------------------------------------------------------------------------
    @staticmethod
    def parse_email(message):
        """
            Parse Responses directed to the Deploy Module
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

        # Is this a Response to an Alert?
        # @ToDo: Use template
        if ":mission_id:" not in message_body:
            return reply

        parts = message_body.split(":mission_id:", 1)
        try:
            parts = parts[1].split(":", 1)
        except:
            return reply

        mission_id = parts[0]
        if not mission_id:
            return reply

        try:
            mission_id = int(mission_id)
        except:
            return reply

        # Link Message to Mission
        data = dict(message_id=message_id,
                    mission_id=mission_id,
                    )

        # Can we identify the Member?
        from_address = message.from_address
        if "<" in from_address:
            from_address = from_address.split("<")[1].split(">")[0]
        atable = s3db.deploy_human_resource_application
        hrtable = db.hrm_human_resource
        ptable = db.pr_person
        ctable = s3db.pr_contact
        query = (ctable.value == from_address) & \
                (ctable.contact_method == "EMAIL") & \
                (ctable.pe_id == ptable.pe_id) & \
                (ptable.id == hrtable.person_id) & \
                (atable.human_resource_id == hrtable.id) & \
                (atable.active == True) & \
                (ctable.deleted == False)
        possibles = db(query).select(hrtable.id,
                                     limitby=(0, 2))
        if len(possibles) == 1:
            data["human_resource_id"] = possibles.first().id

        table = s3db.deploy_response
        table.insert(**data)

        # @ToDo: Reply?
        reply = None

        return reply

# END =========================================================================
