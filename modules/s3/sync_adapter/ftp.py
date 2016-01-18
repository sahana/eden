# -*- coding: utf-8 -*-

""" S3 Synchronization: Peer Repository Adapter for FTP

    @copyright: 2015-2016 (c) Sahana Software Foundation
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

from gluon import *

from ..s3sync import S3SyncBaseAdapter

from ..s3query import S3URLQuery, FS
from ..s3rest import S3Request
from ..s3export import S3Exporter

try:
    from cStringIO import StringIO    # Faster, where available
except:
    from StringIO import StringIO

# =============================================================================
class S3SyncAdapter(S3SyncBaseAdapter):
    """
        FTP Synchronization Adapter

         currently used by CAP
    """

    # -------------------------------------------------------------------------
    def register(self):
        """
            Register this site at the peer repository

            @return: True to indicate success, otherwise False
        """

        # No registration required
        return True

    # -------------------------------------------------------------------------
    def login(self):
        """
            Login at the peer repository

            @return: None if successful, otherwise the error
        """

        repository = self.repository
        url = repository.url
        error = None

        if not url:
            error = "Remote URL required for FTP Push"
        else:
            import ftplib
            try:
                ftp_connection = ftplib.FTP(url)
            except ftplib.all_errors:
                error = sys.exc_info()[1]
            else:
                try:
                    ftp_connection.login(repository.username, repository.password)
                except ftplib.error_perm:
                    error = sys.exc_info()[1]

            self.ftp_connection = ftp_connection

        if error:
            current.log.debug(error)
        return error

    # -------------------------------------------------------------------------
    def pull(self, task, onconflict=None):
        """
            Fetch updates from the repository and import them
            into the local database (Active Pull)

            @param task: the task (sync_task Row)
        """

        repository = self.repository

        # Log the operation
        message = "Pull from FTP currently not supported"
        log = repository.log
        log.write(repository_id = repository.id,
                  resource_name = task.resource_name,
                  transmission = log.OUT,
                  mode = log.PULL,
                  action = None,
                  remote = False,
                  result = log.FATAL,
                  message = message,
                  )

        return message, None

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
        resource_name = task.resource_name
        log = repository.log
        remote = False
        output = None

        current.log.debug("S3SyncRepository.push(%s, %s)" % (repository.url,
                                                             resource_name))

        # Define the resource
        resource = current.s3db.resource(resource_name,
                                         # FTP remote deletion is not supported yet
                                         #include_deleted=True,
                                         )

        # Apply sync filters for this task
        filters = current.sync.get_filters(task.id)
        table = resource.table
        tablename = resource.tablename

        if filters:
            queries = S3URLQuery.parse(resource, filters[tablename])
            [resource.add_filter(q) for a in queries for q in queries[a]]

        # Filter to records after last push
        msince = task.last_push

        if msince:
            strategy = task.strategy
            created = "create" in strategy
            updated = "update" in strategy
            if created and updated:
                mtime_filter = table.modified_on > msince
            elif created:
                mtime_filter = table.created_on > msince
            elif updated:
                mtime_filter = (table.created_on <= msince) & \
                               (table.modified_on > msince)
            else:
                mtime_filter = None

            if mtime_filter:
                resource.add_filter(mtime_filter)

        mtime = resource.muntil
        # Get the ID of the resource after filter and msince
        resource_ids = resource.get_id()

        # No Changes since last push?
        if resource_ids is None:
            message = "No Changes since last push"
            result = log.WARNING
        else:
            # Filename
            settings = current.deployment_settings
            # Placeholders for filename
            placeholders = {"systemname": settings.get_system_name(),
                            "systemname_short": settings.get_system_name_short(),
                            "resource": resource_name,
                            "public_url": settings.get_base_public_url(),
                            }

            from string import Template
            filename = resource.get_config("upload_filename")
            if not filename:
                filename = settings.get_sync_upload_filename()
            filename = Template(filename).safe_substitute(s="%(systemname_short)s",
                                                          r="%(resource)s")
            filename = filename % placeholders
            # Get Representation
            representation = task.representation
            filename = ("%s.%s") % (filename, representation)

            # FTP Transfer
            remote = True
            import ftplib
            ftp_connection = self.ftp_connection
            if task.multiple_file:
                if type(resource_ids) is not list:
                    resource_ids = [resource_ids]

                for resource_id in resource_ids:
                    resource.clear_query()
                    resource.add_filter(FS("id") == resource_id)
                    data = self._get_data(resource, representation)

                    try:
                        ftp_connection.storbinary("STOR %s" % filename,
                                                  StringIO(data))
                    except ftplib.error_perm:
                        message = sys.exc_info()[1]
                        result = log.ERROR
                        output = message
                    else:
                        message = "FTP Transfer Successful"
                        result = log.SUCCESS

                    current.log.debug(message)
            else:
                data = self._get_data(resource, representation)

                try:
                    ftp_connection.storbinary("STOR %s" % filename,
                                              StringIO(data))
                except ftplib.error_perm:
                    message = sys.exc_info()[1]
                    result = log.ERROR
                    output = message
                else:
                    message = "FTP Transfer Successful"
                    result = log.SUCCESS

                current.log.debug(message)

            # Quit the connection here
            ftp_connection.quit()

        # Log the operation
        log.write(repository_id = repository.id,
                  resource_name = resource_name,
                  transmission = log.OUT,
                  mode = log.PUSH,
                  action = "send",
                  remote = remote,
                  result = result,
                  message = message,
                  )
        # Returns after operation is complete
        if output is not None:
            mtime = None
        return output, mtime

    # -------------------------------------------------------------------------
    # Internal methods:
    # -------------------------------------------------------------------------
    def _get_data(self, resource, representation):
        """ Returns the representation data for the resource """

        request = S3Request(prefix = resource.prefix,
                            name = resource.name,
                            extension = representation,
                            )

        if request.transformable():
            return resource.export_xml(stylesheet = request.stylesheet(),
                                       pretty_print = True,
                                       )

        else:
            if representation == "csv":
                exporter = S3Exporter().csv

            # @ToDo use CRUD
            #elif representation == "html":

            elif representation == "pdf":
                exporter = S3Exporter().pdf

            elif representation == "xls":
                exporter = S3Exporter().xls

            elif representation == "json":
                exporter = S3Exporter().json

            return exporter(resource)

# End =========================================================================
