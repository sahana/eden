# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

""" Message Parsing

    Template-specific Message Parsers are defined here.

    @copyright: 2014-2019 (c) Sahana Software Foundation
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
    def parse_rss_2_cms(message):
        """
            Parse Feeds into the CMS Module
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
                                                                   table.tags,
                                                                   table.author,
                                                                   limitby=(0, 1)
                                                                   ).first()
        if not record or not record.body:
            return

        post_table = s3db.cms_post

        # Is this an Update or a Create?
        body = record.body or record.title
        url = record.from_address
        if url:
            doc_table = s3db.doc_document
            exists = db(doc_table.url == url).select(doc_table.doc_id,
                                                     limitby=(0, 1)
                                                     ).first()
            if exists:
                exists = db(post_table.doc_id == exists.doc_id).select(post_table.id,
                                                                       limitby=(0, 1)
                                                                       ).first()
        else:
            # Use Body
            exists = db(post_table.body == body).select(post_table.id,
                                                        limitby=(0, 1)
                                                        ).first()


        channel_id = record.channel_id
        tags = record.tags

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
                s3db.update_super(ptable, dict(id=person_id))
        else:
            person_id = None

        if exists:
            post_id = exists.id
            db(post_table.id == post_id).update(title = record.title,
                                                body = body,
                                                created_on = record.date,
                                                location_id = record.location_id,
                                                person_id = person_id,
                                                )
            # Read existing Tags (which came from remote)
            ttable = db.cms_tag
            ltable = db.cms_tag_post
            query = (ltable.post_id == post_id) & \
                    (ltable.mci == 1) & \
                    (ltable.tag_id == ttable.id)
            rows = db(query).select(ttable.name)
            # Compare these to tags in current version of post
            old_tags = [r.name for r in rows]
            new_tags = []
            delete_tags = []
            for tag in tags:
                if tag not in old_tags:
                    new_tags.append(tag)
            for tag in old_tags:
                if tag not in tags:
                    delete_tags.append(tag)
            if new_tags or delete_tags:
                lookup_tags = []
                lookup_tags.extend(new_tags)
                lookup_tags.extend(delete_tags)
                _tags = db(ttable.name.belongs(lookup_tags)).select(ttable.id,
                                                                    ttable.name,
                                                                    ).as_dict(key="name")
            for t in new_tags:
                tag = _tags.get(t, None)
                if tag:
                    tag_id = tag["id"]
                else:
                    tag_id = ttable.insert(name = t)
                ltable.insert(post_id = post_id,
                              tag_id = tag_id,
                              mci = 1, # This is an imported record, not added natively
                              )
            for t in delete_tags:
                tag = _tags.get(t, None)
                if tag:
                    query = (ltable.post_id == post_id) & \
                            (ltable.tag_id == tag["id"]) & \
                            (ltable.mci == 1) & \
                            (ltable.deleted == False)
                    db(query).delete()

        else:
            # Default to 'News' series
            table = db.cms_series
            series = db(table.name == "News").select(table.id,
                                                     cache=s3db.cache,
                                                     limitby=(0, 1)
                                                     ).first()
            try:
                series_id = series.id
            except:
                raise KeyError("News Series not present in CMS module")

            post_id = post_table.insert(title = record.title,
                                        body = body,
                                        created_on = record.date,
                                        location_id = record.location_id,
                                        person_id = person_id,
                                        series_id = series_id,
                                        mci = 1, # This is an imported record, not added natively
                                        )
            record = dict(id=post_id)
            s3db.update_super(post_table, record)

            # Source link
            if url:
                doc_table.insert(doc_id = record["doc_id"],
                                 url = url,
                                 )

            if tags:
                ttable = db.cms_tag
                ltable = db.cms_tag_post
                _tags = db(ttable.name.belongs(tags)).select(ttable.id,
                                                             ttable.name,
                                                             ).as_dict(key="name")
                for t in tags:
                    tag = _tags.get(t, None)
                    if tag:
                        tag_id = tag["id"]
                    else:
                        tag_id = ttable.insert(name = t)
                    ltable.insert(post_id = post_id,
                                  tag_id = tag_id,
                                  mci = 1, # This is an imported record, not added natively
                                  )

        # No Reply
        return

    # -------------------------------------------------------------------------
    @staticmethod
    def parse_rss_2_cap(message):
        """
            Parse RSS Feeds into the CAP Module
        """

        db = current.db
        s3db = current.s3db
        table = s3db.msg_rss
        message_id = message.message_id
        record = db(table.message_id == message_id).select(table.id,
                                                           table.channel_id,
                                                           table.title,
                                                           table.from_address,
                                                           table.body,
                                                           table.date,
                                                           table.location_id,
                                                           table.author,
                                                           limitby=(0, 1)
                                                           ).first()
        if not record:
            return

        pstable = s3db.msg_parsing_status
        # not adding (pstable.channel_id == record.channel_id) to query
        # because two channels (http://host.domain/eden/cap/public.rss and
        # (http://host.domain/eden/cap/alert.rss) may contain common url
        # eg. http://host.domain/eden/cap/public/xx.cap
        pquery = (pstable.message_id == message_id)
        prows = db(pquery).select(pstable.id, pstable.is_parsed)
        for prow in prows:
            if prow.is_parsed:
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
                s3db.update_super(ptable, dict(id=person_id))
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

        else:
            # Embedded link
            url = record.from_address
            import_xml = s3db.resource("cap_alert").import_xml
            stylesheet = os.path.join(current.request.folder, "static", "formats", "cap", "import.xsl")
            try:
                file = fetch(url)
            except urllib2.HTTPError, e:
                import base64
                rss_table = s3db.msg_rss_channel
                query = (rss_table.channel_id == record.channel_id)
                channel = db(query).select(rss_table.date,
                                           rss_table.etag,
                                           rss_table.url,
                                           rss_table.username,
                                           rss_table.password,
                                           limitby=(0, 1)).first()
                username = channel.username
                password = channel.password
                if e.code == 401 and username and password:
                    request = urllib2.Request(url)
                    base64string = base64.encodestring("%s:%s" % (username, password))
                    request.add_header("Authorization", "Basic %s" % base64string)
                else:
                    request = None

                try:
                    file = urllib2.urlopen(request).read() if request else fetch(url)
                except urllib2.HTTPError, e:
                    # Check if there are links to look into
                    from urlparse import urlparse
                    ltable = s3db.msg_rss_link
                    query_ = (ltable.rss_id == record.id) & (ltable.deleted != True)
                    rows_ = db(query_).select(ltable.type,
                                              ltable.url)
                    url_format = "{uri.scheme}://{uri.netloc}/".format
                    url_domain = url_format(uri=urlparse(url))
                    for row_ in rows_:
                        url = row_.url
                        if url and row_.type == "application/cap+xml" and \
                           url_domain == url_format(uri=urlparse(url)):
                            # Same domain, so okey to use same username/pwd combination
                            if e.code == 401 and username and password:
                                request = urllib2.Request(url)
                                request.add_header("Authorization", "Basic %s" % base64string)
                            else:
                                request = None
                            try:
                                file = urllib2.urlopen(request).read() if request else fetch(url)
                            except urllib2.HTTPError, e:
                                current.log.error("Getting content from link failed: %s" % e)
                            else:
                                # Import via XSLT
                                import_xml(StringIO(file), stylesheet=stylesheet, ignore_errors=True)
                else:
                    # Import via XSLT
                    import_xml(StringIO(file), stylesheet=stylesheet, ignore_errors=True)
            else:
                # Public Alerts
                # eg. http://host.domain/eden/cap/public/xx.cap
                # Import via XSLT
                import_xml(StringIO(file), stylesheet=stylesheet, ignore_errors=True)

        # No Reply
        return

    # -------------------------------------------------------------------------
    @staticmethod
    def parse_tweet(message):
        """
            Parse Tweets into the CMS Module
        """

        db = current.db
        s3db = current.s3db
        table = s3db.msg_twitter
        record = db(table.message_id == message.message_id).select(table.channel_id,
                                                                   table.from_address,
                                                                   table.body,
                                                                   table.date,
                                                                   #table.location_id,
                                                                   #table.author,
                                                                   limitby=(0, 1)
                                                                   ).first()
        if not record:
            return

        channel_id = record.channel_id

        post_table = s3db.cms_post

        # Is this an Update or a Create?
        # Use Body
        body = record.body
        exists = db(post_table.body == body).select(post_table.id,
                                                    limitby=(0, 1)
                                                    ).first()

        if exists:
            post_id = exists.id
            db(post_table.id == post_id).update(#title = record.title,
                                                body = body,
                                                created_on = record.date,
                                                #location_id = record.location_id,
                                                #person_id = person_id,
                                                )

        else:
            # Default to 'News' series
            table = db.cms_series
            series = db(table.name == "News").select(table.id,
                                                     cache=s3db.cache,
                                                     limitby=(0, 1)
                                                     ).first()
            try:
                series_id = series.id
            except:
                raise KeyError("News Series not present in CMS module")

            post_id = post_table.insert(#title = record.title,
                                        body = body,
                                        created_on = record.date,
                                        #location_id = record.location_id,
                                        #person_id = person_id,
                                        series_id = series_id,
                                        mci = 1, # This is an imported record, not added natively
                                        )
            record = dict(id=post_id)
            s3db.update_super(post_table, record)

        # No Reply
        return

# END =========================================================================
