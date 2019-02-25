# -*- coding: utf-8 -*-

""" S3 Synchronization

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

import json
import sys
import datetime

try:
    from cStringIO import StringIO # Faster, where available
except ImportError:
    from StringIO import StringIO

from gluon import current, URL, DIV
from gluon.storage import Storage

from s3datetime import s3_parse_datetime, s3_utc
from s3rest import S3Method
from s3import import S3ImportItem
from s3query import S3URLQuery
from s3utils import s3_str

# =============================================================================
class S3Sync(S3Method):
    """ Synchronization Handler """

    def __init__(self):
        """ Constructor """

        S3Method.__init__(self)

        self.log = S3SyncLog()
        self._config = None

    # -------------------------------------------------------------------------
    def apply_method(self, r, **attr):
        """
            RESTful method handler, responds to:
                - GET [prefix]/[name]/sync.xml          - incoming pull
                - PUT|POST [prefix]/[name]/sync.xml     - incoming push
                - POST sync/repository/register.json    - remote registration

            NB incoming pull/push reponse normally by local sync/sync
               controller as resource proxy => back-end generated S3Request

            @param r: the S3Request
            @param attr: controller parameters for the request
        """

        output = {}

        method = r.method
        if method == "sync":

            if r.http == "GET":
                # Incoming pull
                output = self.__send(r, **attr)

            elif r.http in ("PUT", "POST"):
                # Incoming push
                output = self.__receive(r, **attr)

            else:
                r.error(405, current.ERROR.BAD_METHOD)

        elif method == "register":

            if r.http in ("PUT", "POST"):
                # Incoming registration request
                if r.representation == "json":
                    output = self.__register(r, **attr)
                else:
                    r.error(415, current.ERROR.BAD_FORMAT)

            else:
                r.error(405, current.ERROR.BAD_METHOD)

        else:
            r.error(405, current.ERROR.BAD_METHOD)

        return output

    # -------------------------------------------------------------------------
    # REST Methods:
    # -------------------------------------------------------------------------
    def __register(self, r, **attr):
        """
            Respond to an incoming registration request

            @param r: the S3Request
            @param attr: controller parameters for the request
        """

        # Parse the request parameters
        from s3validators import JSONERRORS
        source = r.read_body()
        if not source:
            r.error(400, "Missing parameters")
        try:
            parameters = json.load(source[0])
        except JSONERRORS:
            r.error(400, "Invalid parameters: %s" % (sys.exc_info()[1]))

        log = self.log

        result = log.SUCCESS
        repository_id = None

        ruid = parameters.get("uuid")
        if ruid:

            # New repository or update?
            db = current.db
            rtable = current.s3db.sync_repository
            row = db(rtable.uuid == ruid).select(rtable.id,
                                                 limitby = (0, 1),
                                                 ).first()

            # Check permissions
            permitted = current.auth.s3_has_permission
            if row:
                repository_id = row.id
                if not permitted("update", rtable, record_id = repository_id):
                    r.unauthorised()
                data = {"deleted": False}
            else:
                if not permitted("create", rtable):
                    r.unauthorised()
                data = {"uuid": ruid}

            # Add repository parameters
            apitype = parameters.get("apitype")
            if apitype:
                data["apitype"] = apitype

            name = parameters.get("name")
            if name:
                data["name"] = name

            # Update or insert repository record
            if row:
                success = row.update_record(**data)
                if success:
                    message = "Registration update successful"
                else:
                    result = log.ERROR
                    message = "Registration update failed"
            else:
                repository_id = rtable.insert(**data)
                if repository_id:
                    message = "Registration successful"
                else:
                    result = log.ERROR
                    message = "Registration failed"
        else:
            result = log.ERROR
            message = "No repository identifier specified"

        # Response message (JSON)
        if result == log.SUCCESS:
            output = current.xml.json_message(message = message,
                                              sender = "%s" % self.config.uuid,
                                              )
        else:
            output = current.xml.json_message(False, 400,
                                              message = message,
                                              sender = "%s" % self.config.uuid,
                                              )

        # Set Content-Type response header
        current.response.headers["Content-Type"] = "application/json"

        # Log the operation
        log.write(repository_id = repository_id,
                  resource_name = log.NONE,
                  transmission = log.IN,
                  mode = log.REGISTER,
                  result = result,
                  message = message,
                  )

        return output

    # -------------------------------------------------------------------------
    def __send(self, r, **attr):
        """
            Respond to an incoming pull

            @param r: the S3Request
            @param attr: the controller attributes
        """

        mixed =  attr.get("mixed", False)
        get_vars = r.get_vars
        vars_get = get_vars.get

        resource = r.resource

        # Identify the requesting repository
        repository_uuid = vars_get("repository")
        connector = None

        if repository_uuid:

            rtable = current.s3db.sync_repository
            query = rtable.uuid == repository_uuid
            row = current.db(query).select(limitby=(0, 1)).first()
            if row:
                connector = S3SyncRepository(row)

        if connector is None:
            # Use a dummy repository with Eden API
            connector = S3SyncRepository(Storage(id = None,
                                                 name = "unknown",
                                                 apitype = "eden",
                                                 ))

        current.log.debug("S3Sync PULL from %s (%s)" % (connector.name,
                                                        connector.apitype))

        # Additional export parameters
        start = vars_get("start", None)
        if start is not None:
            try:
                start = int(start)
            except ValueError:
                start = None
        limit = vars_get("limit", None)
        if limit is not None:
            try:
                limit = int(limit)
            except ValueError:
                limit = None
        msince = vars_get("msince", None)
        if msince is not None:
            msince = s3_parse_datetime(msince)

        # Sync filters from peer
        filters = {}
        for k, v in get_vars.items():
            if k[0] == "[" and "]" in k:
                tablename, urlvar = k[1:].split("]", 1)
                if urlvar:
                    if not tablename or tablename == "~":
                        tablename = resource.tablename
                    f = filters.get(tablename, {})
                    u = f.get(urlvar, None)
                    if u:
                        u = "%s&%s" % (u, v)
                    else:
                        u = v
                    f[urlvar] = u
                    filters[tablename] = f
        if not filters:
            filters = None

        # Should we include Components?
        # @ToDo: Option to specify components?
        components = vars_get("components", None)
        if components and components.lower() == "none":
            resource.components.reset(expose=[])

        try:
            result = connector.send(resource,
                                    start = start,
                                    limit = limit,
                                    msince = msince,
                                    filters = filters,
                                    mixed = mixed,
                                    )
        except NotImplementedError:
            r.error(405, "Synchronization method not supported for repository")

        log = self.log
        log.write(repository_id = connector.id,
                  resource_name = "mixed" if mixed else resource.tablename,
                  transmission = log.IN,
                  mode = log.PULL,
                  action = "send",
                  remote = result.get("remote", False),
                  result = result.get("status", log.NONE),
                  message = result.get("message", ""),
                  )

        return result.get("response")

    # -------------------------------------------------------------------------
    def __receive(self, r, **attr):
        """
            Respond to an incoming push

            @param r: the S3Request
            @param attr: the controller attributes
        """

        mixed = attr.get("mixed", False)
        get_vars = r.get_vars

        s3db = current.s3db
        db = current.db

        # Identify the sending repository
        repository_uuid = get_vars.get("repository")
        connector = None

        if repository_uuid:

            rtable = s3db.sync_repository
            query = rtable.uuid == repository_uuid
            row = current.db(query).select(limitby=(0, 1)).first()
            if row:
                connector = S3SyncRepository(row)

        if connector is None:
            # Repositories must be registered to push, so that we
            # can track sync times and log operations properly
            r.error(403, "Registration required")

        current.log.debug("S3Sync PUSH from %s (%s)" % (connector.name,
                                                        connector.apitype,
                                                        ))

        # Get strategy and policy
        default_update_policy = S3ImportItem.POLICY.NEWER
        default_conflict_policy = S3ImportItem.POLICY.MASTER

        # Identify the synchronization task
        ttable = s3db.sync_task
        if not mixed:
            query = (ttable.repository_id == connector.id) & \
                    (ttable.resource_name == r.tablename) & \
                    (ttable.deleted != True)
            task = db(query).select(limitby=(0, 1)).first()
        else:
            task = None

        last_sync = None
        if task:
            strategy = task.strategy
            update_policy = task.update_policy or default_update_policy
            conflict_policy = task.conflict_policy or default_conflict_policy
            if update_policy not in ("THIS", "OTHER"):
                last_sync = task.last_pull

        else:
            policies = S3ImportItem.POLICY
            p = get_vars.get("update_policy", None)
            values = {"THIS": "OTHER", "OTHER": "THIS"}
            switch = lambda p: p in values and values[p] or p
            if p and p in policies:
                p = switch(p)
                update_policy = policies[p]
            else:
                update_policy = default_update_policy
            p = get_vars.get("conflict_policy", None)
            if p and p in policies:
                p = switch(p)
                conflict_policy = policies[p]
            else:
                conflict_policy = default_conflict_policy
            msince = get_vars.get("msince", None)
            if msince is not None:
                last_sync = s3_parse_datetime(msince)
            s = get_vars.get("strategy", None)
            if s:
                s = str(s).split(",")
                methods = S3ImportItem.METHOD
                strategy = [method for method in methods.values()
                                   if method in s]
            else:
                strategy = ttable.strategy.default

        # Get the source
        source = r.read_body()

        # Import resource
        resource = r.resource

        try:
            result = connector.receive(source,
                                       resource,
                                       strategy = strategy,
                                       update_policy = update_policy,
                                       conflict_policy = conflict_policy,
                                       last_sync = last_sync,
                                       onconflict = self.onconflict,
                                       mixed = mixed,
                                       )
        except IOError:
            current.auth.permission.fail()
        except SyntaxError:
            e = sys.exc_info()[1]
            r.error(400, e)
        except NotImplementedError:
            r.error(405, "Synchronization method not supported for repository")

        log = self.log
        log.write(repository_id = connector.id,
                  resource_name = "mixed" if mixed else resource.tablename,
                  transmission = log.IN,
                  mode = log.PUSH,
                  action = "receive",
                  remote = result.get("remote", False),
                  result = result.get("status", log.NONE),
                  message = result.get("message", ""),
                  )

        return result.get("response")

    # -------------------------------------------------------------------------
    # API Methods:
    # -------------------------------------------------------------------------
    def synchronize(self, repository):
        """
            Synchronize with a repository, called from scheduler task

            @param repository: the repository Row

            @return: True if successful, False if there was an error
        """

        current.log.debug("S3Sync: synchronize %s" % repository.url)

        log = self.log
        repository_id = repository.id

        error = None
        if repository.apitype == "filesync":
            if not repository.path:
                error = "No path set for repository"
        else:
            if not repository.url:
                error = "No URL set for repository"
        if error:
            log.write(repository_id = repository_id,
                      resource_name = None,
                      transmission = None,
                      mode = log.NONE,
                      action = "connect",
                      remote = False,
                      result = log.FATAL,
                      message = error,
                      )
            return False

        # Should we update sync tasks from peer?
        connector = S3SyncRepository(repository)
        if hasattr(connector, "refresh"):
            success = connector.refresh()

        # Look up current sync tasks
        db = current.db
        s3db = current.s3db
        ttable = s3db.sync_task
        query = (ttable.repository_id == repository_id) & \
                (ttable.deleted == False)
        tasks = db(query).select()

        # Login at repository
        error = connector.login()
        if error:
            log.write(repository_id = repository_id,
                      resource_name = None,
                      transmission = log.OUT,
                      mode = log.LOGIN,
                      action = "login",
                      remote = True,
                      result = log.FATAL,
                      message = error,
                      )
            return False

        # Activate UUID synchronisation if required
        s3 = current.response.s3
        s3.synchronise_uuids = connector.synchronise_uuids

        # Delta for msince progress = 1 second after the mtime of
        # the youngest item transmitted (without this, the youngest
        # items would be re-transmitted until there is another update,
        # because msince means greater-or-equal)
        delta = datetime.timedelta(seconds=1)

        success = True
        for task in tasks:

            # Pull
            mtime = None
            if task.mode in (1, 3):
                error, mtime = connector.pull(task,
                                              onconflict=self.onconflict,
                                              )
            if error:
                success = False
                current.log.debug("S3Sync: %s PULL error: %s" %
                                  (task.resource_name, error))
                continue
            if mtime is not None:
                task.update_record(last_pull=mtime+delta)

            # Push
            mtime = None
            if task.mode in (2, 3):
                error, mtime = connector.push(task)
            if error:
                success = False
                current.log.debug("S3Sync: %s PUSH error: %s" %
                                  (task.resource_name, error))
                continue
            if mtime is not None:
                task.update_record(last_push=mtime+delta)

            current.log.debug("S3Sync.synchronize: %s done" % task.resource_name)

        s3.synchronise_uuids = False
        db(s3db.sync_repository.id == repository_id).update(
                            last_connected = datetime.datetime.utcnow(),
                            )

        connector.close_archives()

        return success

    # -------------------------------------------------------------------------
    @classmethod
    def onconflict(cls, item, repository, resource):
        """
            Automatic conflict resolution

            @param item: the conflicting import item
            @param repository: the repository the item comes from
            @param resource: the resource the item shall be imported to
        """

        s3db = current.s3db
        debug = current.log.debug

        tablename = resource.tablename
        resolver = s3db.get_config(tablename, "onconflict")

        debug("Resolving conflict in %s" % resource.tablename)
        debug("Repository: %s" % repository.name)
        debug("Conflicting item: %s" % item)
        debug("Method: %s" % item.method)

        if resolver:
            debug("Applying custom rule")
            resolver(item, repository, resource)
            if item.conflict:
                debug("Do not accept")
            else:
                debug("Accept per custom rule")
        else:
            debug("Applying default rule")
            ttable = s3db.sync_task
            policies = S3ImportItem.POLICY
            query = (ttable.repository_id == repository.id) & \
                    (ttable.resource_name == tablename) & \
                    (ttable.deleted != True)
            task = current.db(query).select(limitby=(0, 1)).first()
            if task and item.original:
                original = item.original
                conflict_policy = task.conflict_policy
                if conflict_policy == policies.OTHER:
                    # Always accept
                    debug("Accept by default")
                    item.conflict = False
                elif conflict_policy == policies.NEWER:
                    # Accept if newer
                    xml = current.xml
                    if xml.MTIME in original and \
                       s3_utc(original[xml.MTIME]) <= item.mtime:
                        debug("Accept because newer")
                        item.conflict = False
                    else:
                        debug("Do not accept")
                elif conflict_policy == policies.MASTER:
                    # Accept if master
                    if current.xml.MCI in original and \
                       original.mci == 0 or item.mci == 1:
                        debug("Accept because master")
                        item.conflict = False
                    else:
                        debug("Do not accept")
                else:
                    # Never accept
                    debug("Do not accept")
            else:
                # No rule - accept always
                debug("Accept because no rule found")
                item.conflict = False

    # -------------------------------------------------------------------------
    def create_archive(self, dataset_id, task_id=None):
        """
            Create an archive for a data set

            @param dataset_id: the data set record ID
            @param task_id: the scheduler task ID if the archive is
                            created asynchronously

            @return: error message if an error occured, otherwise None
        """

        db = current.db
        s3db = current.s3db

        T = current.T

        # Standard download path for archives
        DOWNLOAD = "/default/download"

        # Get the data set
        dtable = s3db.sync_dataset
        query = (dtable.id == dataset_id) & \
                (dtable.deleted == False)
        dataset = db(query).select(dtable.id,
                                   dtable.code,
                                   dtable.archive_url,
                                   dtable.repository_id,
                                   limitby = (0, 1),
                                   ).first()
        if not dataset:
            return T("Data Set not found")
        elif dataset.repository_id:
            return T("Cannot create archive from remote data set")
        else:
            code = dataset.code
            if code:
                filename = "%s.zip" % code
            else:
                filename = "dataset-%s.zip" % dataset_id

        # Get all sync tasks for the data set
        ttable = s3db.sync_task
        query = (ttable.dataset_id == dataset_id) & \
                (ttable.repository_id == None) & \
                (ttable.mode == 1) & \
                (ttable.deleted == False)
        tasks = db(query).select(ttable.id,
                                 ttable.uuid,
                                 ttable.resource_name,
                                 ttable.components,
                                 )

        if not tasks:
            return T("No resources defined for dataset")

        # Get the current archive record
        atable = s3db.sync_dataset_archive
        query = (atable.dataset_id == dataset_id) & \
                (atable.deleted == False)
        row = db(query).select(atable.id,
                               limitby = (0, 1),
                               ).first()
        if row:
            archive_id = row.id
            if task_id:
                row.update_record(task_id=task_id)
                db.commit()
        else:
            archive_id = atable.insert(dataset_id = dataset_id)
        if not archive_id:
            return T("Could not create or update archive")

        # Create archive
        archive = S3SyncDataArchive()

        for task in tasks:

            # Define the resource
            components = [] if task.components is False else None
            resource = current.s3db.resource(task.resource_name,
                                             components = components,
                                             )

            # Get the sync filters for this task
            filters = current.sync.get_filters(task.id)

            # Export the resource as S3XML
            data = resource.export_xml(filters = filters,
                                       #pretty_print = True,
                                       )

            # Add to archive, using the UUID of the task as object name
            archive.add("%s.xml" % task.uuid, data)

        # Close the archive and get the output as file-like object
        fileobj = archive.close()

        # Store the fileobj in the archive-field
        stored_filename = atable.archive.store(fileobj, filename)
        db(atable.id == archive_id).update(date = datetime.datetime.utcnow(),
                                           archive = stored_filename,
                                           task_id = None,
                                           )

        # Update archive URL if it is empty or a local path
        # pointing to the standard download location
        archive_url = dataset.archive_url
        if not archive_url or archive_url.startswith(DOWNLOAD):
            dataset.update_record(
                use_archive = True,
                archive_url = "%s/%s" % (DOWNLOAD, stored_filename),
                )

        # Return None to indicate success
        return None

    # -------------------------------------------------------------------------
    # Utility methods:
    # -------------------------------------------------------------------------
    @property
    def config(self):
        """ Lazy access to the current sync config """

        if self._config is None:

            table = current.s3db.sync_config
            row = current.db().select(table.ALL, limitby=(0, 1)).first()
            self._config = row

        return self._config

    # -------------------------------------------------------------------------
    def get_status(self):
        """ Read the current sync status """

        table = current.s3db.sync_status
        row = current.db().select(table.ALL, limitby=(0, 1)).first()
        if not row:
            row = Storage()
        return row

    # -------------------------------------------------------------------------
    def set_status(self, **attr):
        """ Update the current sync status """

        table = current.s3db.sync_status

        data = dict((k, attr[k]) for k in attr if k in table.fields)
        data["timestmp"] = datetime.datetime.utcnow()

        row = current.db().select(table._id, limitby=(0, 1)).first()
        if row:
            row.update_record(**data)
        else:
            table.insert(**data)
            row = data
        return row

    # -------------------------------------------------------------------------
    @staticmethod
    def get_filters(task_id):
        """
            Get all filters for a synchronization task

            @param task_id: the task ID
            @return: a dict of dicts like {tablename: {url_var: value}}
        """

        db = current.db
        s3db = current.s3db

        ftable = s3db.sync_resource_filter
        query = (ftable.task_id == task_id) & \
                (ftable.deleted != True)
        rows = db(query).select(ftable.tablename,
                                ftable.filter_string,
                                )

        filters = {}
        for row in rows:
            tablename = row.tablename
            if tablename in filters:
                filters[tablename] = "%s&%s" % (filters[tablename],
                                                row.filter_string,
                                                )
            else:
                filters[tablename] = row.filter_string

        parse_url = S3URLQuery.parse_url
        for tablename in filters:
            filters[tablename] = parse_url(filters[tablename])
        return filters

# =============================================================================
class S3SyncLog(S3Method):
    """ Synchronization Logger """

    TABLENAME = "sync_log"

    # Outcomes
    SUCCESS = "success"     # worked
    WARNING = "warning"     # worked, but had issues
    ERROR = "error"         # failed, but may work later
    FATAL = "fatal"         # failed, will never work unless reconfigured

    # Transmissions
    IN = "incoming"
    OUT = "outgoing"

    # Methods
    PULL = "pull"
    PUSH = "push"
    LOGIN = "login"
    REGISTER = "register"

    # None
    NONE = "none"

    # -------------------------------------------------------------------------
    def apply_method(self, r, **attr):
        """
            RESTful method handler

            @param r: the S3Request instance
            @param attr: controller attributes for the request
        """

        output = {}

        resource = r.resource
        if resource.tablename == self.TABLENAME:
            return resource.crud.select(r, **attr)

        elif resource.tablename == "sync_repository":
            # READ for sync log for this repository (currently not needed)
            pass

        else:
            if r.interactive:
                # READ for sync log for this resource
                here = "%s.%s" % (r.controller, r.function)
                sync_log = current.s3db[self.TABLENAME]
                sync_log.resource_name.readable = False
                query = (sync_log.resource_name == resource.tablename)
                r = r.factory(prefix="sync", name="log", args=[])
                s3 = current.response.s3
                s3.filter = query
                s3.prep = None
                s3.postp = None
                s3.actions = [{"label": s3_str(current.T("Details")),
                               "_class": "action-btn",
                               "url": URL(c = "sync",
                                          f = "log",
                                          args = ["[id]"],
                                          vars = {"return":here},
                                          )
                               },
                              ]
                output = r(subtitle=None, rheader=self.rheader)
            else:
                r.error(415, current.ERROR.BAD_FORMAT)

        return output

    # -------------------------------------------------------------------------
    @classmethod
    def write(cls,
              repository_id=None,
              resource_name=None,
              transmission=None,
              mode=None,
              action=None,
              result=None,
              remote=False,
              message=None):
        """
            Writes a new entry to the log

            @param repository_id: the repository record ID
            @param resource_name: the resource name
            @param transmission: transmission mode (IN, OUT or None)
            @param mode: synchronization mode (PULL, PUSH or None)
            @param action: action that triggers the log entry (if any)
            @param result: the result of the transaction
                           (SUCCESS, WARNING, ERROR or FATAL)
            @param remote: boolean, True if this is a remote error
            @param message: clear text message
        """

        if result not in (cls.SUCCESS, cls.WARNING, cls.ERROR, cls.FATAL):
            result = cls.SUCCESS

        if result == cls.SUCCESS:
            # Can't be a remote error if it's not an error at all
            remote = False

        if transmission not in (cls.IN, cls.OUT):
            transmission = cls.NONE

        if mode not in (cls.PULL, cls.PUSH, cls.LOGIN, cls.REGISTER):
            mode = cls.NONE

        if not action:
            action = cls.NONE

        entry = {"timestmp": datetime.datetime.utcnow(),
                 "repository_id": repository_id,
                 "resource_name": resource_name,
                 "mode": "%s/%s" % (mode, transmission),
                 "action": action,
                 "result": result,
                 "remote": remote,
                 "message": message,
                 }

        current.s3db[cls.TABLENAME].insert(**entry)

    # -------------------------------------------------------------------------
    @staticmethod
    def rheader(r, **attr):
        """ S3SyncLog resource header """

        if r.id is None:
            return DIV(current.T("Showing latest entries first"))
        else:
            return None

# =============================================================================
class S3SyncRepository(object):
    """ Class representation of a peer repository """

    def __init__(self, repository):
        """
            Constructor

            @param repository: the repository record (Row)
        """

        # Logger and Config
        self.log = S3SyncLog
        self._config = None

        # Identifier and name
        self.id = repository.id
        self.name = repository.name

        # API type and import/export backend
        self.apitype = repository.apitype
        self.backend = repository.backend

        # URL / Path
        self.url = repository.url
        self.path = repository.path

        # Authentication
        self.username = repository.username
        self.password = repository.password
        self.client_id = repository.client_id
        self.client_secret = repository.client_secret
        self.site_key = repository.site_key
        self.refresh_token = repository.refresh_token

        # Network
        self.proxy = repository.proxy

        # Processing Options
        self.synchronise_uuids = repository.synchronise_uuids
        self.keep_source = repository.keep_source
        self.last_refresh = repository.last_refresh

        # Instantiate Adapter
        import sync_adapter
        api = sync_adapter.__dict__.get(self.apitype)
        if api:
            adapter = api.S3SyncAdapter(self)
        else:
            adapter = S3SyncBaseAdapter(self)

        self.adapter = adapter
        self.archives = {}

    # -------------------------------------------------------------------------
    @property
    def config(self):
        """ Lazy access to the current sync config """

        if self._config is None:

            table = current.s3db.sync_config
            row = current.db().select(table.ALL, limitby=(0, 1)).first()
            self._config = row

        return self._config

    # -------------------------------------------------------------------------
    def __getattr__(self, name):
        """
            Delegate other attributes and methods to the adapter

            @param name: the attribute/method
        """

        return object.__getattribute__(self.adapter, name)

    # -------------------------------------------------------------------------
    def close_archives(self):
        """
            Close any open archives
        """

        for archive in self.archives.values():
            if archive:
                archive.close()
        self.archives = {}

# =============================================================================
class S3SyncBaseAdapter(object):
    """
        Sync Adapter (base class) - interface providing standard
        synchronization methods for the respective repository type.

        This class isn't meant to be instantiated or accessed directly,
        but is normally accessed through the S3SyncRepository instance.
    """

    def __init__(self, repository):
        """
            Constructor

            @param repository: the repository (S3Repository instance)
        """

        self.repository = repository
        self.log = repository.log

        self.archives = {}

    # -------------------------------------------------------------------------
    # Methods to be implemented by subclasses:
    # -------------------------------------------------------------------------
    def register(self):
        """
            Register this site at the peer repository

            @return: True|False to indicate success|failure,
                     or None if registration is not required
        """

        raise NotImplementedError

    # -------------------------------------------------------------------------
    def login(self):
        """
            Login at the peer repository

            @return: None if successful, otherwise the error
        """

        raise NotImplementedError

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

        raise NotImplementedError

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

        raise NotImplementedError

    # -------------------------------------------------------------------------
    def send(self,
             resource,
             start=None,
             limit=None,
             msince=None,
             filters=None,
             mixed=False,
             pretty_print=False,
             ):
        """
            Respond to an incoming pull from the peer repository

            @param resource: the resource to be synchronized
            @param start: index of the first record to send
            @param limit: maximum number of records to send
            @param msince: minimum modification date/time for records to send
            @param filters: URL filters for record extraction
            @param mixed: negotiate resource with peer (disregard resource)
            @param pretty_print: make the output human-readable

            @return: a dict {status, remote, message, response}, with:
                        - status....the outcome of the operation
                        - remote....whether the error was remote (or local)
                        - message...the log message
                        - response..the response to send to the peer
        """

        raise NotImplementedError

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

        raise NotImplementedError

# =============================================================================
class S3SyncDataArchive(object):
    """
        Simple abstraction layer for (compressed) data archives, currently
        based on zipfile (Python standard library). Compression additionally
        requires zlib to be installed (both for write and read).
    """

    def __init__(self, fileobj=None, compressed=True):
        """
            Create or open an archive

            @param fileobj: the file object containing the archive,
                            None to create a new archive
            @param compress: enable (or suppress) compression of new
                             archives
        """

        import zipfile

        if compressed:
            compression = zipfile.ZIP_DEFLATED
        else:
            compression = zipfile.ZIP_STORED

        if fileobj is not None:
            if not hasattr(fileobj, "seek"):
                # Possibly a addinfourl instance from urlopen,
                # => must copy to StringIO buffer for random access
                fileobj = StringIO(fileobj.read())
            try:
                archive = zipfile.ZipFile(fileobj, "r")
            except RuntimeError:
                current.log.warn("invalid ZIP archive: %s" % sys.exc_info()[1])
                archive = None
        else:
            fileobj = StringIO()
            try:
                archive = zipfile.ZipFile(fileobj, "w", compression, True)
            except RuntimeError:
                # Zlib not available? => try falling back to STORED
                compression = zipfile.ZIP_STORED
                archive = zipfile.ZipFile(fileobj, "w", compression, True)
                current.log.warn("zlib not available - cannot compress archive")

        self.fileobj = fileobj
        self.archive = archive

    # -------------------------------------------------------------------------
    def add(self, name, obj):
        """
            Add an object to the archive

            @param name: the file name for the object inside the archive
            @param obj: the object to add (string or file-like object)

            @raises UserWarning: when adding a duplicate name (overwrites
                                 the existing object in the archive)
            @raises RuntimeError: if the archive is not writable, or
                                  no valid object name has been provided
            @raises TypeError: if the object is not a unicode, str or
                               file-like object
        """

        # Make sure the object name is an utf-8 encoded str
        if not name:
            raise RuntimeError("name is required")
        elif type(name) is not str:
            name = s3_str(name)

        # Make sure the archive is available
        archive = self.archive
        if not archive:
            raise RuntimeError("cannot add to closed archive")

        # Convert unicode objects to str
        if type(obj) is unicode:
            obj = obj.encode("utf-8")

        # Write the object
        if type(obj) is str:
            archive.writestr(name, obj)

        elif hasattr(obj, "read"):
            if hasattr(obj, "seek"):
                obj.seek(0)
            archive.writestr(name, obj.read())

        else:
            raise TypeError("invalid object type")

    # -------------------------------------------------------------------------
    def extract(self, name):
        """
            Extract an object from the archive by name

            @param name: the object name

            @return: the object as file-like object, or None if
                     the object could not be found in the archive
        """

        if not self.archive:
            raise RuntimeError("cannot extract from closed archive")

        try:
            return self.archive.open(name)
        except KeyError:
            # Object doesn't exist
            return None

    # -------------------------------------------------------------------------
    def close(self):
        """
            Close the archive and return it as file-like object; no further
            add/extract operations will be possible after closing.

            @return: the file-like object containing the archive
        """

        if self.archive:
            self.archive.close()
            self.archive = None

        fileobj = self.fileobj
        if fileobj:
            fileobj.seek(0)

        return fileobj

# End =========================================================================
