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
        if not record:
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
            series_id = db(table.name == "News").select(table.id,
                                                        cache=s3db.cache,
                                                        limitby=(0, 1)
                                                        ).first().id

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

            # Is this feed associated with an Org/Network?
            def lookup_pe(channel_id):
                ctable = s3db.msg_rss_channel
                channel_url = db(ctable.channel_id == channel_id).select(ctable.url,
                                                                         limitby=(0, 1)
                                                                         ).first().url
                ctable = s3db.pr_contact
                ptable = s3db.pr_pentity
                query = (ctable.contact_method == "RSS") & \
                        (ctable.value == channel_url) & \
                        (ctable.pe_id == ptable.pe_id)
                pe = db(query).select(ptable.pe_id,
                                      ptable.instance_type,
                                      limitby=(0, 1)
                                      ).first()
                if pe:
                    pe_type = pe.instance_type
                    otable = s3db[pe_type]
                    org_id = db(otable.pe_id == pe.pe_id).select(otable.id,
                                                                 limitby=(0, 1),
                                                                 ).first().id
                    return pe_type, org_id
                else:
                    return None, None

            pe_type, org_id = current.cache.ram("pe_channel_%s" % channel_id,
                                                lambda: lookup_pe(channel_id),
                                                time_expire=120
                                                )
            if pe_type == "org_organisation":
                s3db.cms_post_organisation.insert(post_id=post_id,
                                                  organisation_id=org_id,
                                                  )
            elif pe_type == "org_group":
                s3db.cms_post_organisation_group.insert(post_id=post_id,
                                                        group_id=org_id,
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

# END =========================================================================
