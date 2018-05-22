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
import urllib2

try:
    from lxml import etree
except ImportError:
    sys.stderr.write("ERROR: lxml module needed for XML handling\n")
    raise

from gluon import current

from ..s3datetime import s3_encode_iso_datetime
from ..s3validators import JSONERRORS
from eden import S3SyncAdapter as S3SyncEdenAdapter

# =============================================================================
class S3SyncAdapter(S3SyncEdenAdapter):
    """
        Sahana Eden Data Repository Synchronization Adapter
    """

    @staticmethod
    def register():
        """
            Register this site at the peer repository

            @return: True|False to indicate success|failure,
                     or None if registration is not required
        """

        # No registration required
        return None

    # -------------------------------------------------------------------------
    def refresh(self):
        """
            Refresh sync tasks from peer

            @return: True|False to indicate success|failure,
                     or None if registration is not required
        """

        repository = self.repository

        base_url = repository.url
        if not base_url:
            # No repository URL => refresh not possible
            return None

        debug = current.log.debug
        debug("Refreshing sync tasks from %s" % base_url)

        # Look up all data sets currently configured for this repository
        repository_id = repository.id

        db = current.db
        s3db = current.s3db

        table = s3db.sync_dataset
        query = (table.repository_id == repository_id) & \
                (table.deleted == False)
        datasets = db(query).select(table.code)

        if not datasets:
            # No data sets configured => no tasks to refresh
            return None
        else:
            codes = set(dataset.code for dataset in datasets)

        # Construct the URL
        from urllib import quote
        url = "%s/sync/task.xml?~.dataset_id$code=%s" % \
              (base_url, quote(",".join(codes)))

        # Look up last refresh date
        last_refresh = repository.last_refresh
        if last_refresh:
            url = "%s&msince=%s" % (url, s3_encode_iso_datetime(last_refresh))

        # Initialize log details
        remote = False
        result = None
        message = None

        # Fetch the sync tasks for the configured data sets
        opener = self._http_opener(url)
        response = None
        log = repository.log
        try:
            f = opener.open(url)
        except urllib2.HTTPError, e:
            # HTTP status
            result = log.ERROR
            remote = True # Peer error

            message = e.read()
            try:
                # Sahana-Eden would send a JSON message,
                # try to extract the actual error message:
                message_json = json.loads(message)
            except JSONERRORS:
                pass
            else:
                message = message_json.get("message", message)

            # Strip XML markup from the message
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

            # Prepend HTTP status code
            message = "[%s] %s" % (e.code, message)

        except:
            # Other error
            result = log.FATAL
            message = sys.exc_info()[1]
        else:
            response = f

        # Import the sync_tasks
        if response:
            resource = current.s3db.resource("sync_task")

            # Set default repository for newly imported tasks
            table = resource.table
            field = table.repository_id
            field.default = repository_id

            count = 0
            try:
                resource.import_xml(response,
                                    ignore_errors = True,
                                    )
                count = resource.import_count
                mtime = resource.mtime
            except IOError:
                result = log.FATAL
                message = "%s" % sys.exc_info()[1]
            except:
                result = log.FATAL
                import traceback
                message = "Uncaught Exception During Import: %s" % \
                          traceback.format_exc()
            else:
                if resource.error:
                    result = log.ERROR
                    message = resource.error
                else:
                    if count == 0:
                        message = "No new/updated tasks found"
                    else:
                        message = "Successfully refreshed %s tasks" % count
                    # Update last_refresh timestamp of the repository
                    if mtime:
                        # Delta for msince progress
                        delta = datetime.timedelta(seconds=1)
                        rtable = s3db.sync_repository
                        query = (rtable.id == repository_id)
                        db(query).update(last_refresh=mtime+delta)
        else:
            result = log.WARNING
            message = "No data received"

        # Log the operation
        log.write(repository_id = repository_id,
                  transmission = log.OUT,
                  mode = log.PULL,
                  action = "refresh",
                  remote = remote,
                  result = result,
                  message = message,
                  )

        return True

# End =========================================================================
