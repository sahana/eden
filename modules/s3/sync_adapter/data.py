# -*- coding: utf-8 -*-

""" S3 Synchronization: Peer Repository Adapter

    @copyright: 2011-2021 (c) Sahana Software Foundation
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

try:
    from lxml import etree
except ImportError:
    sys.stderr.write("ERROR: lxml module needed for XML handling\n")
    raise
from urllib.error import HTTPError, URLError
from urllib.parse import quote as urllib_quote

from gluon import current

from ..s3datetime import s3_encode_iso_datetime
from ..s3validators import JSONERRORS
from .eden import S3SyncAdapter as S3SyncEdenAdapter

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

        db = current.db
        s3db = current.s3db

        repository = self.repository
        log = repository.log

        base_url = repository.url
        if not base_url:
            # No repository URL => refresh not possible
            return None

        debug = current.log.debug
        debug("Refreshing sync tasks from %s" % base_url)

        # Look up all data sets currently configured for this repository
        repository_id = repository.id
        table = s3db.sync_dataset
        query = (table.repository_id == repository_id) & \
                (table.deleted == False)
        datasets = db(query).select(table.code)

        if not datasets:
            # No data sets configured => no tasks to refresh
            return None
        else:
            # Collect the data set codes
            codes = set(dataset.code for dataset in datasets)

        # Determine the necessary updates
        current_tasks = "%s/sync/task.xml?~.dataset_id$code=%s" % \
                        (base_url, urllib_quote(",".join(codes)))
        updates = [{"tablename": "sync_task",
                    "url": current_tasks,
                    "strategy": ("create", "update"),
                    },
                   ]

        # Look up last refresh date
        last_refresh = repository.last_refresh
        if last_refresh:
            # Use msince
            msince = s3_encode_iso_datetime(last_refresh)

            # Also fetch deleted tasks/filters
            deleted = "?include_deleted=True&~.deleted=True"
            deleted_tasks = "%s/sync/task.xml%s" % (base_url, deleted)
            deleted_filters = "%s/sync/resource_filter.xml%s" % (base_url, deleted)
            updates.extend([{"tablename": "sync_task",
                             "url": deleted_tasks,
                             "strategy": ("delete",),
                             },
                            {"tablename": "sync_resource_filter",
                             "url": deleted_filters,
                             "strategy": ("delete",),
                             },
                            ])
        else:
            # No msince, just get all current tasks for the configured data sets
            msince = None

        # Initialize log details
        success = False
        count = 0
        timestamp = None

        # Enable UUID synchronization
        s3 = current.response.s3
        synchronise_uuids = s3.synchronise_uuids
        s3.synchronise_uuids = True

        # Fetch the sync tasks for the configured data sets
        for update in updates:

            error = self._fetch(update, msince)

            if error:
                # Log the error, skip the update
                log.write(repository_id = repository_id,
                          transmission = log.OUT,
                          mode = log.PULL,
                          action = "refresh",
                          remote = update.get("remote", False),
                          result = update.get("result", log.ERROR),
                          message = error,
                          )
                continue

            if update.get("response"):
                error = self._import(update)
                if error:
                    # Log the error
                    log.write(repository_id = repository_id,
                              transmission = log.OUT,
                              mode = log.PULL,
                              action = "refresh",
                              remote = update.get("remote", False),
                              result = update.get("result", log.ERROR),
                              message = error,
                              )
                else:
                    # Success - collect count/mtime
                    success = True
                    if update["tablename"] == "sync_task":
                        count += update.get("count", 0)
                    mtime = update.get("mtime")
                    if mtime and (not timestamp or timestamp < mtime):
                        timestamp = mtime
            else:
                # Log no data received
                log.write(repository_id = repository_id,
                          transmission = log.OUT,
                          mode = log.PULL,
                          action = "refresh",
                          remote = False,
                          result = log.WARNING,
                          message = "No data received",
                          )

        if success:
            if count:
                message = "Successfully updated %s tasks" % count
            else:
                message = "No new/updated tasks found"

            log.write(repository_id = repository_id,
                      transmission = log.OUT,
                      mode = log.PULL,
                      action = "refresh",
                      remote = False,
                      result = log.SUCCESS,
                      message = message,
                      )

            if timestamp:
                # Update last_refresh
                delta = datetime.timedelta(seconds=1)
                rtable = s3db.sync_repository
                query = (rtable.id == repository_id)
                db(query).update(last_refresh=timestamp+delta)

        s3.synchronise_uuids = synchronise_uuids
        return True

    # -------------------------------------------------------------------------
    def _fetch(self, update, msince):
        """
            Fetch sync task updates from the repository

            @param update: the update dict containing:
                           {"url": the url to fetch,
                            }
            @return: error message if there was an error, otherwise None
        """

        log = self.repository.log
        error = None

        # Get the URL, add msince if available
        url = update["url"]
        if msince:
            url = "%s&msince=%s" % (url, msince)

        # Fetch the data
        opener = self._http_opener(url)
        try:
            f = opener.open(url)
        except HTTPError as e:
            # HTTP status (remote error)
            result = log.ERROR
            update["remote"] = True

            # Get the error message
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
            error = "[%s] %s" % (e.code, message)

        except URLError as e:
            # URL Error (network error)
            result = log.ERROR
            update["remote"] = True
            error = "Peer repository unavailable (%s)" % e.reason

        except:
            # Other error (local error)
            result = log.FATAL
            error = sys.exc_info()[1]

        else:
            # Success
            result = log.SUCCESS
            update["response"] = f

        update["result"] = result
        return error

    # -------------------------------------------------------------------------
    def _import(self, update):
        """
            Import sync task updates

            @param update: the update dict containing:
                           {"response": the response from _fetch,
                            "strategy": the import strategy,
                            }
            @return: error message if there was an error, otherwise None
        """


        repository = self.repository
        log = repository.log

        resource = current.s3db.resource(update["tablename"])

        # Set default repository for newly imported tasks
        strategy = update.get("strategy")
        if "create" in strategy:
            table = resource.table
            table.repository_id.default = repository.id

        error = None
        result = None

        response = update["response"]
        try:
            resource.import_xml(response,
                                ignore_errors = True,
                                strategy = strategy,
                                )
        except IOError:
            result = log.FATAL
            error = "%s" % sys.exc_info()[1]

        except:
            result = log.FATAL
            import traceback
            error = "Uncaught Exception During Import: %s" % \
                    traceback.format_exc()

        else:
            if resource.error:
                result = log.ERROR
                error = resource.error
            else:
                result = log.SUCCESS
                update["count"] = resource.import_count
                update["mtime"] = resource.mtime

        update["result"] = result

        return error

# End =========================================================================
