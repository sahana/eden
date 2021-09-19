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

import json
import sys

try:
    from lxml import etree
except ImportError:
    sys.stderr.write("ERROR: lxml module needed for XML handling\n")
    raise
from urllib import parse as urlparse
from urllib import request as urllib2
from urllib.error import HTTPError
from urllib.request import urlopen
from urllib.parse import urlencode

from gluon import *

from ..s3datetime import s3_encode_iso_datetime
from ..s3sync import S3SyncBaseAdapter
from ..s3utils import s3_unicode

# =============================================================================
class S3SyncAdapter(S3SyncBaseAdapter):
    """
        Wrike® Synchronization Adapter

        http://www.wrike.com/wiki/dev/api3
    """

    # -------------------------------------------------------------------------
    def __init__(self, repository):
        """
            Constructor
        """

        super(S3SyncAdapter, self).__init__(repository)

        self.access_token = None
        self.token_type = None

    # -------------------------------------------------------------------------
    # Methods to be implemented by subclasses:
    # -------------------------------------------------------------------------
    def register(self):
        """
            Register at the repository, in Wrike: use client ID and the
            authorization code (site key), alternatively username and
            password to obtain the refresh_token and store it in the
            repository config.

            @note: this invalidates the authorization code (if any), so it
                   will be set to None regardless whether this operation
                   succeeds or not

            @return: True if successful, otherwise False
        """

        repository = self.repository

        log = repository.log
        success = False
        remote = False
        skip = False

        data = None
        site_key = repository.site_key
        if not site_key:
            username = repository.username
            password = repository.password
            if username and password:
                data = {
                    "client_id": repository.client_id,
                    "client_secret": repository.client_secret,
                    "username": username,
                    "password": password,
                    "grant_type": "password",
                }
        else:
            data = {
                "client_id": repository.client_id,
                "client_secret": repository.client_secret,
                "grant_type": "authorization_code",
                "code": site_key,
            }

        if not data:
            if not repository.refresh_token:
                # Can't register without credentials
                result = log.WARNING
                message = "No credentials to obtain refresh token " \
                          "with, skipping registration"
            else:
                # Already registered
                result = log.SUCCESS
                success = True
                message = None
            skip = True

        else:
            repository.refresh_token = None
            self.access_token = None

            # Get refresh token from peer
            response, message = self._send_request(method = "POST",
                                                   data = data,
                                                   auth = True,
                                                   )
            if not response:
                result = log.FATAL
                remote = True
            else:
                refresh_token = response.get("refresh_token")
                if not refresh_token:
                    result = log.FATAL
                    message = "No refresh token received"
                else:
                    repository.refresh_token = refresh_token
                    self.access_token = response.get("access_token")
                    result = log.SUCCESS
                    success = True
                    message = "Registration successful"
            self.update_refresh_token()

        # Log the operation
        log.write(repository_id=repository.id,
                  transmission=log.OUT,
                  mode=log.PUSH,
                  action="request refresh token",
                  remote=remote,
                  result=result,
                  message=message)

        if not success:
            current.log.error(message)
        return success if not skip else True

    # -------------------------------------------------------------------------
    def login(self):
        """
            Login to the repository, in Wrike: use the client ID (username),
            the client secret (password) and the refresh token to obtain the
            access token for subsequent requests.

            @return: None if successful, otherwise error message
        """

        repository = self.repository

        log = repository.log
        error = None
        remote = False

        refresh_token = repository.refresh_token
        if not refresh_token:
            result = log.FATAL
            error = "Login failed: no refresh token available (registration failed?)"
        else:
            data = {
                "client_id": repository.client_id,
                "client_secret": repository.client_secret,
                "grant_type": "refresh_token",
                "refresh_token": refresh_token
            }
            response, message = self._send_request(method = "POST",
                                                   data = data,
                                                   auth = True,
                                                   )
            if not response:
                result = log.FATAL
                remote = True
                error = message
            else:
                access_token = response.get("access_token")
                if not access_token:
                    result = log.FATAL
                    error = "No access token received"
                else:
                    result = log.SUCCESS
                    self.access_token = access_token
                    self.token_type = response.get("token_type", "bearer")


        # Log the operation
        log.write(repository_id=repository.id,
                  transmission=log.OUT,
                  mode=log.PUSH,
                  action="request access token",
                  remote=remote,
                  result=result,
                  message=error)

        if error:
            current.log.error(error)
        return error

    # -------------------------------------------------------------------------
    def pull(self, task, onconflict=None):
        """
            Pull updates from this repository

            @param task: the task Row
            @param onconflict: synchronization conflict resolver
            @return: tuple (error, mtime), with error=None if successful,
                     else error=message, and mtime=modification timestamp
                     of the youngest record received
        """

        repository = self.repository

        resource_name = task.resource_name

        current.log.debug("S3SyncWrike.pull(%s, %s)" %
                          (repository.url, resource_name))

        xml = current.xml
        log = repository.log

        # Last pull time
        last_pull = task.last_pull
        if last_pull and task.update_policy not in ("THIS", "OTHER"):
            msince = s3_encode_iso_datetime(last_pull)
        else:
            msince = None

        # Create the root node of the data tree
        root = etree.Element("wrike-data")

        # Fetch accounts and add them to the tree
        accounts, error = self.fetch_accounts(root)
        if accounts is not None:

            error = None

            def log_fetch_error(action, account_name, message):
                """ Helper to log non-fatal errors during fetch """
                action = "%s for account '%s'" % (action, account_name)
                log.write(repository_id = repository.id,
                          resource_name = resource_name,
                          transmission = log.OUT,
                          mode = log.PULL,
                          action = action,
                          remote = True,
                          result = log.ERROR,
                          message = message)
                return

            for account_id, account_data in accounts.items():

                account_name, root_folder_id, recycle_bin_id = account_data

                # Fetch folders
                response, message = self.fetch_folders(root, account_id)
                if response is None:
                    log_fetch_error("fetch folders",
                                    account_name,
                                    message)
                    continue

                # Fetch active tasks
                response, message = self.fetch_tasks(root,
                                                     root_folder_id,
                                                     msince=msince)
                if response is None:
                    log_fetch_error("fetch active tasks",
                                    account_name,
                                    message)

                # Fetch deleted tasks
                response, message = self.fetch_tasks(root,
                                                     recycle_bin_id,
                                                     msince=msince,
                                                     deleted = True)
                if response is None:
                    log_fetch_error("fetch deleted tasks",
                                    account_name,
                                    message)

        if error:
            # Error during fetch_accounts (fatal)
            result = log.FATAL
            remote = True
            message = error
            output = xml.json_message(False, 400, error)

        elif len(root):
            result = log.SUCCESS
            remote = False
            message = None
            output = None

            # Convert into ElementTree
            tree = etree.ElementTree(root)

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
                                      "wrike",
                                      "import.xsl")

            # Host name of the peer, used by the import stylesheet
            hostname = urlparse.urlsplit(repository.url).hostname

            # Conflict resolution callback
            resource = current.s3db.resource(resource_name)
            if onconflict:
                onconflict_callback = lambda item: onconflict(item,
                                                              repository,
                                                              resource)
            else:
                onconflict_callback = None

            # Import the data
            count = 0
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
            except IOError:
                success = False
                result = log.FATAL
                message = sys.exc_info()[1]
                output = xml.json_message(False, 400, message)

            mtime = resource.mtime

            # Log all validation errors (@todo: doesn't work)
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
            result = log.WARNING
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

        current.log.debug("S3SyncWrike.pull import %s: %s" % (result, message))

        return (output, mtime)

    # -------------------------------------------------------------------------
    def push(self, task):
        """
            Push data for a task

            @param task: the task Row
            @return: tuple (error, mtime), with error=None if successful,
                     else error=message, and mtime=modification timestamp
                     of the youngest record sent
        """

        error = "Wrike API push not implemented"
        current.log.error(error)
        return (error, None)

    # -------------------------------------------------------------------------
    # Internal methods:
    # -------------------------------------------------------------------------
    def fetch_accounts(self, root):
        """
            Get all accessible accounts

            @return: dict {account_id: (rootFolderId, recycleBinId)}
        """

        response, message = self._send_request(path="accounts")
        if not response:
            return None, message

        accounts = {}
        data = response.get("data")
        if data and type(data) is list:
            SubElement = etree.SubElement
            for account_data in data:
                account_id = account_data.get("id")
                account = SubElement(root, "account",
                                     id = str(account_id))
                account_name = account_data.get("name")
                name = SubElement(account, "name")
                name.text = account_name

                accounts[account_id] = (account_name,
                                        account_data.get("rootFolderId"),
                                        account_data.get("recycleBinId"))
        return accounts, None

    # -------------------------------------------------------------------------
    def fetch_folders(self, root, account_id):
        """
            Fetch folders from a Wrike account and add them to the
            data tree

            @param root: the root element of the data tree
            @param account_id: the Wrike account ID
        """

        response, message = self._send_request(path="accounts/%s/folders" % account_id)
        if not response:
            return None, message

        folders = {}
        data = response.get("data")
        if data and type(data) is list:
            SubElement = etree.SubElement
            for folder_data in data:
                scope = folder_data.get("scope")
                if scope not in ("WsFolder", "RbFolder"):
                    continue
                folder_id = folder_data.get("id")
                folder = SubElement(root, "folder",
                                    id = str(folder_id))
                folders[folder_id] = folder
                if scope == "RbFolder":
                    folder.set("deleted", str(True))
                else:
                    title = SubElement(folder, "title")
                    title.text = folder_data.get("title")
                    account = SubElement(folder, "accountId")
                    account.text = str(account_id)

        return folders, None

    # -------------------------------------------------------------------------
    def fetch_tasks(self, root, folder_id, deleted=False, msince=None):
        """
            Fetch all tasks in a folder

            @param root: the root element of the data tree
            @param folder_id: the ID of the folder to read from
            @param deleted: mark the tasks as deleted in the data
                            tree (when reading tasks from a recycle bin)
            @param msince: only retrieve tasks that have been modified
                           after this date/time (ISO-formatted string)
        """

        args = {"descendants": "true",
                "fields": json.dumps(["parentIds",
                                      "description",
                                      ]
                                     ),
                }
        if msince is not None:
            args["updatedDate"] = "%sZ," % msince
        response, message = self._send_request(path = "folders/%s/tasks" % folder_id,
                                               args = args,
                                               )
        if not response:
            return None, message

        details = {"title": "title",
                   "description": "description",
                   "status": "status",
                   "importance": "importance",
                   "permalink": "permalink",
                   "createdDate": "createdDate",
                   "updatedDate": "updatedDate",
                   "dates": {"due": "dueDate",
                             }
                   }

        tasks = {}
        data = response.get("data")
        if data and type(data) is list:
            SubElement = etree.SubElement
            for task_data in data:
                scope = task_data.get("scope")
                if scope not in ("WsTask", "RbTask"):
                    continue
                task_id = task_data.get("id")
                task = SubElement(root, "task", id = str(task_id))
                tasks[task_id] = task
                deleted = scope == "RbTask"
                if deleted:
                    task.set("deleted", str(True))
                    continue
                parent_ids = task_data.get("parentIds")
                if parent_ids:
                    for parent_id in parent_ids:
                        parent = SubElement(task, "parentId")
                        parent.text = str(parent_id)
                self.add_details(task, task_data, details)

        return tasks, None

    # -------------------------------------------------------------------------
    @classmethod
    def add_details(cls, task, data, keys):
        """
            Recursively convert the nested task details dicts into SubElements

            @param task: the task Element
            @param data: the nested dict
            @param keys: the mapping of dict keys to SubElement names
        """

        if not isinstance(data, dict):
            return
        SubElement = etree.SubElement
        for key, name in keys.items():
            wrapper = data.get(key)
            if wrapper is None:
                continue
            if isinstance(name, dict):
                cls.add_details(task, wrapper, name)
            else:
                detail = SubElement(task, name)
                detail.text = s3_unicode(wrapper)
        return

    # -------------------------------------------------------------------------
    def update_refresh_token(self):
        """
            Store the current refresh token in the db, also invalidated
            the site_key (authorization code) because it can not be used
            again.
        """

        repository = self.repository
        repository.site_key = None

        table = current.s3db.sync_repository
        current.db(table.id == repository.id).update(
            refresh_token = repository.refresh_token,
            site_key = repository.site_key
        )
        return

    # -------------------------------------------------------------------------
    def _send_request(self,
                      method="GET",
                      path=None,
                      args=None,
                      data=None,
                      auth=False):
        """
            Send a request to the Wrike API

            @param method: the HTTP method
            @param path: the path relative to the repository URL
            @param data: the data to send
            @param auth: this is an authorization request
        """

        repository = self.repository

        # Request URL
        api = "oauth2/token" if auth else "api/v3"
        url = "/".join((repository.url.rstrip("/"), api))
        if path:
            url = "/".join((url, path.lstrip("/")))
        if args:
            url = "?".join((url, urlencode(args)))

        # Create the request
        req = urllib2.Request(url=url)
        handlers = []

        if not auth:
            # Install access token header
            access_token = self.access_token
            if not access_token:
                message = "Authorization failed: no access token"
                current.log.error(message)
                return None, message
            req.add_header("Authorization", "%s %s" %
                                            (self.token_type, access_token))
            # JSONify request data
            request_data = json.dumps(data) if data else ""
            if request_data:
                req.add_header("Content-Type", "application/json")
        else:
            # URL-encode request data for auth
            request_data = urlencode(data) if data else ""

        # Indicate that we expect JSON response
        req.add_header("Accept", "application/json")

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
        else:
            # Parse the response
            try:
                response = json.load(f)
            except ValueError as e:
                message = sys.exc_info()[1]

        return response, message

# End =========================================================================
