# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

""" Message Parsing

    Template-specific Message Parsers are defined here.

    @copyright: 2014 (c) Sahana Software Foundation
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

import os
import urllib2          # Needed for quoting & error handling on fetch
try:
    from cStringIO import StringIO    # Faster, where available
except:
    from StringIO import StringIO

from gluon import current
from gluon.tools import fetch

from s3.s3parser import S3Parsing

# =============================================================================
class S3Parser(object):
    """
       Message Parsing Template.
    """

    # -------------------------------------------------------------------------
    @staticmethod
    def parse_email(message):
        """
            Parse Email Messages into the CAP Module
        """

        pass

    # -------------------------------------------------------------------------
    @staticmethod
    def parse_rss(message):
        """
            Parse RSS Feeds into the CAP Module
        """

        db = current.db
        s3db = current.s3db
        table = s3db.msg_rss
        record = db(table.message_id == message.message_id).select(table.channel_id,
                                                                   table.title,
                                                                   table.from_address,
                                                                   table.body,
                                                                   table.date,
                                                                   table.location_id,
                                                                   #table.tags,
                                                                   table.author,
                                                                   limitby=(0, 1)
                                                                   ).first()
        if not record:
            return

        alert_table = s3db.cap_alert
        info_table = s3db.cap_info

        # Is this an Update or a Create?
        # @ToDo: Use guid?
        # Use Body
        body = record.body or record.title
        query = (info_table.description == body)
        exists = db(query).select(info_table.id,
                                  limitby=(0, 1)
                                  ).first()

        channel_id = record.channel_id
        #tags = record.tags

        author = record.author
        if author:
            ptable = s3db.pr_person
            # https://code.google.com/p/python-nameparser/
            from nameparser import HumanName
            name = HumanName(author)
            first_name = name.first
            middle_name = name.middle
            last_name = name.last
            query = (ptable.first_name == first_name) & \
                    (ptable.middle_name == middle_name) & \
                    (ptable.last_name == last_name)
            pexists = db(query).select(ptable.id,
                                       limitby=(0, 1)
                                       ).first()
            if pexists:
                person_id = pexists.id
            else:
                person_id = ptable.insert(first_name = first_name,
                                          middle_name = middle_name,
                                          last_name = last_name)
        else:
            person_id = None

        if exists:
            # @ToDo: Use XSLT
            info_id = exists.id
            db(info_table.id == info_id).update(headline = record.title,
                                                description = body,
                                                created_on = record.date,
                                                #location_id = record.location_id,
                                                #person_id = person_id,
                                                )
            # Read existing Tags (which came from remote)
            #ttable = db.cap_tag
            #ltable = db.cap_alert_tag
            #query = (ltable.alert_id == alert_id) & \
            #        (ltable.mci == 1) & \
            #        (ltable.tag_id == ttable.id)
            #rows = db(query).select(ttable.name)
            # Compare these to tags in current version of post
            #old_tags = [r.name for r in rows]
            #new_tags = []
            #delete_tags = []
            #for tag in tags:
            #    if tag not in old_tags:
            #        new_tags.append(tag)
            #for tag in old_tags:
            #    if tag not in tags:
            #        delete_tags.append(tag)
            #if new_tags or delete_tags:
            #    lookup_tags = []
            #    lookup_tags.extend(new_tags)
            #    lookup_tags.extend(delete_tags)
            #    _tags = db(ttable.name.belongs(lookup_tags)).select(ttable.id,
            #                                                        ttable.name,
            #                                                        ).as_dict(key="name")
            #for t in new_tags:
            #    tag = _tags.get(t, None)
            #    if tag:
            #        tag_id = tag["id"]
            #    else:
            #        tag_id = ttable.insert(name = t)
            #    ltable.insert(alert_id = alert_id,
            #                  tag_id = tag_id,
            #                  mci = 1, # This is an imported record, not added natively
            #                  )
            #for t in delete_tags:
            #    tag = _tags.get(t, None)
            #    if tag:
            #        query = (ltable.post_id == post_id) & \
            #                (ltable.tag_id == tag["id"]) & \
            #                (ltable.mci == 1) & \
            #                (ltable.deleted == False)
            #        db(query).delete()

        else:
            # Embedded link
            url = record.from_address
            try:
                file = fetch(url)
            except urllib2.URLError:
                response.error = str(sys.exc_info()[1])
                return output
            except urllib2.HTTPError:
                response.error = str(sys.exc_info()[1])
                return output
            File = StringIO(file)

            # Import via XSLT
            resource = s3db.resource("cap_alert")
            stylesheet = os.path.join(current.request.folder, "static", "formats", "cap", "import.xsl")
            success = resource.import_xml(File, stylesheet=stylesheet)

            # Is this feed associated with an Org/Network?
            #def lookup_pe(channel_id):
            #    ctable = s3db.msg_rss_channel
            #    channel_url = db(ctable.channel_id == channel_id).select(ctable.url,
            #                                                             limitby=(0, 1)
            #                                                             ).first().url
            #    ctable = s3db.pr_contact
            #    ptable = s3db.pr_pentity
            #    query = (ctable.contact_method == "RSS") & \
            #            (ctable.value == channel_url) & \
            #            (ctable.pe_id == ptable.pe_id)
            #    pe = db(query).select(ptable.pe_id,
            #                          ptable.instance_type,
            #                          limitby=(0, 1)
            #                          ).first()
            #    if pe:
            #        pe_type = pe.instance_type
            #        otable = s3db[pe_type]
            #        org_id = db(otable.pe_id == pe.pe_id).select(otable.id,
            #                                                     limitby=(0, 1),
            #                                                     ).first().id
            #        return pe_type, org_id
            #    else:
            #        return None, None

            #pe_type, org_id = current.cache.ram("pe_channel_%s" % channel_id,
            #                                    lambda: lookup_pe(channel_id),
            #                                    time_expire=120
            #                                    )
            #if pe_type == "org_organisation":
            #    s3db.cap_alert_organisation.insert(alert_id=alert_id,
            #                                       organisation_id=org_id,
            #                                       )
            #elif pe_type == "org_group":
            #    s3db.cap_alert_organisation_group.insert(alert_id=alert_id,
            #                                             group_id=org_id,
            #                                             )
            
            #if tags:
            #    ttable = db.cap_tag
            #    ltable = db.cap_alert_tag
            #    _tags = db(ttable.name.belongs(tags)).select(ttable.id,
            #                                                 ttable.name,
            #                                                 ).as_dict(key="name")
            #    for t in tags:
            #        tag = _tags.get(t, None)
            #        if tag:
            #            tag_id = tag["id"]
            #        else:
            #            tag_id = ttable.insert(name = t)
            #        ltable.insert(alert_id = alert_id,
            #                      tag_id = tag_id,
            #                      mci = 1, # This is an imported record, not added natively
            #                      )

        # No Reply
        return

# END =========================================================================
