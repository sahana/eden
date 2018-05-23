# -*- coding: utf-8 -*-

""" S3 Synchronization: Peer Repository Adapter

    @copyright: 2011-2018 (c) Sahana Software Foundation
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

import datetime
import json
import sys
import traceback
import urllib2

try:
    from lxml import etree
except ImportError:
    sys.stderr.write("ERROR: lxml module needed for XML handling\n")
    raise

from gluon import current

from ..s3datetime import s3_encode_iso_datetime
from ..s3sync import S3SyncBaseAdapter

# =============================================================================
class S3SyncAdapter(S3SyncBaseAdapter):
    """
        Sahana Eden Synchronization Adapter (default sync adapter)
    """

    # -------------------------------------------------------------------------
    def register(self):
        """
            Register this site at the peer repository

            @return: True to indicate success, otherwise False
        """

        repository = self.repository
        if not repository.url:
            return True

        # Construct the URL
        url = "%s/sync/repository/register.json" % repository.url
        current.log.debug("S3Sync: register at %s" % url)

        # The registration parameters
        config = repository.config
        name = current.deployment_settings.get_base_public_url().split("//", 1)[1]
        parameters = {"uuid": config.uuid,
                      "name": name,
                      "apitype": "eden",
                      }
        data = json.dumps(parameters)

        # Send registration request
        opener = self._http_opener(url,
                                   headers = [("Content-Type", "application/json"),
                                              ],
                                   )

        # Send the request
        log = repository.log
        success = True
        remote = False
        try:
            f = opener.open(url, data)
        except urllib2.HTTPError, e:
            # Remote error
            result = log.FATAL
            remote = True
            message = e.read()
            success = False
            try:
                message_json = json.loads(message)
                message = message_json.get("message", message)
            except:
                pass

        except urllib2.URLError, e:
            # URL Error (network error)
            result = log.ERROR
            remote = True
            message = "Peer repository unavailable (%s)" % e.reason

        except:
            # Local error
            result = log.FATAL
            message = sys.exc_info()[1]
            success = False

        else:
            result = log.SUCCESS

            message = f.read()
            try:
                message_json = json.loads(message)
                message = message_json.get("message", message)
                ruid = message_json.get("sender", None)
            except:
                message = "Registration successful"
                ruid = None

            if ruid is not None:
                # Update the peer repository UID
                db = current.db
                rtable = current.s3db.sync_repository
                try:
                    db(rtable.id == repository.id).update(uuid=ruid)
                except:
                    pass

        # Log the operation
        log.write(repository_id = repository.id,
                  transmission = log.OUT,
                  mode = log.PUSH,
                  action = "request registration",
                  remote = remote,
                  result = result,
                  message = message,
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

        xml = current.xml
        debug = current.log.debug

        repository = self.repository
        config = repository.config

        # Verify that the target resource exists
        resource_name = task.resource_name
        try:
            resource = current.s3db.resource(resource_name)
        except AttributeError:
            # Target resource is not defined
            debug("Undefined resource %s - sync task ignored" % resource_name)
            return (None, None)

        debug("S3Sync: pull %s from %s" % (resource_name, repository.url))

        # Construct the URL
        url = "%s/sync/sync.xml?resource=%s&repository=%s" % \
              (repository.url, resource_name, config.uuid)
        last_pull = task.last_pull
        if last_pull and task.update_policy not in ("THIS", "OTHER"):
            url += "&msince=%s" % s3_encode_iso_datetime(last_pull)
        if task.components is False: # Allow None to remain the old default of 'Include Components'
            url += "&components=None"
        url += "&include_deleted=True"

        # Add sync filters to URL
        from urllib import quote
        filters = current.sync.get_filters(task.id)
        for tablename in filters:
            prefix = "~" if not tablename or tablename == resource_name \
                            else tablename
            for k, v in filters[tablename].items():
                urlfilter = "[%s]%s=%s" % (prefix, k, quote(v))
                url += "&%s" % urlfilter

        debug("...pull from URL %s" % url)

        # Execute the request
        remote = False
        action = "fetch"
        response = None
        output = None

        opener = self._http_opener(url)
        log = repository.log
        try:
            f = opener.open(url)

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

        except urllib2.URLError, e:
            # URL Error (network error)
            result = log.ERROR
            remote = True
            message = "Peer repository unavailable (%s)" % e.reason
            output = xml.json_message(False, 400, message)

        except:
            result = log.FATAL
            message = sys.exc_info()[1]
            output = xml.json_message(False, 400, message)

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
            if onconflict:
                onconflict_callback = lambda item: onconflict(item,
                                                              repository,
                                                              resource,
                                                              )
            else:
                onconflict_callback = None
            count = 0
            try:
                success = resource.import_xml(response,
                                              ignore_errors = True,
                                              strategy = strategy,
                                              update_policy = update_policy,
                                              conflict_policy = conflict_policy,
                                              last_sync = last_pull,
                                              onconflict = onconflict_callback,
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
                if not count:
                    message = "No data to import (already up-to-date)"
                else:
                    message = "Data imported successfully (%s records)" % count

        elif result == log.SUCCESS:
            # No data received from peer
            result = log.ERROR
            remote = True
            message = "No data received from peer"

        # Log the operation
        log.write(repository_id = repository.id,
                  resource_name = task.resource_name,
                  transmission = log.OUT,
                  mode = log.PULL,
                  action = action,
                  remote = remote,
                  result = result,
                  message = message,
                  )

        debug("S3Sync: pull %s: %s" % (result, message))
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
        debug = current.log.debug

        repository = self.repository
        config = repository.config

        resource_name = task.resource_name
        debug("S3SyncRepository.push(%s, %s)" % (repository.url, resource_name))

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

        debug("...push to URL %s" % url)

        if task.components is False:
            # Allow None to remain the old default of 'Include Components'
            components = []
        else:
            # Default
            components = None

        # Define the resource
        resource = current.s3db.resource(resource_name,
                                         components = components,
                                         include_deleted = True,
                                         )

        # Apply sync filters for this task
        filters = current.sync.get_filters(task.id)

        # Export the resource as S3XML
        data = resource.export_xml(filters = filters,
                                   msince = last_push,
                                   )
        count = resource.results or 0
        mtime = resource.muntil

        # Transmit the data via HTTP
        remote = False
        output = None
        log = repository.log
        if data and count:
            # Execute the request
            opener = self._http_opener(url,
                                       headers = [("Content-Type", "text/xml"),
                                                  ],
                                       )
            try:
                opener.open(url, data)
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
            except urllib2.URLError, e:
                # URL Error (network error)
                result = log.ERROR
                remote = True
                message = "Peer repository unavailable (%s)" % e.reason
                output = xml.json_message(False, 400, message)
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
        log.write(repository_id = repository.id,
                  resource_name = task.resource_name,
                  transmission = log.OUT,
                  mode = log.PUSH,
                  action = "send",
                  remote = remote,
                  result = result,
                  message = message,
                  )

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
        output = resource.export_xml(start = start,
                                     limit = limit,
                                     filters = filters,
                                     msince = msince,
                                     pretty_print = pretty_print,
                                     )
        count = resource.results
        msg = "Data sent to peer (%s records)" % count

        # Update date/time of last incoming connection
        current.db(current.s3db.sync_repository.id == self.repository.id).update(
                    last_connected = datetime.datetime.utcnow(),
                    )

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

        # @todo: - make this the default, allow peer to URL-override?
        #        - have a repository setting to enforce strict validation?
        ignore_errors = True

        if onconflict:
            onconflict_callback = lambda item: onconflict(item,
                                                          repository,
                                                          resource,
                                                          )
        else:
            onconflict_callback = None

        output = resource.import_xml(source,
                                     format = "xml",
                                     ignore_errors = ignore_errors,
                                     strategy = strategy,
                                     update_policy = update_policy,
                                     conflict_policy = conflict_policy,
                                     last_sync = last_sync,
                                     onconflict = onconflict_callback,
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

        # Update date/time of last incoming connection
        current.db(current.s3db.sync_repository.id == self.repository.id).update(
                    last_connected = datetime.datetime.utcnow(),
                    )

        return {"status": result,
                "remote": remote,
                "message": message,
                "response": output,
                }

    # -------------------------------------------------------------------------
    def _http_opener(self, url, headers=None):
        """
            Configure a HTTP opener for sync operations

            @param url: the target URL
        """

        repository = self.repository
        config = repository.config

        # Configure opener headers
        addheaders = []
        if headers:
            addheaders.extend(headers)

        # Configure opener handlers
        handlers = []

        # Proxy handling
        proxy = repository.proxy or config.proxy or None
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
        username = repository.username
        password = repository.password
        if username and password:
            # Add a 401 handler (in case Auth header is not accepted)
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
        if username and password:
            # Send credentials unsolicitedly to force login - otherwise
            # the request would be treated as anonymous if login is not
            # required (i.e. no 401 triggered), but we want to login in
            # any case:
            import base64
            base64string = base64.encodestring('%s:%s' % (username, password))[:-1]
            addheaders.append(("Authorization", "Basic %s" % base64string))

        if addheaders:
            opener.addheaders = addheaders

        return opener

# End =========================================================================
