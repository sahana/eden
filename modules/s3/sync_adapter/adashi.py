# -*- coding: utf-8 -*-

""" S3 Synchronization: Peer Repository Adapter for ADASHI

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

import os
import sys

from gluon import *

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
        ADASHI Synchronization Adapter (passive)

        http://www.adashisystems.com
    """

    # -------------------------------------------------------------------------
    def register(self):
        """
            Register this site at the peer repository

            @return: True to indicate success, otherwise False
        """

        # No registration required (passive adapter)
        return True

    # -------------------------------------------------------------------------
    def login(self):
        """
            Login at the peer repository

            @return: None if successful, otherwise the error
        """

        # No login required (passive adapter)
        return None

    # -------------------------------------------------------------------------
    def pull(self, task, onconflict=None):
        """
            Outgoing pull

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
                  message = "Pull from ADASHI currently not supported",
                  )

        output = current.xml.json_message(False, 400, message)
        return(output, None)

    # -------------------------------------------------------------------------
    def push(self, task):
        """
            Outgoing push

            @param task: the sync_task Row
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
                  message = "Push to ADASHI currently not supported",
                  )

        output = current.xml.json_message(False, 400, message)
        return(output, None)

    # -------------------------------------------------------------------------
    def send(self,
             resource,
             start=None,
             limit=None,
             msince=None,
             filters=None,
             mixed=False):
        """
            Respond to an incoming pull from a peer repository

            @param resource: the resource to be synchronized
            @param start: index of the first record to send
            @param limit: maximum number of records to send
            @param msince: minimum modification date/time for records to send
            @param filters: URL filters for record extraction
            @param mixed: negotiate resource with peer (disregard resource)
        """

        if not resource or mixed:
            msg = "Mixed resource synchronization not supported"
            return {"status": self.log.FATAL,
                    "message": msg,
                    "response": current.xml.json_message(False, 400, msg),
                    }

        # Export the data as S3XML
        stylesheet = os.path.join(current.request.folder,
                                  "static", "formats", "georss", "export.xsl")
        output = resource.export_xml(start=start,
                                     limit=limit,
                                     filters=filters,
                                     msince=msince,
                                     stylesheet=stylesheet,
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
        """

        s3db = current.s3db

        xml = current.xml
        log = self.log
        remote = False

        # Sync always has only one source per request
        source = source[0]

        # Parse the feed
        tree = xml.parse(source)
        if not tree:
            # Parser error
            msg = xml.error if xml.error else "Invalid source"
            return {"status": log.FATAL,
                    "message": msg,
                    "remote": remote,
                    "response": xml.json_message(False, 400, msg),
                    }

        # Identify feed category
        category = tree.findall("//channel/category")
        if not category:
            msg = "Feed category missing"
            return {"status": log.ERROR,
                    "message": msg,
                    "remote": remote,
                    "response": xml.json_message(False, 400, msg),
                    }
        category = category[0].text

        # Instantiate target resource after feed category
        if category == "AVL":
            resource = s3db.resource("pr_group")
        elif category == "Incidents":
            resource = s3db.resource("event_incident")
        else:
            msg = "Unknown feed category"
            return {"status": log.WARNING,
                    "message": msg,
                    "remote": remote,
                    "response": xml.json_message(False, 400, msg),
                    }

        # Import transformation stylesheet
        stylesheet = os.path.join(current.request.folder,
                                  "static",
                                  "formats",
                                  "georss",
                                  "import.xsl",
                                  )

        # Import parameters
        if onconflict:
            onconflict_callback = lambda item: onconflict(item,
                                                          repository,
                                                          resource,
                                                          )
        else:
            onconflict_callback = None
        ignore_errors = True

        # Import
        output = resource.import_xml(tree,
                                     format = "xml",
                                     stylesheet = stylesheet,
                                     ignore_errors = ignore_errors,
                                     strategy = strategy,
                                     update_policy = update_policy,
                                     conflict_policy = conflict_policy,
                                     last_sync = last_sync,
                                     onconflict = onconflict_callback,
                                     source_type = "adashi",
                                     )

        # Process validation errors, if any
        if resource.error_tree is not None:

            result = log.WARNING if ignore_errors else log.FATAL
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
            message = "Data received from peer"

        return {"status": result,
                "remote": remote,
                "message": message,
                "response": output,
                }

# End =========================================================================
