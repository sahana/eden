# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

""" Message Parsing

    Template-specific Message Parsers are defined here.

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

from s3.s3parser import S3Parsing

# =============================================================================
class S3Parser(object):
    """
       Message Parsing Template.
    """

    # -------------------------------------------------------------------------
    @staticmethod
    def parse_rss(message):
        """
            Parse Feeds into the CMS Module

            @ToDo: Parse Tags
                   - add cms_tag & cms_post_tag records
                   - place post into the relevant series_id
        """

        db = current.db
        s3db = current.s3db
        table = s3db.msg_rss
        record = db(table.message_id == message.message_id).select(table.title,
                                                                   table.from_address,
                                                                   table.body,
                                                                   table.created_on,
                                                                   table.location_id,
                                                                   table.tags,
                                                                   table.author,
                                                                   limitby=(0, 1)
                                                                   ).first()
        if not record:
            return

        body = record.body or record.title
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
            exists = db(query).select(ptable.id,
                                      limitby=(0, 1)
                                      ).first()
            if exists:
                person_id = exists.id
            else:
                person_id = ptable.insert(first_name = first_name,
                                          middle_name = middle_name,
                                          last_name = last_name)
        else:
            person_id = None

        tags = record.tags
        url = record.from_address

        # Default to 'News' series
        table = s3db.cms_series
        series_id = db(table.name == "News").select(table.id,
                                                    limitby=(0, 1)
                                                    ).first().id

        table = db.cms_post
        post_id = table.insert(title = record.title,
                               body = body,
                               created_on = record.created_on,
                               location_id = record.location_id,
                               person_id = person_id,
                               series_id = series_id,
                               )
        record = dict(id=post_id)
        s3db.update_super(table, record)

        if url:
            s3db.doc_document.insert(doc_id = record["doc_id"],
                                     url = url,
                                     )

        if tags:
            ttable = db.cms_tag
            ltable = db.cms_tag_post
            for t in tags:
                tag = db(ttable.name == t).select(ttable.id,
                                                  limitby=(0, 1),
                                                  ).first()
                if tag:
                    tag_id = tag.id
                else:
                    tag_id = ttable.insert(name = t)
                ltable.insert(post_id = post_id,
                              tag_id = tag_id,
                              )

        # No Reply
        return

# END =========================================================================
