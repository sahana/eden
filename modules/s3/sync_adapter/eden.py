# -*- coding: utf-8 -*-

""" S3 Synchronization: Peer Repository Adapter

    @copyright: 2011-2016 (c) Sahana Software Foundation
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
import urllib2
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
from ..s3utils import S3ModuleDebug

DEBUG = False
if DEBUG:
    print >> sys.stderr, "S3SYNC: DEBUG MODE"
    _debug = S3ModuleDebug.on
else:
    _debug = S3ModuleDebug.off

# =============================================================================
class S3SyncAdapter(S3SyncBaseAdapter):
    """
        Sahana Eden Synchronization Adapter (default sync adapter)
    """

    # -------------------------------------------------------------------------
    # Methods to be implemented by subclasses:
    # -------------------------------------------------------------------------
    def register(self):
        """
            Register this site at the peer repository

            @return: True to indicate success, otherwise False
        """

        repository = self.repository

        if not repository.url:
            return True

        current.log.debug("S3Sync: register at %s" % (repository.url))

        # Construct the URL
        config = repository.config
        url = "%s/sync/repository/register.xml?repository=%s" % \
              (repository.url, config.uuid)

        current.log.debug("S3Sync: send registration to URL %s" % url)

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
                                        passwd=password,
                                        )
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
                message = "Registration successful"
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
                  message=message,
                  )

        return success

    # -------------------------------------------------------------------------
    def login(self):
        """
            Login at the peer repository

            @return: None if successful, otherwise the error
        """

        # Sahana Eden uses HTTP Basic Auth, no explicit login required
        return None

    # -------------------------------------------------------------------------
    def pull(self, task, onconflict=None):
        """
            Fetch updates from the peer repository and import them
            into the local database (active pull)

            @param task: the synchronization task (sync_task Row)
            @param onconflict: callback for automatic conflict resolution

            @return: tuple (error, mtime), with error=None if successful,
                     else error=message, and mtime=modification timestamp
                     of the youngest record sent
        """

        repository = self.repository
        xml = current.xml
        config = repository.config
        resource_name = task.resource_name

        current.log.debug("S3Sync: pull %s from %s" % (resource_name,
                                                       repository.url))

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
            current.log.debug("S3Sync: pull, using proxy=%s" % proxy)
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
        action = "fetch"
        response = None
        output = None

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
            action = "import"

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
                                onconflict=onconflict_callback,
                                )
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
                message = "Data imported successfully (%s records)" % count

        elif result == log.SUCCESS:
            # No data received from peer
            result = log.ERROR
            remote = True
            message = "No data received from peer"

        # Log the operation
        log.write(repository_id=repository.id,
                  resource_name=task.resource_name,
                  transmission=log.OUT,
                  mode=log.PULL,
                  action=action,
                  remote=remote,
                  result=result,
                  message=message)

        current.log.debug("S3Sync: import %s: %s" % (result, message))
        return (output, mtime)

    # -------------------------------------------------------------------------
    def push(self, task):
        """
            Extract new updates from the local database and send
            them to the peer repository (active push)

            @param task: the synchronization task (sync_task Row)

            @return: tuple (error, mtime), with error=None if successful,
                     else error=message, and mtime=modification timestamp
                     of the youngest record sent
        """

        xml = current.xml
        repository = self.repository
        config = repository.config
        resource_name = task.resource_name

        _debug("S3SyncRepository.push(%s, %s)", repository.url, resource_name)

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
        _debug("...push to URL %s", url)

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
                _debug("using proxy=%s", proxy)
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
                  action="send",
                  remote=remote,
                  result=result,
                  message=message)

        if output is not None:
            mtime = None
        return (output, mtime)

    # -------------------------------------------------------------------------
    def send(self,
             resource,
             start=None,
             limit=None,
             msince=None,
             filters=None,
             mixed=False,
             pretty_print=False):
        """
            Respond to an incoming pull from the peer repository

            @param resource: the resource to be synchronized
            @param start: index of the first record to send
            @param limit: maximum number of records to send
            @param msince: minimum modification date/time for records to send
            @param filters: URL filters for record extraction
            @param mixed: negotiate resource with peer (disregard resource)
            @param pretty_print: make the output human-readable

            @return: a dict {status, remote, message, response}, with:
                        - status....the outcome of the operation
                        - remote....whether the error was remote (or local)
                        - message...the log message
                        - response..the response to send to the peer
        """

        if not resource or mixed:
            msg = "Mixed resource synchronization not supported"
            return {"status": self.log.FATAL,
                    "message": msg,
                    "response": current.xml.json_message(False, 400, msg),
                    }

        # Export the data as S3XML
        output = resource.export_xml(start=start,
                                     limit=limit,
                                     filters=filters,
                                     msince=msince,
                                     pretty_print=pretty_print,
                                     )
        count = resource.results
        msg = "Data sent to peer (%s records)" % count

        # Set content type header
        headers = current.response.headers
        headers["Content-Type"] = "text/xml"

        return {"status": self.log.SUCCESS,
                "message": msg,
                "response": output,
                }

    # -------------------------------------------------------------------------
    def receive(self,
                source,
                resource,
                strategy=None,
                update_policy=None,
                conflict_policy=None,
                onconflict=None,
                last_sync=None,
                mixed=False):
        """
            Respond to an incoming push from the peer repository

            @param source: the input stream (list of file-like objects)
            @param resource: the target resource
            @param strategy: the import strategy
            @param update_policy: the update policy
            @param conflict_policy: the conflict resolution policy
            @param onconflict: callback for conflict resolution
            @param last_sync: the last synchronization date/time for the peer
            @param mixed: negotiate resource with peer (disregard resource)

            @return: a dict {status, remote, message, response}, with:
                        - status....the outcome of the operation
                        - remote....whether the error was remote (or local)
                        - message...the log message
                        - response..the response to send to the peer
        """

        if not resource or mixed:
            msg = "Mixed resource synchronization not supported"
            return {"status": self.log.FATAL,
                    "remote": False,
                    "message": msg,
                    "response": current.xml.json_message(False, 400, msg),
                    }

        repository = self.repository

        ignore_errors = True
        if onconflict:
            onconflict_callback = lambda item: onconflict(item,
                                                          repository,
                                                          resource)
        else:
            onconflict_callback = None

        output = resource.import_xml(source, format="xml",
                                     ignore_errors=ignore_errors,
                                     strategy=strategy,
                                     update_policy=update_policy,
                                     conflict_policy=conflict_policy,
                                     last_sync=last_sync,
                                     onconflict=onconflict_callback,
                                     )

        log = self.log

        if resource.error_tree is not None:
            # Validation error (log in any case)
            if ignore_errors:
                result = log.WARNING
            else:
                result = log.FATAL
            remote = True
            message = "%s" % resource.error
            for element in resource.error_tree.findall("resource"):
                error_msg = element.get("error", "unknown error")

                error_fields = element.findall("data[@error]")
                if error_fields:
                    for field in error_fields:
                        error_msg = field.get("error", "unknown error")
                        if error_msg:
                            msg = "(UID: %s) %s.%s=%s: %s" % \
                                    (element.get("uuid", None),
                                     element.get("name", None),
                                     field.get("field", None),
                                     field.get("value", field.text),
                                     error_msg)
                            message = "%s, %s" % (message, msg)
                else:
                    msg = "(UID: %s) %s: %s" % \
                          (element.get("uuid", None),
                           element.get("name", None),
                           error_msg)
                    message = "%s, %s" % (message, msg)
        else:
            result = log.SUCCESS
            remote = False
            message = "Data received from peer"

        return {"status": result,
                "remote": remote,
                "message": message,
                "response": output,
                }

# End =========================================================================
