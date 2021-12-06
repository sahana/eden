# -*- coding: utf-8 -*-

""" S3 Synchronization: Peer Repository Adapter

    @copyright: 2014-2021 (c) Sahana Software Foundation
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

from urllib import request as urllib2
from urllib.error import HTTPError
from urllib.request import urlopen
from urllib.parse import urlencode

from gluon import *

from ..s3sync import S3SyncBaseAdapter

# =============================================================================
class S3SyncAdapter(S3SyncBaseAdapter):
    """
        Mariner CommandBridge Synchronization Adapter

        Status:
            Experimental
    """

    # -------------------------------------------------------------------------
    def register(self):
        """
            Register at the repository (does nothing in CommandBridge)

            Returns:
                True if successful, otherwise False
        """

        return True

    # -------------------------------------------------------------------------
    def login(self):
        """
            Login to the repository (does nothing in CommandBridge)

            Returns:
                None if successful, otherwise error message
        """

        return None

    # -------------------------------------------------------------------------
    def pull(self, task, onconflict=None):
        """
            Pull updates from this repository

            Args:
                task: the task Row
                onconflict: synchronization conflict resolver

            Returns:
                tuple (error, mtime), with error=None if successful,
                     else error=message, and mtime=modification timestamp
                     of the youngest record received
        """

        error = "CommandBridge API pull not implemented"
        current.log.error(error)
        return (error, None)

    # -------------------------------------------------------------------------
    def push(self, task):
        """
            Push data for a task

            Args:
                task: the task Row

            Returns:
                tuple (error, mtime), with error=None if successful,
                     else error=message, and mtime=modification timestamp
                     of the youngest record sent
        """

        repository = self.repository

        resource_name = task.resource_name
        current.log.debug("S3SyncCommandBridge.push(%s, %s)" %
                          (repository.url, resource_name))

        # Define the resource
        resource = current.s3db.resource(resource_name,
                                         include_deleted=True)

        # Export stylesheet
        folder = current.request.folder
        import os
        stylesheet = os.path.join(folder,
                                  "static",
                                  "formats",
                                  "mcb",
                                  "export.xsl")

        # Last push
        last_push = task.last_push

        # Apply sync filters for this task
        filters = current.sync.get_filters(task.id)

        settings = current.deployment_settings

        identifiers = settings.get_sync_mcb_resource_identifiers()
        resources = "".join("[%s:%s]" % (k, v) for k, v in identifiers.items())

        identifiers = settings.get_sync_mcb_domain_identifiers()
        domains = "".join("[%s:%s]" % (k, v) for k, v in identifiers.items())

        # Export the resource as S3XML
        data = resource.export_xml(filters = filters,
                                   msince = last_push,
                                   stylesheet = stylesheet,
                                   pretty_print = True,
                                   resources = resources,
                                   domains = domains,
                                   )

        count = resource.results or 0
        mtime = resource.muntil

        # Transmit the data via HTTP
        remote = False
        output = None
        log = repository.log
        if data and count:
            response, message = self._send_request(method = "POST",
                                                   path = "BulkStream",
                                                   data = data,
                                                   )
            if response is None:
                result = log.FATAL
                remote = True
                if not message:
                    message = "unknown error"
                output = message
            else:
                result = log.SUCCESS
                message = "Data sent successfully (%s records)" % count
        else:
            # No data to send
            result = log.WARNING
            message = "No data to send"

        # Log the operation
        log.write(repository_id = repository.id,
                  resource_name = resource_name,
                  transmission = log.OUT,
                  mode = log.PUSH,
                  action = "send",
                  remote = remote,
                  result = result,
                  message = message)

        if output is not None:
            mtime = None
        return (output, mtime)

    # -------------------------------------------------------------------------
    # Internal methods:
    # -------------------------------------------------------------------------
    def _send_request(self,
                      method = "GET",
                      path = None,
                      args = None,
                      data = None,
                      auth = False,
                      ):
        """
            Send a request to the CommandBridge API

            Args:
                method: the HTTP method
                path: the path relative to the repository URL
                data: the data to send
                auth: this is an authorization request
        """

        xml = current.xml
        repository = self.repository

        # Request URL
        url = repository.url.rstrip("/")
        if path:
            url = "/".join((url, path.lstrip("/")))
        if args:
            url = "?".join((url, urlencode(args)))

        # Create the request
        req = urllib2.Request(url=url)
        handlers = []

        site_key = repository.site_key
        if not site_key:
            message = "CommandBridge Authorization failed: no access token (site key)"
            current.log.error(message)
            return None, message
        req.add_header("Authorization-Token", "%s" % site_key)

        # Request Data
        request_data = data if data is not None else ""
        if request_data:
            req.add_header("Content-Type", "application/xml")

        # Indicate that we expect XML response
        req.add_header("Accept", "application/xml")

        # Proxy handling
        config = repository.config
        proxy = repository.proxy or config.proxy or None
        if proxy:
            current.log.debug("using proxy=%s" % proxy)
            proxy_handler = urllib2.ProxyHandler({"https": proxy})
            handlers.append(proxy_handler)

        # Install all handlers
        if handlers:
            opener = urllib2.build_opener(*handlers)
            urllib2.install_opener(opener)

        # Execute the request
        response = None
        message = None
        try:
            if method == "POST":
                f = urlopen(req, data=request_data)
            else:
                f = urlopen(req)
        except HTTPError as e:
            message = "HTTP %s: %s" % (e.code, e.reason)
            # More details may be in the response body
            error_response = xml.parse(e)
            if error_response:
                error_messages = error_response.findall("Message")
                details = " / ".join(item.text for item in error_messages)
                message = "%s (%s)" % (message, details)
        else:
            response = xml.parse(f)
            if response is None:
                if method == "POST":
                    response = True
                elif xml.error:
                    message = xml.error

        return response, message

# End =========================================================================
