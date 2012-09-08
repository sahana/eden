# -*- coding: utf-8 -*-

""" S3 Synchronization

    @author: Dominic König <dominic[at]aidiq[dot]com>

    @copyright: 2011-12 (c) Sahana Software Foundation
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

__all__ = ["S3Sync", "S3SyncLog"]

import sys
import urllib2
import datetime
import time

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

from s3rest import S3Method
from s3import import S3ImportItem

DEBUG = False
if DEBUG:
    print >> sys.stderr, "S3SYNC: DEBUG MODE"

    def _debug(m):
        print >> sys.stderr, m
else:
    _debug = lambda m: None

# =============================================================================

class S3Sync(S3Method):
    """ S3 Synchronization Toolkit """

    # -------------------------------------------------------------------------
    def __init__(self):
        """
            Constructor, initializes the Logger
        """

        S3Method.__init__(self)
        self.log = S3SyncLog()

    # -------------------------------------------------------------------------
    def apply_method(self, r, **attr):
        """
            RESTful method handler

            @param r: the S3Request instance
            @param attr: controller attributes for the request
        """

        output = dict()

        if r.method == "sync":
            if r.http == "GET":
                output = self.__send(r, **attr)
            elif r.http in ("PUT", "POST"):
                output = self.__receive(r, **attr)
            else:
                r.error(405, current.manager.ERROR.BAD_METHOD)
        elif r.name == "repository" and r.method == "register":
            if r.http == "GET":
                output = self.__register(r, **attr)
            else:
                r.error(405, current.manager.ERROR.BAD_METHOD)
        else:
            r.error(405, current.manager.ERROR.BAD_METHOD)

        return output

    # -------------------------------------------------------------------------
    def get_status(self):
        """
            Read the current sync status
        """

        table = current.s3db.sync_status
        row = current.db().select(table.ALL, limitby=(0, 1)).first()
        if not row:
            row = Storage()
        return row

    # -------------------------------------------------------------------------
    def set_status(self, **attr):
        """
            Update the current sync status
        """

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
        """
            Read the sync settings, avoid repeated DB lookups
        """

        if not hasattr(self, "config"):

            table = current.s3db.sync_config
            row = current.db().select(table.ALL, limitby=(0, 1)).first()
            self.config = row

        return self.config

    # -------------------------------------------------------------------------
    def synchronize(self, repository):
        """
            Synchronize a repository

            @param repository: a sync_repository row
        """

        _debug("S3Sync.synchronize(%s)" % repository.url)

        if not repository.url:
            message = "No URL set for repository"
            self.log.write(repository_id=repository.id,
                           resource_name=None,
                           transmission=None,
                           mode=None,
                           action="connect",
                           remote=False,
                           result=self.log.FATAL,
                           message=message)
            return current.xml.json_message(False, 400, message=message)

        rtable = current.s3db.sync_task
        query = (rtable.repository_id == repository.id) & \
                (rtable.deleted != True)
        tasks = current.db(query).select()
        for task in tasks:

            # Pull
            mtime = None
            if task.mode in (1, 3):
                error, mtime = self.__pull(repository, task)
            if error:
                _debug("S3Sync.synchronize: %s PULL error %s" %
                                    (task.resource_name, error))
                continue
            if mtime is not None:
                task.update_record(last_pull=mtime)

            # Push
            mtime = None
            if task.mode in (2, 3):
                error, mtime = self.__push(repository, task)
            if error:
                _debug("S3Sync.synchronize: %s PUSH error %s" %
                                    (task.resource_name, error))
                continue
            if mtime is not None:
                task.update_record(last_push=mtime)

            _debug("S3Sync.synchronize: %s success" % task.resource_name)

        # Success
        return current.xml.json_message()

    # -------------------------------------------------------------------------
    def __pull(self, repository, task):
        """
            Outgoing pull

            @param repository: the repository (sync_repository row)
            @param task: the task (sync_task row)
        """

        ignore_errors = True
        manager = current.manager
        xml = current.xml

        resource_name = task.resource_name

        _debug("S3Sync.__pull(%s, %s)" % (repository.url, resource_name))

        # Construct the URL
        config = self.__get_config()
        proxy = repository.proxy or config.proxy or None
        url = "%s/sync/sync.xml?resource=%s&repository=%s" % \
              (repository.url, resource_name, config.uuid)

        username = repository.username
        password = repository.password
        last_pull = task.last_pull

        # Get the target resource for this task
        resource = current.s3db.resource(resource_name)

        # Add msince and deleted to the URL
        if last_pull and task.update_policy not in ("THIS", "OTHER"):
            url += "&msince=%s" % xml.encode_iso_datetime(last_pull)
        url += "&include_deleted=True"

        _debug("...pull from URL %s" % url)

        response = None
        url_split = url.split("://", 1)
        if len(url_split) == 2:
            protocol, path = url_split
        else:
            protocol, path = "http", None

        # Prepare the request
        import urllib2
        req = urllib2.Request(url=url)
        handlers = []

        # Proxy handling
        if proxy:
            _debug("using proxy=%s" % proxy)
            proxy_handler = urllib2.ProxyHandler({protocol: proxy})
            handlers.append(proxy_handler)

        # Authentication handling
        if username and password:
            # Send auth data unsolicitedly (the only way with Eden instances):
            import base64
            base64string = base64.encodestring('%s:%s' %
                                               (username, password))[:-1]
            req.add_header("Authorization", "Basic %s" % base64string)
            # Just in case the peer does not accept that, add a 401 handler:
            passwd_manager = urllib2.HTTPPasswordMgrWithDefaultRealm()
            passwd_manager.add_password(realm=None,
                                        uri=url,
                                        user=username,
                                        passwd=password)
            auth_handler = urllib2.HTTPBasicAuthHandler(passwd_manager)
            handlers.append(auth_handler)

        # Install all handlers
        if handlers:
            opener = urllib2.build_opener(*handlers)
            urllib2.install_opener(opener)

        remote = False
        output = None
        response = None

        # Execute the request
        try:
            f = urllib2.urlopen(req)
        except urllib2.HTTPError, e:
            result = self.log.ERROR
            remote = True # Peer error
            code = e.code
            message = e.read()
            try:
                # Sahana-Eden would send a JSON message,
                # try to extract the actual error message:
                message_json = json.loads(message)
                message = message_json.get("message", message)
            except:
                pass
            # Prefix as peer error and strip XML markup from the message
            # @todo: better method to do this?
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
            output = xml.json_message(False, code, message, tree=None)
        except:
            result = self.log.FATAL
            code = 400
            message = sys.exc_info()[1]
            output = xml.json_message(False, code, message)
        else:
            result = self.log.SUCCESS
            response = f

        # Get import strategy and update policy
        strategy = task.strategy
        update_policy = task.update_policy
        conflict_policy = task.conflict_policy

        # Try to import the response
        count = 0
        mtime = None
        if response:
            success = True
            message = ""
            try:
                import_xml = resource.import_xml
                onconflict = lambda item: \
                             self.__resolve_conflict(item,
                                                     repository,
                                                     resource)
                success = import_xml(response,
                                     ignore_errors=ignore_errors,
                                     strategy=strategy,
                                     update_policy=update_policy,
                                     conflict_policy=conflict_policy,
                                     last_sync=last_pull,
                                     onconflict=onconflict)
                count = resource.import_count
            except IOError, e:
                result = self.log.FATAL
                message = "%s" % e
                output = xml.json_message(False, 400, message)

            mtime = resource.mtime
            if resource.error_tree is not None:
                # Validation error (log in any case)
                result = self.log.WARNING
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

            if not success:
                result = self.log.FATAL
                if not message:
                    error = manager.error
                    message = "%s" % error
                output = xml.json_message(False, 400, message)
                mtime = None

            elif not message:
                message = "data imported successfully (%s records)" % count

        elif result == self.log.SUCCESS:
            result = self.log.ERROR
            remote = True
            message = "no data received from peer"

        # log the operation
        self.log.write(repository_id=repository.id,
                       resource_name=task.resource_name,
                       transmission=self.log.OUT,
                       mode=self.log.PULL,
                       action=None,
                       remote=remote,
                       result=result,
                       message=message)

        _debug("S3Sync.__pull import %s: %s" % (result, message))
        return (output, mtime)

    # -------------------------------------------------------------------------
    def __push(self, repository, task):
        """
            Outgoing push

           @param repository: a sync_repository row
           @param task: a sync_task row
         """

        manager = current.manager
        xml = current.xml

        resource_name = task.resource_name

        _debug("S3Sync.__push(%s, %s)" % (repository.url, resource_name))

        # Construct the URL
        config = self.__get_config()
        proxy = repository.proxy or config.proxy or None
        url = "%s/sync/sync.xml?resource=%s&repository=%s" % \
              (repository.url, resource_name, config.uuid)

        username = repository.username
        password = repository.password

        strategy = task.strategy
        if strategy:
            url += "&strategy=%s" % ",".join(strategy)
        update_policy = task.update_policy
        if update_policy:
            url += "&update_policy=%s" % update_policy
        conflict_policy = task.conflict_policy
        if conflict_policy:
            url += "&conflict_policy=%s" % conflict_policy
        last_push = task.last_push
        if last_push and update_policy not in ("THIS", "OTHER"):
            url += "&msince=%s" % xml.encode_iso_datetime(last_push)
        else:
            last_push = None

        _debug("...push to URL %s" % url)

        # Export the resource as S3XML
        resource = current.s3db.resource(resource_name,
                                         include_deleted=True)
        data = resource.export_xml(msince=last_push)
        count = resource.results or 0
        mtime = resource.muntil

        remote = False
        output = None

        if data and count:
            # Find the protocol
            url_split = url.split("://", 1)
            if len(url_split) == 2:
                protocol, path = url_split
            else:
                protocol, path = "http", None

            # Generate the request
            import urllib2
            req = urllib2.Request(url=url, data=data)
            req.add_header('Content-Type', "text/xml")

            handlers = []
            if proxy:
                # Proxy handling
                _debug("using proxy=%s" % proxy)
                proxy_handler = urllib2.ProxyHandler({protocol: proxy})
                handlers.append(proxy_handler)
            if username and password:
                # Authentication handling:
                # send auth credentials unsolicitedly
                import base64
                base64string = base64.encodestring('%s:%s' %
                                                   (username, password))[:-1]
                req.add_header("Authorization", "Basic %s" % base64string)
                # Just in case the peer does not accept that
                # => add a 401 handler:
                passwd_manager = urllib2.HTTPPasswordMgrWithDefaultRealm()
                passwd_manager.add_password(realm=None,
                                            uri=url,
                                            user=username,
                                            passwd=password)
                auth_handler = urllib2.HTTPBasicAuthHandler(passwd_manager)
                handlers.append(auth_handler)
            # Install all handlers
            if handlers:
                opener = urllib2.build_opener(*handlers)
                urllib2.install_opener(opener)

            # Execute the request
            try:
                f = urllib2.urlopen(req)
            except urllib2.HTTPError, e:
                result = self.log.FATAL
                remote = True # Peer error
                code = e.code
                message = e.read()
                try:
                    # Sahana-Eden would send a JSON message,
                    # try to extract the actual error message:
                    message_json = json.loads(message)
                    message = message_json.get("message", message)
                except:
                    pass
                output = xml.json_message(False, code, message)
            except:
                result = self.log.FATAL
                code = 400
                message = sys.exc_info()[1]
                output = xml.json_message(False, code, message)
            else:
                result = self.log.SUCCESS
                message = "data sent successfully (%s records)" % count
        else:
            # No data to send
            result = self.log.WARNING
            message = "No data to send"

        # log the operation
        self.log.write(repository_id=repository.id,
                       resource_name=task.resource_name,
                       transmission=self.log.OUT,
                       mode=self.log.PUSH,
                       action=None,
                       remote=remote,
                       result=result,
                       message=message)

        if output is not None:
            mtime = None
        return (output, mtime)

    # -------------------------------------------------------------------------
    def __register(self, r, **attr):
        """
            Peer auto-registration, passive

            @param r: the S3Request
            @param attr: the controller attributes
        """

        result = self.log.SUCCESS
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
                    result = self.log.ERROR
                    message = "registration failed"
        else:
            result = self.log.ERROR
            message = "no repository identifier specified"

        if result == self.log.SUCCESS:
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
        self.log.write(repository_id=repository_id,
                       resource_name=self.log.NONE,
                       transmission=self.log.IN,
                       mode=self.log.PUSH,
                       action="register repository",
                       result=result,
                       message=message)

        return output

    # -------------------------------------------------------------------------
    def request_registration(self, repository):
        """
            Send out a registration request to a peer repository

            @param repository: a sync_repository row
         """

        xml = current.xml

        if not repository.url:
            return True

        _debug("S3Sync.request_registration(%s)" % (repository.url))

        # Construct the URL
        config = self.__get_config()
        proxy = repository.proxy or config.proxy or None
        url = "%s/sync/repository/register.xml?repository=%s" % \
              (repository.url, config.uuid)
        _debug("...send to URL %s" % url)

        username = repository.username
        password = repository.password

        # Generate the request
        import urllib2
        req = urllib2.Request(url=url)
        handlers = []
        if proxy:
            proxy_handler = urllib2.ProxyHandler({"http": proxy})
            handlers.append(proxy_handler)
        if username and password:
            import base64
            base64string = base64.encodestring('%s:%s' %
                                               (username, password))[:-1]
            req.add_header("Authorization", "Basic %s" % base64string)
            passwd_manager = urllib2.HTTPPasswordMgrWithDefaultRealm()
            passwd_manager.add_password(realm=None,
                                        uri=url,
                                        user=username,
                                        passwd=password)
            auth_handler = urllib2.HTTPBasicAuthHandler(passwd_manager)
            handlers.append(auth_handler)
        if handlers:
            opener = urllib2.build_opener(*handlers)
            urllib2.install_opener(opener)

        # Execute the request
        success = True
        remote = False
        try:
            f = urllib2.urlopen(req)
        except urllib2.HTTPError, e:
            result = self.log.FATAL
            remote = True # Peer error
            code = e.code
            message = e.read()
            success = False
            try:
                message_json = json.loads(message)
                message = message_json.get("message", message)
            except:
                pass
        except:
            result = self.log.FATAL
            code = 400
            message = sys.exc_info()[1]
            success = False
        else:
            ruid = None
            message = f.read()
            try:
                message_json = json.loads(message)
                message = message_json.get("message", message)
                ruid = message_json.get("sender", None)
            except:
                message = "registration successful"
            result = self.log.SUCCESS
            if ruid is not None:
                db = current.db
                rtable = current.s3db.sync_repository
                try:
                    db(rtable.id == repository.id).update(uuid=ruid)
                except:
                    pass

        # Log the operation
        self.log.write(repository_id=repository.id,
                       transmission=self.log.OUT,
                       mode=self.log.PUSH,
                       action="request registration",
                       remote=remote,
                       result=result,
                       message=message)

        return success

    # -------------------------------------------------------------------------
    def __send(self, r, **attr):
        """
            Respond to an incoming pull

            @param r: the S3Request
            @param attr: the controller attributes
        """

        _debug("S3Sync.__send")

        # Identify the requesting repository
        repository = Storage(id=None)
        if "repository" in r.vars:
            ruid = r.vars["repository"]
            rtable = current.s3db.sync_repository
            row = current.db(rtable.uuid == ruid).select(limitby=(0, 1)).first()
            if row:
                repository = row

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

        # Export the resource
        resource = r.resource
        output = resource.export_xml(start=start,
                                     limit=limit,
                                     msince=msince)
        count = resource.results

        # Set content type header
        headers = current.response.headers
        headers["Content-Type"] = "text/xml"

        # Log the operation
        self.log.write(repository_id=repository.id,
                       resource_name=r.resource.tablename,
                       transmission=self.log.IN,
                       mode=self.log.PULL,
                       result=self.log.SUCCESS,
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
            r.error(403, current.manager.ERROR.NOT_PERMITTED)

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
        onconflict = lambda item: \
                     self.__resolve_conflict(item, repository, resource)
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

        if resource.error_tree is not None:
            # Validation error (log in any case)
            if ignore_errors:
                result = self.log.WARNING
            else:
                result = self.log.FATAL
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
        else:
            result = self.log.SUCCESS
            message = "data received from peer"

        self.log.write(repository_id=repository.id,
                       resource_name=resource.tablename,
                       transmission=self.log.IN,
                       mode=self.log.PUSH,
                       result=result,
                       message=message)

        return output

    # -------------------------------------------------------------------------
    def __resolve_conflict(self, item, repository, resource):
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
                if task.conflict_policy == policies.OTHER:
                    # Always accept
                    _debug("Accept by default")
                    item.conflict = False
                elif task.conflict_policy == policies.NEWER:
                    # Accept if newer
                    xml = current.xml
                    if xml.MTIME in original and \
                       xml.as_utc(original[xml.MTIME]) <= item.mtime:
                        _debug("Accept because newer")
                        item.conflict = False
                    else:
                        _debug("Do not accept")
                elif task.conflict_policy == policies.MASTER:
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
                r.error(501, current.manager.ERROR.BAD_FORMAT)

        return output

    # -------------------------------------------------------------------------
    def write(self,
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

        if result not in (self.SUCCESS,
                          self.WARNING,
                          self.ERROR,
                          self.FATAL):
            result = self.SUCCESS

        if transmission not in (self.IN, self.OUT):
            transmission = self.NONE
        if mode not in (self.PULL, self.PUSH):
            mode = self.NONE

        mode = "%s/%s" % (mode, transmission)

        if not action:
            action = self.NONE

        now = datetime.datetime.utcnow()
        entry = Storage(timestmp=now,
                        repository_id=repository_id,
                        resource_name=resource_name,
                        mode=mode,
                        action=action,
                        result=result,
                        remote=remote,
                        message=message)

        table = current.s3db[self.TABLENAME]

        table.insert(**entry)
        return

    # -------------------------------------------------------------------------
    @staticmethod
    def rheader(r, **attr):

        if r.id is None:
            return DIV(current.T("Showing latest entries first"))
        else:
            return None

# End =========================================================================
