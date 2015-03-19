# -*- coding: utf-8 -*-

""" S3 Synchronization

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

import sys
import urllib, urllib2
import datetime
import time
import traceback

try:
    from cStringIO import StringIO # Faster, where available
except:
    from StringIO import StringIO

try:
    from lxml import etree
except ImportError:
    print >> sys.stderr, "ERROR: lxml module needed for XML handling"
    raise

try:
    import json # try stdlib (Python 2.6)
except ImportError:
    try:
        import simplejson as json # try external module
    except:
        import gluon.contrib.simplejson as json # fallback to pure-Python module

from gluon import *
from gluon.storage import Storage

from s3datetime import s3_utc
from s3rest import S3Method
from s3import import S3ImportItem
from s3query import S3URLQuery
from s3utils import s3_unicode

DEBUG = False
if DEBUG:
    print >> sys.stderr, "S3SYNC: DEBUG MODE"

    def _debug(m):
        print >> sys.stderr, m
else:
    _debug = lambda m: None

# =============================================================================
class S3Sync(S3Method):
    """ Synchronization Handler """

    # -------------------------------------------------------------------------
    def __init__(self):
        """ Constructor """

        S3Method.__init__(self)
        self.log = S3SyncLog()

    # -------------------------------------------------------------------------
    def apply_method(self, r, **attr):
        """
            RESTful method handler (repository/sync, repository/register)

            @param r: the S3Request instance
            @param attr: controller attributes for the request
        """

        output = dict()

        if r.method == "sync":

            if r.http == "GET":
                # Incoming pull
                output = self.__send(r, **attr)

            elif r.http in ("PUT", "POST"):
                # Incoming push
                output = self.__receive(r, **attr)

            else:
                r.error(405, current.ERROR.BAD_METHOD)

        elif r.name == "repository" and r.method == "register":

            if r.http == "GET":
                # Incoming registration request
                output = self.__register(r, **attr)

            else:
                r.error(405, current.ERROR.BAD_METHOD)

        else:
            r.error(405, current.ERROR.BAD_METHOD)

        return output

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

        data = Storage([(k, attr[k]) for k in attr if k in table.fields])
        data.update(timestmp = datetime.datetime.utcnow())
        row = current.db().select(table._id, limitby=(0, 1)).first()
        if row:
            row.update_record(**data)
        else:
            table.insert(**data)
            row = data
        return row

    # -------------------------------------------------------------------------
    def __get_config(self):
        """ Read the sync settings, avoid repeated DB lookups """

        if not hasattr(self, "config"):

            table = current.s3db.sync_config
            row = current.db().select(table.ALL, limitby=(0, 1)).first()
            self.config = row

        return self.config

    # -------------------------------------------------------------------------
    def synchronize(self, repository):
        """
            Synchronize with a repository

            @param repository: the repository Row

            @return: True if successful, False if there was an error
        """

        _debug("S3Sync.synchronize(%s)" % repository.url)

        log = self.log

        if not repository.url:
            message = "No URL set for repository"
            log.write(repository_id=repository.id,
                      resource_name=None,
                      transmission=None,
                      mode=None,
                      action="connect",
                      remote=False,
                      result=self.log.FATAL,
                      message=message)
            return False

        ttable = current.s3db.sync_task
        query = (ttable.repository_id == repository.id) & \
                (ttable.deleted != True)
        tasks = current.db(query).select()

        connector = S3SyncRepository(repository)
        error = connector.login()
        if error:
            log.write(repository_id=repository.id,
                      resource_name=None,
                      transmission=log.OUT,
                      mode=None,
                      action="login",
                      remote=True,
                      result=log.FATAL,
                      message=error)
            return False

        success = True
        for task in tasks:

            # Pull
            mtime = None
            if task.mode in (1, 3):
                error, mtime = connector.pull(task,
                                              onconflict=self.onconflict)
            if error:
                success = False
                _debug("S3Sync.synchronize: %s PULL error: %s" %
                                    (task.resource_name, error))
                continue
            if mtime is not None:
                task.update_record(last_pull=mtime)

            # Push
            mtime = None
            if task.mode in (2, 3):
                error, mtime = connector.push(task)
            if error:
                success = False
                _debug("S3Sync.synchronize: %s PUSH error: %s" %
                                    (task.resource_name, error))
                continue
            if mtime is not None:
                task.update_record(last_push=mtime)

            _debug("S3Sync.synchronize: %s done" % task.resource_name)

        return success

    # -------------------------------------------------------------------------
    def __register(self, r, **attr):
        """
            Respond to an incoming registration request

            @param r: the S3Request
            @param attr: the controller attributes
        """

        log = self.log
        result = log.SUCCESS
        message = "registration successful"
        repository_id = None

        config = self.__get_config()

        if "repository" in r.vars:
            ruid = r.vars["repository"]
            db = current.db
            rtable = current.s3db.sync_repository
            row = db(rtable.uuid == ruid).select(limitby=(0, 1)).first()
            if row:
                repository_id = row.id
                if not row.accept_push and current.auth.s3_has_role("ADMIN"):
                    row.update_record(accept_push=True)
            else:
                if current.auth.s3_has_role("ADMIN"):
                    accept_push = True
                else:
                    accept_push = False
                repository_id = rtable.insert(name=ruid,
                                              uuid=ruid,
                                              accept_push=accept_push)
                if not repository_id:
                    result = log.ERROR
                    message = "registration failed"
        else:
            result = log.ERROR
            message = "no repository identifier specified"

        if result == log.SUCCESS:
            output = current.xml.json_message(message=message,
                                              sender="%s" % config.uuid)
        else:
            output = current.xml.json_message(False, 400,
                                              message=message,
                                              sender="%s" % config.uuid)

        # Set content type header
        headers = current.response.headers
        headers["Content-Type"] = "application/json"

        # Log the operation
        log.write(repository_id=repository_id,
                  resource_name=log.NONE,
                  transmission=log.IN,
                  mode=log.PUSH,
                  action="register repository",
                  result=result,
                  message=message)

        return output

    # -------------------------------------------------------------------------
    def __send(self, r, **attr):
        """
            Respond to an incoming pull

            @param r: the S3Request
            @param attr: the controller attributes
        """

        _debug("S3Sync.__send")

        resource = r.resource

        # Identify the requesting repository
        repository_id = None
        if "repository" in r.vars:

            db = current.db
            s3db = current.s3db

            ruid = r.vars["repository"]
            rtable = s3db.sync_repository
            ttable = s3db.sync_task

            left = ttable.on((rtable.id == ttable.repository_id) & \
                             (ttable.resource_name == resource.tablename))

            row = db(rtable.uuid == ruid).select(rtable.id,
                                                 ttable.id,
                                                 left=left,
                                                 limitby=(0, 1)).first()
            if row:
                repository_id = row[rtable.id]
                task_id = row[ttable.id]

        # Additional export parameters
        _vars = r.get_vars
        start = _vars.get("start", None)
        if start is not None:
            try:
                start = int(start)
            except ValueError:
                start = None
        limit = _vars.get("limit", None)
        if limit is not None:
            try:
                limit = int(limit)
            except ValueError:
                limit = None
        msince = _vars.get("msince", None)
        if msince is not None:
            tfmt = current.xml.ISOFORMAT
            try:
                (y, m, d, hh, mm, ss, t0, t1, t2) = \
                    time.strptime(msince, tfmt)
                msince = datetime.datetime(y, m, d, hh, mm, ss)
            except ValueError:
                msince = None

        # Sync filters from peer
        filters = {}
        for k, v in _vars.items():
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

        # Export the resource
        output = resource.export_xml(start=start,
                                     limit=limit,
                                     filters=filters,
                                     msince=msince)
        count = resource.results

        # Set content type header
        headers = current.response.headers
        headers["Content-Type"] = "text/xml"

        # Log the operation
        log = self.log
        log.write(repository_id=repository_id,
                  resource_name=r.resource.tablename,
                  transmission=log.IN,
                  mode=log.PULL,
                  result=log.SUCCESS,
                  message="data sent to peer (%s records)" % count)

        return output

    # -------------------------------------------------------------------------
    def __receive(self, r, **attr):
        """
            Respond to an incoming push

            @param r: the S3Request
            @param attr: the controller attributes
        """

        _debug("S3Sync.__receive")

        s3db = current.s3db
        db = current.db

        # Identify the sending repository
        repository = Storage(id=None)
        if "repository" in r.vars:
            ruid = r.vars["repository"]
            rtable = s3db.sync_repository
            row = db(rtable.uuid == ruid).select(limitby=(0, 1)).first()
            if row:
                repository = row
        if not repository.id or \
           not repository.accept_push:
            r.error(403, current.ERROR.NOT_PERMITTED)

        # Get strategy and policy
        default_update_policy = S3ImportItem.POLICY.NEWER
        default_conflict_policy = S3ImportItem.POLICY.MASTER

        ttable = s3db.sync_task
        query = (ttable.repository_id == repository.id) & \
                (ttable.resource_name == r.tablename) & \
                (ttable.deleted != True)
        task = db(query).select(limitby=(0, 1)).first()
        last_sync = None
        if task:
            strategy = task.strategy
            update_policy = task.update_policy or default_update_policy
            conflict_policy = task.conflict_policy or default_conflict_policy
            if update_policy not in ("THIS", "OTHER"):
                last_sync = task.last_pull
        else:
            policies = S3ImportItem.POLICY
            p = r.get_vars.get("update_policy", None)
            values = {"THIS": "OTHER", "OTHER": "THIS"}
            switch = lambda p: p in values and values[p] or p
            if p and p in policies:
                p = switch(p)
                update_policy = policies[p]
            else:
                update_policy = default_update_policy
            p = r.get_vars.get("conflict_policy", None)
            if p and p in policies:
                p = switch(p)
                conflict_policy = policies[p]
            else:
                conflict_policy = default_conflict_policy
            msince = r.get_vars.get("msince", None)
            if msince is not None:
                tfmt = current.xml.ISOFORMAT
                try:
                    (y, m, d, hh, mm, ss, t0, t1, t2) = \
                        time.strptime(msince, tfmt)
                    last_sync = datetime.datetime(y, m, d, hh, mm, ss)
                except ValueError:
                    last_sync = None
            s = r.get_vars.get("strategy", None)
            if s:
                s = str(s).split(",")
                methods = S3ImportItem.METHOD
                strategy = [method for method in methods.values()
                                   if method in s]
            else:
                strategy = ttable.strategy.default

        # Other parameters
        ignore_errors = True

        # Get the source
        source = r.read_body()

        # Import resource
        resource = r.resource
        onconflict = lambda item: self.onconflict(item, repository, resource)
        try:
            output = resource.import_xml(source, format="xml",
                                         ignore_errors=ignore_errors,
                                         strategy=strategy,
                                         update_policy=update_policy,
                                         conflict_policy=conflict_policy,
                                         last_sync=last_sync,
                                         onconflict=onconflict)
        except IOError:
            current.auth.permission.fail()
        except SyntaxError:
            e = sys.exc_info()[1]
            r.error(400, e)

        log = self.log

        if resource.error_tree is not None:
            # Validation error (log in any case)
            if ignore_errors:
                result = log.WARNING
            else:
                result = log.FATAL
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
            message = "data received from peer"

        log.write(repository_id=repository.id,
                  resource_name=resource.tablename,
                  transmission=log.IN,
                  mode=log.PUSH,
                  result=result,
                  message=message)

        return output

    # -------------------------------------------------------------------------
    def onconflict(self, item, repository, resource):
        """
            Automatic conflict resolution

            @param item: the conflicting import item
            @param repository: the repository the item comes from
            @param resource: the resource the item shall be imported to
        """

        s3db = current.s3db

        tablename = resource.tablename
        resolver = s3db.get_config(tablename, "onconflict")

        _debug("Resolving conflict in %s" % resource.tablename)
        _debug("Repository: %s" % repository.name)
        _debug("Conflicting item: %s" % item)
        _debug("Method: %s" % item.method)

        if resolver:
            _debug("Applying custom rule")
            resolver(item, repository, resource)
            if item.conflict:
                _debug("Do not accept")
            else:
                _debug("Accept per custom rule")
        else:
            _debug("Applying default rule")
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
                    _debug("Accept by default")
                    item.conflict = False
                elif conflict_policy == policies.NEWER:
                    # Accept if newer
                    xml = current.xml
                    if xml.MTIME in original and \
                       s3_utc(original[xml.MTIME]) <= item.mtime:
                        _debug("Accept because newer")
                        item.conflict = False
                    else:
                        _debug("Do not accept")
                elif conflict_policy == policies.MASTER:
                    # Accept if master
                    if current.xml.MCI in original and \
                       original.mci == 0 or item.mci == 1:
                        _debug("Accept because master")
                        item.conflict = False
                    else:
                        _debug("Do not accept")
                else:
                    # Never accept
                    _debug("Do not accept")
                    pass
            else:
                # No rule - accept always
                _debug("Accept because no rule found")
                item.conflict = False

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
                                ftable.filter_string)

        filters = {}
        for row in rows:
            tablename = row.tablename
            if tablename in filters:
                filters[tablename] = "%s&%s" % (filters[tablename],
                                                row.filter_string)
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

    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    FATAL = "fatal"

    IN = "incoming"
    OUT = "outgoing"
    PULL = "pull"
    PUSH = "push"

    NONE = "none"

    # -------------------------------------------------------------------------
    def apply_method(self, r, **attr):
        """
            RESTful method handler

            @param r: the S3Request instance
            @param attr: controller attributes for the request
        """

        output = dict()

        resource = r.resource
        if resource.tablename == "sync_log":
            return resource.crud.select(r, **attr)
        elif resource.tablename == "sync_repository":
            # READ for sync log for this repository
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
                s3.actions = [
                    dict(label=str(current.T("Details")),
                         _class="action-btn",
                         url=URL(c="sync", f="log",
                                 args=["[id]"],
                                 vars={"return":here}))
                    ]
                output = r(subtitle=None,
                           rheader=self.rheader)
            else:
                r.error(501, current.ERROR.BAD_FORMAT)

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
            @param action: action taken to resolve errors (if any)
            @param result: the result of the transaction
                           (SUCCESS, WARNING, ERROR or FATAL)
            @param remote: boolean, True if this is a remote error
            @param message: clear text message
        """

        if result not in (cls.SUCCESS,
                          cls.WARNING,
                          cls.ERROR,
                          cls.FATAL):
            result = cls.SUCCESS

        if transmission not in (cls.IN, cls.OUT):
            transmission = cls.NONE
        if mode not in (cls.PULL, cls.PUSH):
            mode = cls.NONE

        mode = "%s/%s" % (mode, transmission)

        if not action:
            action = cls.NONE

        now = datetime.datetime.utcnow()
        entry = Storage(timestmp=now,
                        repository_id=repository_id,
                        resource_name=resource_name,
                        mode=mode,
                        action=action,
                        result=result,
                        remote=remote,
                        message=message)

        table = current.s3db[cls.TABLENAME]

        table.insert(**entry)
        return

    # -------------------------------------------------------------------------
    @staticmethod
    def rheader(r, **attr):

        if r.id is None:
            return DIV(current.T("Showing latest entries first"))
        else:
            return None

# =============================================================================
class S3SyncRepository(object):
    """ Class representation a peer repository """

    def __init__(self, repository):
        """
            Constructor

            @param repository: the repository record (Row)
        """

        self.log = S3SyncLog
        self._config = None

        self.id = repository.id
        self.name = repository.name
        self.url = repository.url
        self.username = repository.username
        self.password = repository.password
        self.client_id = repository.client_id
        self.client_secret = repository.client_secret
        self.site_key = repository.site_key
        self.refresh_token = repository.refresh_token
        self.proxy = repository.proxy
        self.apitype = repository.apitype

        import sync_adapter
        api = sync_adapter.__dict__.get(self.apitype)
        if api:
            adapter = api.S3SyncAdapter(self)
        else:
            adapter = S3SyncBaseAdapter(self)

        self.adapter = adapter

    # -------------------------------------------------------------------------
    @property
    def config(self):
        """
            Lazy access to synchronization settings
        """

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

# =============================================================================
class S3SyncBaseAdapter(object):

    def __init__(self, repository):

        self.repository = repository
        self.log = repository.log

    # -------------------------------------------------------------------------
    def register(self):

        raise NotImplementedError

    # -------------------------------------------------------------------------
    def login(self):

        raise NotImplementedError

    # -------------------------------------------------------------------------
    def pull(self, task, onconflict=None):

        raise NotImplementedError

    # -------------------------------------------------------------------------
    def push(self, task):

        raise NotImplementedError

# End =========================================================================
