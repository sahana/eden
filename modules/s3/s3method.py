# -*- coding: utf-8 -*-

""" S3 Method Handler base class for the RESTful API

    @see: U{B{I{S3XRC}} <http://eden.sahanafoundation.org/wiki/S3XRC>}

    @requires: U{B{I{gluon}} <http://web2py.com>}

    @copyright: 2009-2012 (c) Sahana Software Foundation
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

__all__ = ["S3Method"]

import os
from gluon import current

# =============================================================================
class S3Method(object):
    """
        REST Method Handler Base Class

        Method handler classes should inherit from this class and
        implement the apply_method() method.

        @note: instances of subclasses don't have any of the instance
               attributes available until they actually get invoked
               from a request - i.e. apply_method() should never be
               called directly.
    """

    # -------------------------------------------------------------------------
    def __call__(self, r, method=None, **attr):
        """
            Entry point for the REST interface

            @param r: the S3Request
            @param method: the method established by the REST interface
            @param attr: dict of parameters for the method handler

            @returns: output object to send to the view
        """

        # Environment of the request
        self.request = r
        manager = current.manager

        # Settings
        self.permit = manager.permit
        self.download_url = manager.s3.download_url

        # Init
        self.next = None

        # Override request method
        if method is not None:
            self.method = method
        else:
            self.method = r.method

        # Find the target resource and record
        if r.component:
            component = r.component
            self.resource = component
            self.record_id = self._record_id(r)
            if not self.method:
                if r.multiple and not r.component_id:
                    self.method = "list"
                else:
                    self.method = "read"
            if component.link:
                actuate_link = r.actuate_link()
                if not actuate_link:
                    self.resource = component.link
        else:
            self.record_id = r.id
            self.resource = r.resource
            if not self.method:
                if r.id or r.method in ("read", "display"):
                    self.method = "read"
                else:
                    self.method = "list"

            ## In interactive single-record CRUD, open the
            ## instance record instead of a super-entity record
            #if r.interactive and \
               #self.record_id and \
               #self.method in ("read", "update") and \
               #self.resource.table._id.name != "id":
                #record = self.resource[self.record_id]
                #tablename = record.instance_type
                #prefix, name = tablename.split("_", 1)
                #resource = manager.define_resource(prefix, name,
                                                   #uid=record.uuid)
                #resource.load()
                #if resource.count() == 1:
                    #self.resource = resource
                    #self.record_id = resource.records().first()[resource.table._id]

        self.prefix = self.resource.prefix
        self.name = self.resource.name
        self.tablename = self.resource.tablename
        self.table = self.resource.table

        if self.method == "_init":
            return None

        # Apply method
        output = self.apply_method(r, **attr)

        # Redirection
        if self.next and self.resource.lastid:
            self.next = str(self.next)
            placeholder = "%5Bid%5D"
            self.next = self.next.replace(placeholder, self.resource.lastid)
            placeholder = "[id]"
            self.next = self.next.replace(placeholder, self.resource.lastid)
        if not current.response.error:
            r.next = self.next

        # Add additional view variables (e.g. rheader)
        self._extend_view(output, r, **attr)

        return output

    # -------------------------------------------------------------------------
    def apply_method(self, r, **attr):
        """
            Stub for apply_method, to be implemented in subclass

            @param r: the S3Request
            @param attr: dictionary of parameters for the method handler

            @returns: output object to send to the view
        """

        output = dict()
        return output

    # -------------------------------------------------------------------------
    # Utility functions
    # -------------------------------------------------------------------------
    def _permitted(self, method=None):
        """
            Check permission for the requested resource

            @param method: method to check, defaults to the actually
                           requested method
        """

        auth = current.auth
        has_permission = auth.s3_has_permission

        r = self.request

        table = mtable = r.table
        record_id = r.id

        if not method:
            method = self.method
        if method == "list":
            # Rest handled in S3Permission.METHODS
            method = "read"

        if r.component is not None:
            table = ctable = r.component.table
            record_id = r.component_id
            master_access = True
            if method in ("create", "update", "delete"):
                is_owner = auth.permission.is_owner
                if is_owner(ctable, record=record_id):
                    master_access = True
                else:
                    # User must have update permission on the master record
                    master_access = has_permission("update",
                                                   mtable, record_id=r.id)
                    if not master_access:
                        # ... or own the master record
                        master_access = is_owner(mtable, r.id)
            if not master_access:
                return False

        return has_permission(method, table, record_id=record_id)

    # -------------------------------------------------------------------------
    @staticmethod
    def _record_id(r):
        """
            Get the ID of the target record of a S3Request

            @param r: the S3Request
        """

        if r.component:
            # Component
            if not r.multiple and not r.component_id:
                resource = r.component
                table = resource.table
                pkey = table._id.name
                resource.load(start=0, limit=1)
                if len(resource):
                    r.component_id = resource.records().first()[pkey]
            component_id = r.component_id
            if not r.link:
                return component_id
            elif r.id and component_id:
                if r.actuate_link():
                    return component_id
                elif r.link_id:
                    return r.link_id
        else:
            # Master record
            return r.id

        return None

    # -------------------------------------------------------------------------
    def _config(self, key, default=None):
        """
            Get a configuration setting of the current table

            @param key: the setting key
            @param default: the default value
        """

        return current.s3db.get_config(self.tablename, key, default)

    # -------------------------------------------------------------------------
    @staticmethod
    def _view(r, default, format=None):
        """
            Get the path to the view stylesheet file

            @param r: the S3Request
            @param default: name of the default view stylesheet file
            @param format: format string (optional)
        """

        request = r
        folder = request.folder
        prefix = request.controller

        if r.component:
            view = "%s_%s_%s" % (r.name, r.component_name, default)
            path = os.path.join(folder, "views", prefix, view)
            if os.path.exists(path):
                return "%s/%s" % (prefix, view)
            else:
                view = "%s_%s" % (r.name, default)
                path = os.path.join(folder, "views", prefix, view)
        else:
            if format:
                view = "%s_%s_%s" % (r.name, default, format)
            else:
                view = "%s_%s" % (r.name, default)
            path = os.path.join(folder, "views", prefix, view)

        if os.path.exists(path):
            return "%s/%s" % (prefix, view)
        else:
            if format:
                return default.replace(".html", "_%s.html" % format)
            else:
                return default

    # -------------------------------------------------------------------------
    @staticmethod
    def _extend_view(output, r, **attr):
        """
            Add additional view variables (invokes all callables)

            @param output: the output dict
            @param r: the S3Request
            @param attr: the view variables (e.g. 'rheader')

            @note: overload this method in subclasses if you don't want
                   additional view variables to be added automatically
        """

        if r.interactive and isinstance(output, dict):
            for key in attr:
                handler = attr[key]
                if callable(handler):
                    resolve = True
                    try:
                        display = handler(r)
                    except TypeError:
                        # Argument list failure
                        # => pass callable to the view as-is
                        display = handler
                        continue
                    except:
                        # Propagate all other errors to the caller
                        raise
                else:
                    display = handler
                if isinstance(display, dict) and resolve:
                    output.update(**display)
                elif display is not None:
                    output.update(**{key: display})
                elif key in output and callable(handler):
                    del output[key]

# END =========================================================================
