# -*- coding: utf-8 -*-

""" S3 Synchronization: Peer Repository Adapter for FTP

    @copyright: 2015 (c) Sahana Software Foundation
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
import os

from gluon import *

from ..s3sync import S3SyncBaseAdapter

from ..s3query import S3URLQuery, S3FieldSelector as FS
from ..s3rest import S3Request
from ..s3export import S3Exporter

try:
    from cStringIO import StringIO    # Faster, where available
except:
    from StringIO import StringIO

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
        
        # Need FTP object so login done at push
        return None
    
    # -------------------------------------------------------------------------
    def pull(self, task, onconflict=None):
        """
            Fetch updates from the repository and import them
            into the local database (Active Pull)

            @param task: the task (sync_task Row)
        """

        repository = self.repository

        # Log the operation
        log = repository.log
        log.write(repository_id = repository.id,
                  resource_name = task.resource_name,
                  transmission = log.OUT,
                  mode = log.PUSH,
                  action = None,
                  remote = False,
                  result = log.FATAL,
                  message = "Pull from FTP currently not supported",
                  )

        output = current.xml.json_message(False, 400, message)
        return(output, None)

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
        url = repository.url
        log = repository.log
        remote = False
        output = None
        
        if not url:
            message = "Remote URL required for FTP Push"
            log.write(repository_id = repository.id,
                      resource_name = resource_name,
                      transmission = log.OUT,
                      mode = log.PUSH,
                      action = "send",
                      remote = remote,
                      result = log.ERROR,
                      message = message,
                      )
            output = current.xml.json_message(False, 400, message)
        else:
            _debug("S3SyncRepository.push(%s, %s)" % (url, resource_name))
            # Define the resource
            resource = current.s3db.resource(resource_name,
                                             include_deleted=True)
            
            # Apply sync filters for this task
            filters = current.sync.get_filters(task.id)
            table = resource.table
            tablename = resource.tablename
            
            if filters and tablename in filters:
                queries = S3URLQuery.parse(resource, filters[tablename])
                [resource.add_filter(q) for a in queries for q in queries[a]]
    
            # Filter to records after last push
            msince = task.last_push            
            if msince is not None and "modified_on" in table.fields:
                resource.add_filter(table.modified_on > msince)
                
            # Get the ID of the resource after filter and msince
            resource_ids = resource.get_id()
            
            # No Changes since last push?
            if resource_ids is None:
                log.write(repository_id = repository.id,
                          resource_name = resource_name,
                          transmission = log.OUT,
                          mode = log.PUSH,
                          action = "send",
                          remote = remote,
                          result = log.WARNING,
                          message = "No Changes since last push",
                          )
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
                
                # Get Login Info
                username = repository.username
                password = repository.password
                
                # For log operation                
                if task.multiple_file:
                    if type(resource_ids) is not list:
                        resource_ids = [resource_ids]                    
                      
                    for resource_id in resource_ids:
                        resource.clear_query()
                        resource.add_filter(~(FS("id") == resource_id))
                        
                        data = self._get_data(resource, representation)
                        # FTP Transfer
                        import ftplib
                        remote = True                        
                        try:
                            remote_ftp_connection = ftplib.FTP(url)
                        except ftplib.all_errors as e:
                            message = str(e)
                            result = log.ERROR
                            output = current.xml.json_message(False, 400, message) 
                        else:
                            try:
                                remote_ftp_connection.login(username, password)
                            except ftplib.error_perm as e:
                                message = str(e)
                                result = log.ERROR
                                output = current.xml.json_message(False, 400, message)
                            else:
                                try:                    
                                    remote_ftp_connection.storbinary("STOR %s" % filename,
                                                                     StringIO(data))
                                except ftplib.error_perm as e:
                                    message = str(e)
                                    result = log.ERROR
                                    output = current.xml.json_message(False, 400, message)
                                else:
                                    remote_ftp_connection.quit()
                                    message = "data sent successfully"
                                    result = log.SUCCESS
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
                else:
                    data = self._get_data(resource, representation)
                    
                    # FTP Transfer
                    import ftplib
                    remote = True  
                    try:
                        remote_ftp_connection = ftplib.FTP(url)
                    except ftplib.all_errors as e:
                        message = str(e)
                        result = log.ERROR
                        output = current.xml.json_message(False, 400, message)
                    else:
                        try:
                            remote_ftp_connection.login(username, password)
                        except ftplib.error_perm as e:
                            message = str(e)
                            result = log.ERROR
                            output = current.xml.json_message(False, 400, message)
                        else:
                            try:                    
                                remote_ftp_connection.storbinary("STOR %s" % filename,
                                                                 StringIO(data))
                            except ftplib.error_perm as e:
                                message = str(e)
                                result = log.ERROR
                                output = current.xml.json_message(False, 400, message)
                            else:
                                remote_ftp_connection.quit()
                                message = "data sent successfully"
                                remote = True
                                result = log.SUCCESS
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
            resource.muntil = None
        return(output, resource.muntil)
    
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
            if representation == "html":
                # @ToDo Implement this
                return
            
            elif representation == "csv":
                exporter = S3Exporter().csv
                                
            elif representation == "pdf":
                exporter = S3Exporter().pdf
                                                            
            elif representation == "xls":
                exporter = S3Exporter().xls
                                
            elif representation == "json":
                exporter = S3Exporter().json
            
            return exporter(resource)
    
# End =========================================================================
