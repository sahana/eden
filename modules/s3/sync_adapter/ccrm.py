# -*- coding: utf-8 -*-

""" S3 Synchronization: Peer Repository Adapter

    @copyright: 2012-2019 (c) Sahana Software Foundation
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

from gluon import *
from gluon.storage import Storage

from ..s3sync import S3SyncBaseAdapter

# =============================================================================
class S3SyncAdapter(S3SyncBaseAdapter):
    """
        CiviCRM Synchronization Adapter

        @status: experimental
    """

    # Resource map
    RESOURCE = {
        "pr_person": {
                      "q": "civicrm/contact",
                      "contact_type": "Individual"
                     },
    }

    # -------------------------------------------------------------------------
    # Methods to be implemented by subclasses:
    # -------------------------------------------------------------------------
    def register(self):
        """
            Register this site at the peer repository

            @return: True to indicate success, otherwise False
        """

        # CiviCRM does not support via-web peer registration
        return True

    # -------------------------------------------------------------------------
    def login(self):
        """
            Login at the peer repository

            @return: None if successful, otherwise the error
        """

        _debug = current.log.debug

        _debug("S3SyncCiviCRM.login()")

        repository = self.repository

        request = {
            "q": "civicrm/login",
            "name": repository.username,
            "pass": repository.password,
        }
        response, error = self._send_request(**request)

        if error:
            _debug("S3SyncCiviCRM.login FAILURE: %s" % error)
            return error

        api_key = response.findall("//api_key")
        if len(api_key):
            self.api_key = api_key[0].text
        else:
            error = "No API Key returned by CiviCRM"
            _debug("S3SyncCiviCRM.login FAILURE: %s" % error)
            return error
        PHPSESSID = response.findall("//PHPSESSID")
        if len(PHPSESSID):
            self.PHPSESSID = PHPSESSID[0].text
        else:
            error = "No PHPSESSID returned by CiviCRM"
            _debug("S3SyncCiviCRM.login FAILURE: %s" % error)
            return error

        _debug("S3SyncCiviCRM.login SUCCESS")
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
        _debug = current.log.debug
        repository = self.repository
        log = repository.log
        resource_name = task.resource_name

        _debug("S3SyncCiviCRM.pull(%s, %s)" % (repository.url, resource_name))

        mtime = None
        message = ""
        remote = False

        # Construct the request
        if resource_name not in self.RESOURCE:
            result = log.FATAL
            message = "Resource type %s currently not supported for CiviCRM synchronization" % \
                      resource_name
            output = xml.json_message(False, 400, message)
        else:
            args = Storage(self.RESOURCE[resource_name])
            args["q"] += "/get"

            tree, error = self._send_request(method="GET", **args)
            if error:

                result = log.FATAL
                remote = True
                message = error
                output = xml.json_message(False, 400, error)

            elif len(tree.getroot()):

                result = log.SUCCESS
                remote = False

                # Get import strategy and update policy
                strategy = task.strategy
                update_policy = task.update_policy
                conflict_policy = task.conflict_policy

                # Import stylesheet
                folder = current.request.folder
                import os
                stylesheet = os.path.join(folder,
                                          "static",
                                          "formats",
                                          "ccrm",
                                          "import.xsl")

                # Host name of the peer,
                # used by the import stylesheet
                import urlparse
                hostname = urlparse.urlsplit(repository.url).hostname

                # Import the data
                resource = current.s3db.resource(resource_name)
                if onconflict:
                    onconflict_callback = lambda item: onconflict(item,
                                                                  repository,
                                                                  resource)
                else:
                    onconflict_callback = None
                count = 0
                success = True
                try:
                    success = resource.import_xml(tree,
                                               stylesheet=stylesheet,
                                               ignore_errors=True,
                                               strategy=strategy,
                                               update_policy=update_policy,
                                               conflict_policy=conflict_policy,
                                               last_sync=task.last_pull,
                                               onconflict=onconflict_callback,
                                               site=hostname)
                    count = resource.import_count
                except IOError as e:
                    result = log.FATAL
                    message = "%s" % e
                    output = xml.json_message(False, 400, message)
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
                    output = None

            else:
                # No data received from peer
                result = log.ERROR
                remote = True
                message = "No data received from peer"
                output = None

        # Log the operation
        log.write(repository_id=repository.id,
                  resource_name=resource_name,
                  transmission=log.OUT,
                  mode=log.PULL,
                  action=None,
                  remote=remote,
                  result=result,
                  message=message)

        _debug("S3SyncCiviCRM.pull import %s: %s" % (result, message))
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
        _debug = current.log.debug
        repository = self.repository

        log = repository.log
        resource_name = task.resource_name

        _debug("S3SyncCiviCRM.push(%s, %s)" % (repository.url, resource_name))

        result = log.FATAL
        remote = False
        message = "Push to CiviCRM currently not supported"
        output = xml.json_message(False, 400, message)

        # Log the operation
        log.write(repository_id=repository.id,
                  resource_name=resource_name,
                  transmission=log.OUT,
                  mode=log.PUSH,
                  action=None,
                  remote=remote,
                  result=result,
                  message=message)

        _debug("S3SyncCiviCRM.push export %s: %s" % (result, message))
        return(output, None)

    # -------------------------------------------------------------------------
    # Internal methods:
    # -------------------------------------------------------------------------
    def _send_request(self, method="GET", **args):

        repository = self.repository
        config = repository.config

        # Authentication
        args = Storage(args)
        if hasattr(self, "PHPSESSID") and self.PHPSESSID:
            args["PHPSESSID"] = self.PHPSESSID
        if hasattr(self, "api_key") and self.api_key:
            args["api_key"] = self.api_key
        if repository.site_key:
            args["key"] = repository.site_key

        # Create the request
        url = repository.url + "?" + urllib.urlencode(args)
        req = urllib2.Request(url=url)
        handlers = []

        # Proxy handling
        proxy = repository.proxy or config.proxy or None
        if proxy:
            current.log.debug("using proxy=%s", proxy)
            proxy_handler = urllib2.ProxyHandler({protocol: proxy})
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
                f = urllib2.urlopen(req, data="")
            else:
                f = urllib2.urlopen(req)
        except urllib2.HTTPError as e:
            message = "HTTP %s: %s" % (e.code, e.reason)
        else:
            # Parse the response
            tree = current.xml.parse(f)
            root = tree.getroot()
            is_error = root.xpath("//ResultSet[1]/Result[1]/is_error")
            if len(is_error) and int(is_error[0].text):
                error = root.xpath("//ResultSet[1]/Result[1]/error_message")
                if len(error):
                    message = error[0].text
                else:
                    message = "Unknown error"
            else:
                response = tree

        return response, message

# End =========================================================================
