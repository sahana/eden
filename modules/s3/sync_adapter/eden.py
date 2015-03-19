# -*- coding: utf-8 -*-

""" S3 Synchronization: Peer Repository Adapter

    @copyright: 2011-14 (c) Sahana Software Foundation
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

import sys
import urllib, urllib2
import traceback

try:
    from lxml import etree
except ImportError:
    print >> sys.stderr, "ERROR: lxml module needed for XML handling"
    raise

try:
    import json # try stdlib (Python 2.6)
except ImportError:
    try:
        import simplejson as json # try external module
    except:
        import gluon.contrib.simplejson as json # fallback to pure-Python module

from gluon import *

from ..s3datetime import s3_encode_iso_datetime
from ..s3sync import S3SyncBaseAdapter

DEBUG = False
if DEBUG:
    print >> sys.stderr, "S3SYNC: DEBUG MODE"

    def _debug(m):
        print >> sys.stderr, m
else:
    _debug = lambda m: None

# =============================================================================
class S3SyncAdapter(S3SyncBaseAdapter):
    """
        API Adapter for Sahana Eden
    """

    # -------------------------------------------------------------------------
    def register(self):
        """ Register at the repository """

        repository = self.repository

        if not repository.url:
            return True

        _debug("S3SyncRepository.register(%s)" % (repository.url))

        # Construct the URL
        config = repository.config
        url = "%s/sync/repository/register.xml?repository=%s" % \
              (repository.url, config.uuid)

        _debug("...send to URL %s" % url)

        # Generate the request
        req = urllib2.Request(url=url)
        handlers = []

        # Proxy handling
        proxy = repository.proxy or config.proxy or None
        if proxy:
            proxy_handler = urllib2.ProxyHandler({"http": proxy})
            handlers.append(proxy_handler)

        # Authentication
        username = repository.username
        password = repository.password
        if username and password:
            import base64
            base64string = base64.encodestring('%s:%s' %
                                               (username, password))[:-1]
            req.add_header("Authorization", "Basic %s" % base64string)
            passwd_manager = urllib2.HTTPPasswordMgrWithDefaultRealm()
            passwd_manager.add_password(realm=None,
                                        uri=url,
                                        user=username,
                                        passwd=password)
            auth_handler = urllib2.HTTPBasicAuthHandler(passwd_manager)
            handlers.append(auth_handler)

        # Install all handlers
        if handlers:
            opener = urllib2.build_opener(*handlers)
            urllib2.install_opener(opener)

        # Execute the request
        log = repository.log
        success = True
        remote = False
        try:
            f = urllib2.urlopen(req)
        except urllib2.HTTPError, e:
            result = log.FATAL
            remote = True # Peer error
            code = e.code
            message = e.read()
            success = False
            try:
                message_json = json.loads(message)
                message = message_json.get("message", message)
            except:
                pass
        except:
            result = log.FATAL
            code = 400
            message = sys.exc_info()[1]
            success = False
        else:
            ruid = None
            message = f.read()
            try:
                message_json = json.loads(message)
                message = message_json.get("message", message)
                ruid = message_json.get("sender", None)
            except:
                message = "registration successful"
            result = log.SUCCESS
            if ruid is not None:
                db = current.db
                rtable = current.s3db.sync_repository
                try:
                    db(rtable.id == repository.id).update(uuid=ruid)
                except:
                    pass

        # Log the operation
        log.write(repository_id=repository.id,
                  transmission=log.OUT,
                  mode=log.PUSH,
                  action="request registration",
                  remote=remote,
                  result=result,
                  message=message)

        return success

    # -------------------------------------------------------------------------
    def login(self):
        """ Login to the repository """

        # Sahana Eden uses HTTP Basic Auth, no login required
        return None

    # -------------------------------------------------------------------------
    def pull(self, task, onconflict=None):
        """
            Outgoing pull

            @param task: the task (sync_task Row)
        """

        repository = self.repository
        xml = current.xml
        config = repository.config
        resource_name = task.resource_name

        _debug("S3SyncRepository.pull(%s, %s)" % (repository.url, resource_name))

        # Construct the URL
        url = "%s/sync/sync.xml?resource=%s&repository=%s" % \
              (repository.url, resource_name, config.uuid)
        last_pull = task.last_pull
        if last_pull and task.update_policy not in ("THIS", "OTHER"):
            url += "&msince=%s" % s3_encode_iso_datetime(last_pull)
        url += "&include_deleted=True"

        # Send sync filters to peer
        filters = current.sync.get_filters(task.id)
        filter_string = None
        resource_name = task.resource_name
        for tablename in filters:
            prefix = "~" if not tablename or tablename == resource_name \
                            else tablename
            for k, v in filters[tablename].items():
                urlfilter = "[%s]%s=%s" % (prefix, k, v)
                url += "&%s" % urlfilter

        _debug("...pull from URL %s" % url)

        # Figure out the protocol from the URL
        url_split = url.split("://", 1)
        if len(url_split) == 2:
            protocol, path = url_split
        else:
            protocol, path = "http", None

        # Create the request
        req = urllib2.Request(url=url)
        handlers = []

        # Proxy handling
        proxy = repository.proxy or config.proxy or None
        if proxy:
            _debug("using proxy=%s" % proxy)
            proxy_handler = urllib2.ProxyHandler({protocol: proxy})
            handlers.append(proxy_handler)

        # Authentication handling
        username = repository.username
        password = repository.password
        if username and password:
            # Send auth data unsolicitedly (the only way with Eden instances):
            import base64
            base64string = base64.encodestring('%s:%s' %
                                               (username, password))[:-1]
            req.add_header("Authorization", "Basic %s" % base64string)
            # Just in case the peer does not accept that, add a 401 handler:
            passwd_manager = urllib2.HTTPPasswordMgrWithDefaultRealm()
            passwd_manager.add_password(realm=None,
                                        uri=url,
                                        user=username,
                                        passwd=password)
            auth_handler = urllib2.HTTPBasicAuthHandler(passwd_manager)
            handlers.append(auth_handler)

        # Install all handlers
        if handlers:
            opener = urllib2.build_opener(*handlers)
            urllib2.install_opener(opener)

        # Execute the request
        remote = False
        output = None
        response = None
        log = repository.log
        try:
            f = urllib2.urlopen(req)
        except urllib2.HTTPError, e:
            result = log.ERROR
            remote = True # Peer error
            code = e.code
            message = e.read()
            try:
                # Sahana-Eden would send a JSON message,
                # try to extract the actual error message:
                message_json = json.loads(message)
                message = message_json.get("message", message)
            except:
                pass
            # Prefix as peer error and strip XML markup from the message
            # @todo: better method to do this?
            message = "<message>%s</message>" % message
            try:
                markup = etree.XML(message)
                message = markup.xpath(".//text()")
                if message:
                    message = " ".join(message)
                else:
                    message = ""
            except etree.XMLSyntaxError:
                pass
            output = xml.json_message(False, code, message, tree=None)
        except:
            result = log.FATAL
            code = 400
            message = sys.exc_info()[1]
            output = xml.json_message(False, code, message)
        else:
            result = log.SUCCESS
            response = f

        # Process the response
        mtime = None
        if response:

            # Get import strategy and update policy
            strategy = task.strategy
            update_policy = task.update_policy
            conflict_policy = task.conflict_policy

            success = True
            message = ""

            # Import the data
            resource = current.s3db.resource(resource_name)
            if onconflict:
                onconflict_callback = lambda item: onconflict(item,
                                                              repository,
                                                              resource)
            else:
                onconflict_callback = None
            count = 0
            try:
                success = resource.import_xml(
                                response,
                                ignore_errors=True,
                                strategy=strategy,
                                update_policy=update_policy,
                                conflict_policy=conflict_policy,
                                last_sync=last_pull,
                                onconflict=onconflict_callback)
                count = resource.import_count
            except IOError, e:
                result = log.FATAL
                message = "%s" % e
                output = xml.json_message(False, 400, message)
            except Exception, e:
                # If we end up here, an uncaught error during import
                # has occured which indicates a code defect! We log it
                # and continue here, however - in order to maintain a
                # valid sync status, so that developers can restart
                # the process more easily after fixing the defect.
                result = log.FATAL
                message = "Uncaught Exception During Import: %s" % \
                          traceback.format_exc()
                output = xml.json_message(False, 500, sys.exc_info()[1])

            mtime = resource.mtime

            # Log all validation errors
            if resource.error_tree is not None:
                result = log.WARNING
                message = "%s" % resource.error
                for element in resource.error_tree.findall("resource"):
                    for field in element.findall("data[@error]"):
                        error_msg = field.get("error", None)
                        if error_msg:
                            msg = "(UID: %s) %s.%s=%s: %s" % \
                                   (element.get("uuid", None),
                                    element.get("name", None),
                                    field.get("field", None),
                                    field.get("value", field.text),
                                    field.get("error", None))
                            message = "%s, %s" % (message, msg)

            # Check for failure
            if not success:
                result = log.FATAL
                if not message:
                    message = "%s" % resource.error
                output = xml.json_message(False, 400, message)
                mtime = None

            # ...or report success
            elif not message:
                message = "data imported successfully (%s records)" % count

        elif result == log.SUCCESS:
            # No data received from peer
            result = log.ERROR
            remote = True
            message = "no data received from peer"

        # Log the operation
        log.write(repository_id=repository.id,
                  resource_name=task.resource_name,
                  transmission=log.OUT,
                  mode=log.PULL,
                  action=None,
                  remote=remote,
                  result=result,
                  message=message)

        _debug("S3SyncRepository.pull import %s: %s" % (result, message))
        return (output, mtime)

    # -------------------------------------------------------------------------
    def push(self, task):
        """
            Outgoing push

            @param task: the sync_task Row
        """

        xml = current.xml
        repository = self.repository
        config = repository.config
        resource_name = task.resource_name

        _debug("S3SyncRepository.push(%s, %s)" % (repository.url, resource_name))

        # Construct the URL
        url = "%s/sync/sync.xml?resource=%s&repository=%s" % \
              (repository.url, resource_name, config.uuid)
        strategy = task.strategy
        if strategy:
            url += "&strategy=%s" % ",".join(strategy)
        update_policy = task.update_policy
        if update_policy:
            url += "&update_policy=%s" % update_policy
        conflict_policy = task.conflict_policy
        if conflict_policy:
            url += "&conflict_policy=%s" % conflict_policy
        last_push = task.last_push
        if last_push and update_policy not in ("THIS", "OTHER"):
            url += "&msince=%s" % s3_encode_iso_datetime(last_push)
        else:
            last_push = None
        _debug("...push to URL %s" % url)

        # Define the resource
        resource = current.s3db.resource(resource_name,
                                         include_deleted=True)

        # Apply sync filters for this task
        filters = current.sync.get_filters(task.id)

        # Export the resource as S3XML
        data = resource.export_xml(filters=filters,
                                   msince=last_push)
        count = resource.results or 0
        mtime = resource.muntil

        # Transmit the data via HTTP
        remote = False
        output = None
        log = repository.log
        if data and count:

            # Find the protocol
            url_split = url.split("://", 1)
            if len(url_split) == 2:
                protocol, path = url_split
            else:
                protocol, path = "http", None

            # Generate the request
            import urllib2
            req = urllib2.Request(url=url, data=data)
            req.add_header('Content-Type', "text/xml")
            handlers = []

            # Proxy handling
            proxy = repository.proxy or config.proxy or None
            if proxy:
                _debug("using proxy=%s" % proxy)
                proxy_handler = urllib2.ProxyHandler({protocol: proxy})
                handlers.append(proxy_handler)

            # Authentication
            username = repository.username
            password = repository.password
            if username and password:
                # send auth credentials unsolicitedly
                import base64
                base64string = base64.encodestring('%s:%s' %
                                                   (username, password))[:-1]
                req.add_header("Authorization", "Basic %s" % base64string)
                # Just in case the peer does not accept that
                # => add a 401 handler:
                passwd_manager = urllib2.HTTPPasswordMgrWithDefaultRealm()
                passwd_manager.add_password(realm=None,
                                            uri=url,
                                            user=username,
                                            passwd=password)
                auth_handler = urllib2.HTTPBasicAuthHandler(passwd_manager)
                handlers.append(auth_handler)

            # Install all handlers
            if handlers:
                opener = urllib2.build_opener(*handlers)
                urllib2.install_opener(opener)

            # Execute the request
            try:
                f = urllib2.urlopen(req)
            except urllib2.HTTPError, e:
                result = log.FATAL
                remote = True # Peer error
                code = e.code
                message = e.read()
                try:
                    # Sahana-Eden sends a JSON message,
                    # try to extract the actual error message:
                    message_json = json.loads(message)
                    message = message_json.get("message", message)
                except:
                    pass
                output = xml.json_message(False, code, message)
            except:
                result = log.FATAL
                code = 400
                message = sys.exc_info()[1]
                output = xml.json_message(False, code, message)
            else:
                result = log.SUCCESS
                message = "data sent successfully (%s records)" % count

        else:
            # No data to send
            result = log.WARNING
            message = "No data to send"

        # Log the operation
        log.write(repository_id=repository.id,
                  resource_name=task.resource_name,
                  transmission=log.OUT,
                  mode=log.PUSH,
                  action=None,
                  remote=remote,
                  result=result,
                  message=message)

        if output is not None:
            mtime = None
        return (output, mtime)

# End =========================================================================
