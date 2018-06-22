# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

""" Message Parsing

    Template-specific Message Parsers are defined here.

    @copyright: 2014-2018 (c) Sahana Software Foundation
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
#try:
#    from cStringIO import StringIO    # Faster, where available
#except ImportError:
#    from StringIO import StringIO

from gluon import current
#from gluon.tools import fetch

#from s3.s3parser import S3Parsing

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


        #channel_id = record.channel_id
        tags = record.tags or []

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
    @classmethod
    def parse_rss_2_cap(cls, message):
        """
            Parse RSS/Atom feed entries and import their CAP-XML sources
            as cap_alerts

            @param message: the msg_message Row to parse

            @returns: a reply to the sender (always None here)
        """

        db = current.db
        s3db = current.s3db

        message_id = message.message_id

        # Check parsing status for this message
        stable = s3db.msg_parsing_status
        query = (stable.message_id == message_id) & \
                (stable.is_parsed == True)
        if db(query).select(stable.id, limitby=(0, 1)).first():
            # Already parsed
            return None

        # Get the RSS/Atom entry for the message
        etable = s3db.msg_rss
        entry = db(etable.message_id == message_id).select(etable.id,
                                                           etable.channel_id,
                                                           etable.from_address,
                                                           #etable.title,
                                                           #etable.body,
                                                           #etable.date,
                                                           #etable.location_id,
                                                           #etable.author,
                                                           limitby = (0, 1),
                                                           ).first()
        if not entry:
            # Not found
            return None

        # Get the CAP-XML source for this entry
        tree, version, error = cls.fetch_cap(entry)

        if tree:
            # Version-specific import transformation stylesheet?
            if version == "cap11":
                filename = "import11.xsl"
            else:
                # Default CAP-1.2
                filename = "import.xsl"
            stylesheet = os.path.join(current.request.folder,
                                      "static", "formats", "cap", filename,
                                      )

            # Import the CAP-XML
            resource = s3db.resource("cap_alert")
            try:
                resource.import_xml(tree,
                                    stylesheet = stylesheet,
                                    ignore_errors = True,
                                    )
            except (IOError, SyntaxError):
                import sys
                error = "CAP import error: %s" % sys.exc_info()[1]
            else:
                if resource.error:
                    # Import validation error
                    # NB can access the exact error through resource.error_tree
                    error = resource.error
                elif resource.import_count == 0:
                    # No error, but nothing imported either
                    error = "No CAP alerts found in source"
                else:
                    # Success
                    error = None
                    msg = "%s new CAP alerts imported, %s alerts updated" % (
                            len(resource.import_created),
                            len(resource.import_updated))
                    current.log.info(msg)

        if error:
            # TODO report the error back to the scheduler run,
            #      so it becomes available in the web GUI
            current.log.error(error)

        # No Reply
        return None

    # -------------------------------------------------------------------------
    @classmethod
    def fetch_cap(cls, entry):
        """
            Fetch and parse the CAP-XML source for an RSS/Atom feed entry

            @param entry: the RSS/Atom feed entry (msg_rss Row), containing:
                          - id
                          - channel_id
                          - from_address

            @returns: tuple (tree, version, error)
                      - tree    = ElementTree of the CAP source
                      - version = the detected CAP version
                      - error   = error message if unsuccessful, else None
        """

        db = current.db
        s3db = current.s3db

        # Get the URLs for all <link>s in this entry which are marked as cap+xml
        ltable = s3db.msg_rss_link
        query = (ltable.rss_id == entry.id) & \
                (ltable.type == "application/cap+xml") & \
                (ltable.deleted == False)
        links = db(query).select(ltable.url)
        urls = [link.url for link in links if link.url]

        # Add the main <link> of the entry (=from_address) as fallback
        if entry.from_address:
            urls.append(entry.from_address)

        # Simple domain formatter for URLs
        from urlparse import urlparse
        url_format = "{uri.scheme}://{uri.netloc}/".format

        # Get domain/username/password for the channel
        ctable = s3db.msg_rss_channel
        query = (ctable.channel_id == entry.channel_id) & \
                (ctable.deleted == False)
        channel = db(query).select(ctable.url,
                                   ctable.username,
                                   ctable.password,
                                   limitby = (0, 1),
                                   ).first()
        if channel:
            channel_domain = url_format(uri=urlparse(channel.url))
            username = channel.username
            password = channel.password
        else:
            channel_domain = None
            username = password = None

        # Iterate over <link> URLs to find the CAP source
        errors = []
        version, tree = None, None
        for url in urls:

            error = None
            current.log.debug("Fetching CAP-XML from %s" % url)

            # If same domain as channel, use channel credentials for auth
            if channel_domain and url_format(uri=urlparse(url)) == channel_domain:
                opener = cls.opener(url, username=username, password=password)
            else:
                opener = cls.opener(url)

            # Fetch the link content
            try:
                content = opener.open(url)
            except urllib2.HTTPError, e:
                # HTTP status
                error = "HTTP %s: %s" % (e.code, e.read())
            except urllib2.URLError, e:
                # URL Error (network error)
                error = "CAP source unavailable (%s)" % e.reason
            except Exception:
                # Other error (local error)
                import sys
                error = sys.exc_info()[1]
            else:
                # Try parse
                tree, version, error = cls.parse_cap(content)

            if tree:
                # XML source found => proceed to import
                break
            elif error:
                errors.append(error)
            else:
                errors.append("Not a valid CAP source: %s" % url)

        return tree, version, error

    # -------------------------------------------------------------------------
    @staticmethod
    def parse_cap(source):
        """
            Parse a CAP-XML source and detect the CAP version

            @param source: the CAP-XML source

            @returns: tuple (tree, version, error)
                      - tree    = ElementTree of the CAP source
                      - version = the detected CAP version
                      - error   = error message if parsing failed, else None
        """

        version = error = None

        xml = current.xml

        # Attempt to parse the source
        tree = xml.parse(source)

        if not tree:
            # Capture parser error
            error = xml.error or "XML parsing failed"

        else:
            # All supported CAP versions and their namespace URIs
            namespaces = (("cap11", "urn:oasis:names:tc:emergency:cap:1.1"),
                          ("cap12", "urn:oasis:names:tc:emergency:cap:1.2"),
                          )

            # Default
            version = "cap12"

            root = tree.getroot()
            for ns, uri in namespaces:
                if root.xpath("/%s:alert[1]" % ns, namespaces = {ns: uri}):
                    version = ns
                    break

        return tree, version, error

    # -------------------------------------------------------------------------
    @staticmethod
    def opener(url,
               headers=None,
               username=None,
               password=None,
               preemptive_auth=False,
               proxy=None,
               ):
        """
            Configure a HTTP opener to fetch CAP messages

            @param url: the target URL
            @param headers: HTTP request headers, list of tuples (header, value)
            @param username: user name for auth
            @param password: password for auth
            @param preemptive_auth: send credentials without waiting for a
                                    HTTP401 challenge
            @param proxy: proxy URL (if required)

            @returns: an OpenerDirector instance with proxy and
                      auth handlers installed

            @example:
                url = "http://example.com/capfile.xml"
                opener = self._opener(url, username="user", password="password")
                content = opener.open(url)
        """

        # Configure opener headers
        addheaders = []
        if headers:
            addheaders.extend(headers)

        # Configure opener handlers
        handlers = []

        # Proxy handling
        if proxy:
            # Figure out the protocol from the URL
            url_split = url.split("://", 1)
            if len(url_split) == 2:
                protocol = url_split[0]
            else:
                protocol = "http"
            proxy_handler = urllib2.ProxyHandler({protocol: proxy})
            handlers.append(proxy_handler)

        # Authentication handling
        if username and password:
            # Add a 401 handler
            passwd_manager = urllib2.HTTPPasswordMgrWithDefaultRealm()
            passwd_manager.add_password(realm = None,
                                        uri = url,
                                        user = username,
                                        passwd = password,
                                        )
            auth_handler = urllib2.HTTPBasicAuthHandler(passwd_manager)
            handlers.append(auth_handler)

        # Create the opener
        opener = urllib2.build_opener(*handlers)

        # Pre-emptive basic auth
        if preemptive_auth and username and password:
            import base64
            base64string = base64.encodestring('%s:%s' % (username, password))[:-1]
            addheaders.append(("Authorization", "Basic %s" % base64string))

        if addheaders:
            opener.addheaders = addheaders

        return opener

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

        #channel_id = record.channel_id

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
