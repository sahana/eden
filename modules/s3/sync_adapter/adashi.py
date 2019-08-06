# -*- coding: utf-8 -*-

""" S3 Synchronization: Peer Repository Adapter for ADASHI

    @copyright: 2011-2019 (c) Sahana Software Foundation
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

from gluon import *

from ..s3sync import S3SyncBaseAdapter

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
        log = repository.log

        # Import path
        PATH = os.path.join(current.request.folder, "uploads", "adashi_feeds")

        # Read names from path
        try:
            files_list = os.listdir(PATH)
        except os.error:
            message = "Upload path does not exist or can not be accessed"
            log.write(repository_id = repository.id,
                      resource_name = "mixed",
                      transmission = log.IN,
                      mode = log.PUSH,
                      action = "read files from %s" % PATH,
                      remote = False,
                      result = log.FATAL,
                      message = message,
                      )
            return message, None

        # Add path to file names, filter for .xml files, sort by mtime
        files = [os.path.join(PATH, f)
                 for f in files_list if f[-4:] == ".xml"]
        files = sorted(filter(os.path.isfile, files), key=os.path.getmtime)

        # Strategy and Policies
        from ..s3import import S3ImportItem
        default_update_policy = S3ImportItem.POLICY.NEWER
        default_conflict_policy = S3ImportItem.POLICY.MASTER
        strategy = task.strategy
        update_policy = task.update_policy or default_update_policy
        conflict_policy = task.conflict_policy or default_conflict_policy
        if update_policy not in ("THIS", "OTHER"):
            last_sync = task.last_pull

        # Import files
        for f in files:
            current.log.debug("ADASHI Sync: importing %s" % f)
            try:
                with open(f, "r") as source:
                    result = self.receive([source],
                                          None,
                                          strategy=strategy,
                                          update_policy=update_policy,
                                          conflict_policy=conflict_policy,
                                          onconflict=onconflict,
                                          last_sync=last_sync,
                                          mixed=True,
                                          )
            except IOError:
                continue

            # Log the operation
            log.write(repository_id = repository.id,
                      resource_name = "mixed",
                      transmission = log.IN,
                      mode = log.PUSH,
                      action = "import %s" % f,
                      remote = result["remote"],
                      result = result["status"],
                      message = result["message"],
                      )

            # Remove the file
            try:
                os.remove(f)
            except os.error:
                current.log.error("ADASHI Sync: can not delete %s" % f)

        return None, current.request.utcnow

    # -------------------------------------------------------------------------
    def push(self, task):
        """
            Outgoing push

            @param task: the sync_task Row
        """

        repository = self.repository

        # Log the operation
        message = "Push to ADASHI currently not supported"
        log = repository.log
        log.write(repository_id = repository.id,
                  resource_name = task.resource_name,
                  transmission = log.OUT,
                  mode = log.PUSH,
                  action = None,
                  remote = False,
                  result = log.FATAL,
                  message = message,
                  )

        output = current.xml.json_message(False, 400, message)
        return output, None

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
            Respond to an incoming pull from a peer repository

            @param resource: the resource to be synchronized
            @param start: index of the first record to send
            @param limit: maximum number of records to send
            @param msince: minimum modification date/time for records to send
            @param filters: URL filters for record extraction
            @param mixed: negotiate resource with peer (disregard resource)
            @param pretty_print: make the output human-readable
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
                                     pretty_print=pretty_print,
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
            resource.configure(oncommit_import_item = self.update_assignments)
        else:
            msg = "Unknown feed category"
            return {"status": log.WARNING,
                    "message": msg,
                    "remote": remote,
                    "response": xml.json_message(False, 400, msg),
                    }

        # Store source data?
        repository = self.repository
        if repository.keep_source:
            self.keep_source(tree, category)

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
        # Flag to let audit know the repository
        s3 = current.response.s3
        s3.repository_id = self.repository.id
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
        s3.repository_id = None

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

    # -------------------------------------------------------------------------
    @staticmethod
    def update_assignments(item):
        """
            Deactivate all previous unit assignments (event_team) for
            an incident which are not in this feed update.

            @param item: the import item

            @note: this assumes that the list of incident resources in
                   the feed update is complete (confirmed for ADASHI)
            @note: must not deactivate assignments which are newer
                   than the feed update (Sync policy NEWER)
        """

        if item.tablename == "event_incident" and \
           item.id and \
           item.method == item.METHOD.UPDATE:

            job = item.job
            mtime = item.data.get("modified_on")

            if not job or not mtime:
                return
            get_item = job.items.get

            # Get the unit names of all current assignments in the feed
            team_names = set()
            add_name = team_names.add
            for citem in item.components:
                if citem.tablename == "event_team":
                    for ref in citem.references:
                        entry = ref.entry
                        team_item_id = entry.item_id
                        if entry.tablename == "pr_group" and team_item_id:
                            team_item = get_item(team_item_id)
                            team_name = team_item.data.get("name")
                            if team_name:
                                add_name(team_name)
                            break

            s3db = current.s3db

            ltable = s3db.event_team
            gtable = s3db.pr_group

            # Get all active assignments in the database which are older
            # than the feed update and which are not in the feed update,
            # and deactivate them
            left = gtable.on(ltable.group_id == gtable.id)
            query = (ltable.incident_id == item.id) & \
                    (ltable.modified_on <= mtime) & \
                    (ltable.status == 3) & \
                    (~(gtable.name.belongs(team_names)))
            rows = current.db(query).select(ltable.id, left=left)

            inactive = set(row.id for row in rows)
            current.db(ltable.id.belongs(inactive)).update(status=4)

    # -------------------------------------------------------------------------
    def keep_source(self, tree, category):
        """
            Helper method to store source data in file system

            @param tree: the XML element tree of the source
            @param category: the feed category
        """

        repository = self.repository

        # Log the operation
        log = repository.log
        log.write(repository_id = repository.id,
                  resource_name = None,
                  transmission = log.IN,
                  mode = log.PUSH,
                  action = "receive",
                  remote = False,
                  result = log.WARNING,
                  message = "'Keep Source Data' active for this repository!",
                  )

        request = current.request
        folder = os.path.join(request.folder, "uploads", "adashi")
        dt = request.utcnow.replace(microsecond=0).isoformat()
        dt = dt.replace(":", "").replace("-", "")
        filename = os.path.join(folder,
                                "%s_%s.xml" % (category, dt),
                                )
        if not os.path.exists(folder):
            try:
                os.mkdir(folder)
            except OSError:
                return
        if filename:
            try:
                with open(filename, "w") as f:
                    tree.write(f, pretty_print=True)
            except IOError:
                return

# End =========================================================================
