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

        s3db = current.s3db
        table = s3db.msg_rss
        record = current.db(table.message_id == message.message_id).select(table.title,
                                                                           limitby=(0, 1)
                                                                           ).first()
        if not record:
            return

        table = s3db.cms_post
        post_id = table.insert(title = record.title,
                               body = message.body,
                               )
        record = dict(id=post_id)
        s3db.update_super(table, record)
        url = message.from_address
        if url:
            s3db.doc_document.insert(doc_id = record["doc_id"],
                                     url = url,
                                     )

        # No Reply
        return

# END =========================================================================
