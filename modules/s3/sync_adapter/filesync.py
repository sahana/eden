# -*- coding: utf-8 -*-

""" S3 Synchronization: Peer Repository Adapter

    @copyright: 2011-15 (c) Sahana Software Foundation
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
import glob
import os
import sys

try:
    from lxml import etree
except ImportError:
    print >> sys.stderr, "ERROR: lxml module needed for XML handling"
    raise

from gluon import *

from ..s3sync import S3SyncBaseAdapter

# =============================================================================
class S3SyncAdapter(S3SyncBaseAdapter):
    """
        File Synchronization Adapter
    """

    def register(self):
        """
            Register this site at the peer repository

            @return: True to indicate success, otherwise False
        """

        # No registration needed
        return True

    # -------------------------------------------------------------------------
    def login(self):
        """
            Login at the peer repository

            @return: None if successful, otherwise the error
        """

        # No explicit login required
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
        log = repository.log

        error = None
        result = None

        # Instantiate the target resource
        tablename = task.resource_name
        if tablename == "mixed":
            resource = None
            mixed = True
        else:
            try:
                resource = current.s3db.resource(tablename)
            except SyntaxError:
                result = log.FATAL
                error = msg = sys.exc_info()[1]
            mixed = False

        # Get input files
        if not result:
            input_files = self._input_files(task)
            if not input_files:
                result = log.SUCCESS
                msg = "No files to import"

        # Instantiate back-end
        if not result:
            adapter = None
            backend = repository.backend
            if not backend:
                backend = "eden"
            backend = "s3.sync_adapter.%s" % backend
            try:
                name = "S3SyncAdapter"
                api = getattr(__import__(backend, fromlist=[name]), name)
            except ImportError:
                result = log.FATAL
                error = msg = "Unsupported back-end: %s" % backend
            else:
                adapter = api(repository)

        # If any of the previous actions has produced a non-default result:
        if result:
            # Log the operation and return
            log.write(repository_id = repository.id,
                      resource_name = tablename,
                      transmission = log.OUT,
                      mode = log.PULL,
                      action = None,
                      remote = False,
                      result = result,
                      message = msg,
                      )
            return (error, None)

        # Set strategy and policies
        from ..s3import import S3ImportItem
        strategy = task.strategy
        update_policy = task.update_policy
        if not update_policy:
            update_policy = S3ImportItem.POLICY.NEWER
        conflict_policy = task.conflict_policy
        if not conflict_policy:
            conflict_policy = S3ImportItem.POLICY.MASTER
        if update_policy not in ("THIS", "OTHER"):
            last_sync = task.last_pull

        # Import the files
        error = None
        mtime = current.request.utcnow

        for f in input_files:
            current.log.debug("FileSync: importing %s" % f)
            try:
                with open(f, "r") as source:
                    result = adapter.receive([source],
                                             resource,
                                             strategy = strategy,
                                             update_policy = update_policy,
                                             conflict_policy = conflict_policy,
                                             onconflict = onconflict,
                                             last_sync = last_sync,
                                             mixed = mixed,
                                             )
            except IOError:
                msg = sys.exc_info()[1]
                current.log.warning(msg)
                continue

            status = result["status"]

            # Log the operation
            log.write(repository_id = repository.id,
                      resource_name = tablename,
                      transmission = log.OUT,
                      mode = log.PULL,
                      action = "import %s" % f,
                      remote = result["remote"],
                      result = status,
                      message = result["message"],
                      )

            if status in (log.ERROR, log.FATAL):
                error = "Error while importing %s" % f
                current.log.error(error)
                mtime = None

            elif task.delete_input_files:
                try:
                    os.remove(f)
                except os.error:
                    current.log.warning("FileSync: can not delete %s" % f)
                else:
                    current.log.debug("FileSync: %s deleted" % f)

        return error, mtime

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

        repository = self.repository

        # Log the operation
        msg = "Push not supported for this repository type"
        log = repository.log
        log.write(repository_id = repository.id,
                  resource_name = task.resource_name,
                  transmission = log.OUT,
                  mode = log.PULL,
                  action = None,
                  remote = False,
                  result = log.FATAL,
                  message = msg,
                  )

        return (msg, None)

    # -------------------------------------------------------------------------
    def send(self,
             resource,
             start=None,
             limit=None,
             msince=None,
             filters=None,
             mixed=False):
        """
            Respond to an incoming pull from the peer repository

            @param resource: the resource to be synchronized
            @param start: index of the first record to send
            @param limit: maximum number of records to send
            @param msince: minimum modification date/time for records to send
            @param filters: URL filters for record extraction
            @param mixed: negotiate resource with peer (disregard resource)

            @return: a dict {status, remote, message, response}, with:
                        - status....the outcome of the operation
                        - remote....whether the error was remote (or local)
                        - message...the log message
                        - response..the response to send to the peer
        """

        msg = "Send not supported for this repository type"

        return {"status": self.log.FATAL,
                "remote": False,
                "message": msg,
                "response": None,
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

        msg = "Receive not supported for this repository type"

        return {"status": self.log.FATAL,
                "remote": False,
                "message": msg,
                "response": None,
                }

    # -------------------------------------------------------------------------
    def _input_files(self, task):
        """
            Helper function to get all relevant input files from the
            repository path, excluding files which have not been modified
            since the last pull of the task

            @param task: the synchronization task
            @return: a list of file paths, ordered by their time
                     stamp (oldest first)
        """

        repository = self.repository

        path = repository.path
        infile_pattern = task.infile_pattern

        if path and infile_pattern:
            pattern = os.path.join(path, infile_pattern)
        else:
            return []

        all_files = glob.glob(pattern)

        infiles = []
        append = infiles.append
        msince = task.last_pull
        for f in filter(os.path.isfile, all_files):
            mtime = datetime.datetime.utcfromtimestamp(os.path.getmtime(f))
            # Disregard files which have not been modified since the last pull
            if msince and mtime <= msince:
                continue
            append((mtime, f))

        # Sort by mtime
        infiles.sort(key=lambda item: item[0])

        return [item[1] for item in infiles]

# End =========================================================================
