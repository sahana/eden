# -*- coding: utf-8 -*-

""" S3 RESTful API

    @copyright: 2009-2014 (c) Sahana Software Foundation
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

__all__ = ("S3Request",
           "S3Method",
           "s3_request",
           )

import datetime
import os
import re
import sys
import time
import types
try:
    from cStringIO import StringIO    # Faster, where available
except:
    from StringIO import StringIO

try:
    import json # try stdlib (Python 2.6)
except ImportError:
    try:
        import simplejson as json # try external module
    except:
        import gluon.contrib.simplejson as json # fallback to pure-Python module

from gluon import *
# Here are dependencies listed for reference:
#from gluon.dal import Field
#from gluon.globals import current
#from gluon.html import A, DIV, URL
#from gluon.http import HTTP, redirect
#from gluon.validators import IS_EMPTY_OR, IS_NOT_IN_DB, IS_DATE, IS_TIME
from gluon.storage import Storage

from s3resource import S3Resource
from s3utils import s3_get_extension, s3_remove_last_record_id, s3_store_last_record_id

REGEX_FILTER = re.compile(".+\..+|.*\(.+\).*")

DEBUG = False
if DEBUG:
    print >> sys.stderr, "S3REST: DEBUG MODE"
    def _debug(m):
        print >> sys.stderr, m
else:
    _debug = lambda m: None

# =============================================================================
class S3Request(object):
    """
        Class to handle RESTful requests
    """

    INTERACTIVE_FORMATS = ("html", "iframe", "popup", "dl")
    DEFAULT_REPRESENTATION = "html"

    # -------------------------------------------------------------------------
    def __init__(self,
                 prefix=None,
                 name=None,
                 r=None,
                 c=None,
                 f=None,
                 args=None,
                 vars=None,
                 extension=None,
                 get_vars=None,
                 post_vars=None,
                 http=None):
        """
            Constructor

            @param prefix: the table name prefix
            @param name: the table name
            @param c: the controller prefix
            @param f: the controller function
            @param args: list of request arguments
            @param vars: dict of request variables
            @param extension: the format extension (representation)
            @param get_vars: the URL query variables (overrides vars)
            @param post_vars: the POST variables (overrides vars)
            @param http: the HTTP method (GET, PUT, POST, or DELETE)

            @note: all parameters fall back to the attributes of the
                   current web2py request object
        """

        # Common settings

        # XSLT Paths
        self.XSLT_PATH = "static/formats"
        self.XSLT_EXTENSION = "xsl"

        # Attached files
        self.files = Storage()

        # Allow override of controller/function
        self.controller = c or self.controller
        self.function = f or self.function
        if "." in self.function:
            self.function, ext = self.function.split(".", 1)
            if extension is None:
                extension = ext
        if c or f:
            auth = current.auth
            if not auth.permission.has_permission("read",
                                                  c=self.controller,
                                                  f=self.function):
                auth.permission.fail()

        # Allow override of request args/vars
        if args is not None:
            if isinstance(args, (list, tuple)):
                self.args = args
            else:
                self.args = [args]
        if get_vars is not None:
            self.get_vars = get_vars
            self.vars = get_vars.copy()
            if post_vars is not None:
                self.vars.update(post_vars)
            else:
                self.vars.update(self.post_vars)
        if post_vars is not None:
            self.post_vars = post_vars
            if get_vars is None:
                self.vars = post_vars.copy()
                self.vars.update(self.get_vars)
        if get_vars is None and post_vars is None and vars is not None:
            self.vars = vars
            self.get_vars = vars
            self.post_vars = Storage()

        self.extension = extension or current.request.extension
        self.http = http or current.request.env.request_method

        # Main resource attributes
        if r is not None:
            if not prefix:
                prefix = r.prefix
            if not name:
                name = r.name
        self.prefix = prefix or self.controller
        self.name = name or self.function

        # Parse the request
        self.__parse()
        self.custom_action = None
        get_vars = Storage(self.get_vars)

        # Interactive representation format?
        self.interactive = self.representation in self.INTERACTIVE_FORMATS

        # Show information on deleted records?
        include_deleted = False
        if self.representation == "xml" and "include_deleted" in get_vars:
            include_deleted = True
        if "components" in get_vars:
            cnames = get_vars["components"]
            if isinstance(cnames, list):
                cnames = ",".join(cnames)
            cnames = cnames.split(",")
            if len(cnames) == 1 and cnames[0].lower() == "none":
                cnames = []
        else:
            cnames = None

        # Append component ID to the URL query
        component_name = self.component_name
        component_id = self.component_id
        if component_name and component_id:
            varname = "%s.id" % component_name
            if varname in get_vars:
                var = get_vars[varname]
                if not isinstance(var, (list, tuple)):
                    var = [var]
                var.append(component_id)
                get_vars[varname] = var
            else:
                get_vars[varname] = component_id

        # Define the target resource
        _filter = current.response.s3.filter
        components = component_name
        if components is None:
            components = cnames

        if self.method == "review":
            approved, unapproved = False, True
        else:
            approved, unapproved = True, False

        tablename = "%s_%s" % (self.prefix, self.name)
        self.resource = S3Resource(tablename,
                                   id=self.id,
                                   filter=_filter,
                                   vars=get_vars,
                                   components=components,
                                   approved=approved,
                                   unapproved=unapproved,
                                   include_deleted=include_deleted,
                                   context=True,
                                   filter_component=component_name,
                                   )

        self.tablename = self.resource.tablename
        table = self.table = self.resource.table

        # Try to load the master record
        self.record = None
        uid = self.vars.get("%s.uid" % self.name)
        if self.id or uid and not isinstance(uid, (list, tuple)):
            # Single record expected
            self.resource.load()
            if len(self.resource) == 1:
                self.record = self.resource.records().first()
                _id = table._id.name
                self.id = self.record[_id]
                s3_store_last_record_id(self.tablename, self.id)
            else:
                error = current.ERROR.BAD_RECORD
                if self.representation == "html":
                    current.session.error = error
                    self.component = None # => avoid infinite loop
                    redirect(URL(r=current.request, c=self.controller))
                else:
                    raise KeyError(error)

        # Identify the component
        self.component = None
        self.pkey = None # @todo: deprecate
        self.fkey = None # @todo: deprecate
        self.multiple = True # @todo: deprecate

        if self.component_name:
            c = self.resource.components.get(self.component_name)
            if c:
                self.component = c
                self.pkey, self.fkey = c.pkey, c.fkey # @todo: deprecate
                self.multiple = c.multiple # @todo: deprecate
            else:
                error = "%s not a component of %s" % (self.component_name,
                                                      self.resource.tablename)
                raise SyntaxError(error)

        # Identify link table and link ID
        self.link = None
        self.link_id = None

        if self.component is not None:
            self.link = self.component.link
        if self.link and self.id and self.component_id:
            self.link_id = self.link.link_id(self.id, self.component_id)
            if self.link_id is None:
                error = current.ERROR.BAD_RECORD
                if self.representation == "html":
                    current.session.error = error
                    self.component = None # => avoid infinite loop
                    redirect(URL(r=current.request, c=self.controller))
                else:
                    raise KeyError(error)

        # Store method handlers
        self._handler = Storage()
        set_handler = self.set_handler
        set_handler("export_tree", self.get_tree,
                    http=["GET"], transform=True)
        set_handler("import_tree", self.put_tree,
                    http=["GET", "PUT", "POST"], transform=True)
        set_handler("fields", self.get_fields,
                    http=["GET"], transform=True)
        set_handler("options", self.get_options,
                    http=["GET"], transform=True)

        sync = current.sync
        set_handler("sync", sync,
                    http=["GET", "PUT", "POST"], transform=True)
        set_handler("sync_log", sync.log,
                    http=["GET"], transform=True)
        set_handler("sync_log", sync.log,
                    http=["GET"], transform=False)

        # Initialize CRUD
        self.resource.crud(self, method="_init")
        if self.component is not None:
            self.component.crud(self, method="_init")

    # -------------------------------------------------------------------------
    # Method handler configuration
    # -------------------------------------------------------------------------
    def set_handler(self, method, handler,
                    http=None,
                    representation=None,
                    transform=False):
        """
            Set a method handler for this request

            @param method: the method name
            @param handler: the handler function
            @type handler: handler(S3Request, **attr)
        """

        HTTP = ["GET", "PUT", "POST", "DELETE"]

        if http is None:
            http = HTTP
        if not isinstance(http, (list, tuple)):
            http = [http]
        if transform:
            representation = ["__transform__"]
        elif representation is None:
            representation = [self.DEFAULT_REPRESENTATION]
        if not isinstance(representation, (list, tuple)):
            representation = [representation]
        if not isinstance(method, (list, tuple)):
            method = [method]

        handlers = self._handler
        for h in http:
            if h not in HTTP:
                continue
            if h not in handlers:
                handlers[h] = Storage()
            format_hooks = handlers[h]
            for r in representation:
                if r not in format_hooks:
                    format_hooks[r] = Storage()
                method_hooks = format_hooks[r]
                for m in method:
                    if m is None:
                        _m = "__none__"
                    else:
                        _m = m
                    method_hooks[_m] = handler
        return

    # -------------------------------------------------------------------------
    def get_handler(self, method, transform=False):
        """
            Get a method handler for this request

            @param method: the method name
            @return: the handler function
        """

        http = self.http
        representation = self.representation

        if transform:
            representation = "__transform__"
        elif representation is None:
            representation = self.DEFAULT_REPRESENTATION
        if method is None:
            method = "__none__"

        if http not in self._handler:
            http = "GET"
        if http not in self._handler:
            return None
        else:
            format_hooks = self._handler[http]

        if representation not in format_hooks:
            representation = self.DEFAULT_REPRESENTATION
        if representation not in format_hooks:
            return None
        else:
            method_hooks = format_hooks[representation]

        if method not in method_hooks:
            method = "__none__"
        if method not in method_hooks:
            return None
        else:
            handler = method_hooks[method]
            if isinstance(handler, (type, types.ClassType)):
                return handler()
            else:
                return handler

    # -------------------------------------------------------------------------
    def get_widget_handler(self, method):
        """
            Get the widget handler for a method

            @param r: the S3Request
            @param method: the widget method
        """

        if self.component:
            resource = self.component
            if resource.link:
                resource = resource.link
        else:
            resource = self.resource
        prefix, name = self.prefix, self.name
        component_name = self.component_name

        custom_action = current.s3db.get_method(prefix,
                                                name,
                                                component_name=component_name,
                                                method=method)

        http = self.http
        handler = None

        if method and custom_action:
            handler = custom_action

        if http == "GET":
            if not method:
                if resource.count() == 1:
                    method = "read"
                else:
                    method = "list"
            transform = self.transformable()
            handler = self.get_handler(method, transform=transform)

        elif http == "PUT":
            transform = self.transformable(method="import")
            handler = self.get_handler(method, transform=transform)

        elif http == "POST":
            transform = self.transformable(method="import")
            return self.get_handler(method, transform=transform)

        elif http == "DELETE":
            if method:
                return self.get_handler(method)
            else:
                return self.get_handler("delete")

        else:
            return None

        if handler is None:
            handler = resource.crud
        if isinstance(handler, (type, types.ClassType)):
            handler = handler()
        return handler

    # -------------------------------------------------------------------------
    # Request Parser
    # -------------------------------------------------------------------------
    def __parse(self):
        """ Parses the web2py request object """

        self.id = None
        self.component_name = None
        self.component_id = None
        self.method = None

        representation = self.extension

        # Get the names of all components
        tablename = "%s_%s" % (self.prefix, self.name)
        components = current.s3db.get_components(tablename)
        if components:
            components = components.keys()
        else:
            components = []

        # Map request args, catch extensions
        f = []
        append = f.append
        args = self.args
        if len(args) > 4:
            args = args[:4]
        method = self.name
        for arg in args:
            if "." in arg:
                arg, representation = arg.rsplit(".", 1)
            if method is None:
                method = arg
            elif arg.isdigit():
                append((method, arg))
                method = None
            else:
                append((method, None))
                method = arg
        if method:
            append((method, None))

        self.id = f[0][1]

        # Sort out component name and method
        l = len(f)
        if l > 1:
            m = f[1][0].lower()
            i = f[1][1]
            if m in components:
                self.component_name = m
                self.component_id = i
            else:
                self.method = m
                if not self.id:
                    self.id = i
        if self.component_name and l > 2:
            self.method = f[2][0].lower()
            if not self.component_id:
                self.component_id = f[2][1]

        representation = s3_get_extension(self)
        if representation:
            self.representation = representation
        else:
            self.representation = self.DEFAULT_REPRESENTATION
        return

    # -------------------------------------------------------------------------
    # REST Interface
    # -------------------------------------------------------------------------
    def __call__(self, **attr):
        """
            Execute this request

            @param attr: Parameters for the method handler
        """

        response = current.response
        s3 = response.s3
        self.next = None

        bypass = False
        output = None
        preprocess = None
        postprocess = None

        representation = self.representation

        # Enforce primary record ID
        if not self.id and representation == "html":
            if self.component or self.method in ("read", "profile", "update"):
                count = self.resource.count()
                if self.vars is not None and count == 1:
                    self.resource.load()
                    self.record = self.resource._rows[0]
                    self.id = self.record.id
                else:
                    #current.session.error = current.ERROR.BAD_RECORD
                    redirect(URL(r=self, c=self.prefix, f=self.name))

        # Pre-process
        if s3 is not None:
            preprocess = s3.get("prep")
        if preprocess:
            pre = preprocess(self)
            # Re-read representation after preprocess:
            representation = self.representation
            if pre and isinstance(pre, dict):
                bypass = pre.get("bypass", False) is True
                output = pre.get("output")
                if not bypass:
                    success = pre.get("success", True)
                    if not success:
                        if representation == "html" and output:
                            if isinstance(output, dict):
                                output.update(r=self)
                            return output
                        else:
                            status = pre.get("status", 400)
                            message = pre.get("message",
                                              current.ERROR.BAD_REQUEST)
                            self.error(status, message)
            elif not pre:
                self.error(400, current.ERROR.BAD_REQUEST)

        # Default view
        if representation not in ("html", "popup"):
            response.view = "xml.html"

        # Content type
        response.headers["Content-Type"] = s3.content_type.get(representation,
                                                               "text/html")

        # Custom action?
        if not self.custom_action:
            action = current.s3db.get_method(self.prefix,
                                             self.name,
                                             component_name=self.component_name,
                                             method=self.method)
            if isinstance(action, (type, types.ClassType)):
                self.custom_action = action()
            else:
                self.custom_action = action

        # Method handling
        http = self.http
        handler = None
        if not bypass:
            # Find the method handler
            if self.method and self.custom_action:
                handler = self.custom_action
            elif http == "GET":
                handler = self.__GET()
            elif http == "PUT":
                handler = self.__PUT()
            elif http == "POST":
                handler = self.__POST()
            elif http == "DELETE":
                handler = self.__DELETE()
            else:
                self.error(405, current.ERROR.BAD_METHOD)
            # Invoke the method handler
            if handler is not None:
                output = handler(self, **attr)
            else:
                # Fall back to CRUD
                output = self.resource.crud(self, **attr)

        # Post-process
        if s3 is not None:
            postprocess = s3.get("postp")
        if postprocess is not None:
            output = postprocess(self, output)
        if output is not None and isinstance(output, dict):
            # Put a copy of r into the output for the view
            # to be able to make use of it
            output.update(r=self)

        # Redirection
        if self.next is not None and \
           (self.http != "GET" or self.method == "clear"):
            if isinstance(output, dict):
                form = output.get("form")
                if form:
                    if not hasattr(form, "errors"):
                        # Form embedded in a DIV together with other components
                        form = form.elements('form', first_only=True)
                        form = form[0] if form else None
                    if form and form.errors:
                        return output

            session = current.session
            session.flash = response.flash
            session.confirmation = response.confirmation
            session.error = response.error
            session.warning = response.warning
            redirect(self.next)

        return output

    # -------------------------------------------------------------------------
    def __GET(self, resource=None):
        """
            Get the GET method handler
        """

        method = self.method
        transform = False
        if method is None or method in ("read", "display", "update"):
            if self.transformable():
                method = "export_tree"
                transform = True
            elif self.component:
                resource = self.resource
                if self.interactive and resource.count() == 1:
                    # Load the record
                    if not resource._rows:
                        resource.load(start=0, limit=1)
                    if resource._rows:
                        self.record = resource._rows[0]
                        self.id = resource.get_id()
                        self.uid = resource.get_uid()
                if self.multiple and not self.component_id:
                    method = "list"
                else:
                    method = "read"
            elif self.id or method in ("read", "display", "update"):
                # Enforce single record
                resource = self.resource
                if not resource._rows:
                    resource.load(start=0, limit=1)
                if resource._rows:
                    self.record = resource._rows[0]
                    self.id = resource.get_id()
                    self.uid = resource.get_uid()
                else:
                    self.error(404, current.ERROR.BAD_RECORD)
                method = "read"
            else:
                method = "list"

        elif method in ("create", "update"):
            if self.transformable(method="import"):
                method = "import_tree"
                transform = True

        elif method == "delete":
            return self.__DELETE()

        elif method == "clear" and not self.component:
            s3_remove_last_record_id(self.tablename)
            self.next = URL(r=self, f=self.name)
            return lambda r, **attr: None

        elif self.transformable():
            transform = True

        return self.get_handler(method, transform=transform)

    # -------------------------------------------------------------------------
    def __PUT(self):
        """
            Get the PUT method handler
        """

        method = self.method
        transform = self.transformable(method="import")

        if not self.method and transform:
            method = "import_tree"

        return self.get_handler(method, transform=transform)

    # -------------------------------------------------------------------------
    def __POST(self):
        """
            Get the POST method handler
        """

        method = self.method

        if method == "delete":
            return self.__DELETE()
        else:
            if self.transformable(method="import"):
                return self.__PUT()
            else:
                post_vars = self.post_vars
                table = self.target()[2]
                if "deleted" in table and "id" not in post_vars: # and "uuid" not in post_vars:
                    original = S3Resource.original(table, post_vars)
                    if original and original.deleted:
                        self.post_vars.update(id=original.id)
                        self.vars.update(id=original.id)
                return self.__GET()

    # -------------------------------------------------------------------------
    def __DELETE(self):
        """
            Get the DELETE method handler
        """

        if self.method:
            return self.get_handler(self.method)
        else:
            return self.get_handler("delete")

    # -------------------------------------------------------------------------
    # Built-in method handlers
    # -------------------------------------------------------------------------
    @staticmethod
    def get_tree(r, **attr):
        """
            XML Element tree export method

            @param r: the S3Request instance
            @param attr: controller attributes
        """

        get_vars = r.get_vars
        args = Storage()

        # Slicing
        start = get_vars.get("start")
        if start is not None:
            try:
                start = int(start)
            except ValueError:
                start = None
        limit = get_vars.get("limit")
        if limit is not None:
            try:
                limit = int(limit)
            except ValueError:
                limit = None

        # msince
        msince = get_vars.get("msince")
        if msince is not None:
            tfmt = current.xml.ISOFORMAT
            try:
                (y, m, d, hh, mm, ss, t0, t1, t2) = \
                    time.strptime(msince, tfmt)
                msince = datetime.datetime(y, m, d, hh, mm, ss)
            except ValueError:
                msince = None

        # Show IDs (default: False)
        if "show_ids" in get_vars:
            if get_vars["show_ids"].lower() == "true":
                current.xml.show_ids = True

        # Show URLs (default: True)
        if "show_urls" in get_vars:
            if get_vars["show_urls"].lower() == "false":
                current.xml.show_urls = False

        # Maxbounds (default: False)
        maxbounds = False
        if "maxbounds" in get_vars:
            if get_vars["maxbounds"].lower() == "true":
                maxbounds = True
        if r.representation in ("gpx", "osm"):
            maxbounds = True

        # Components of the master resource (tablenames)
        if "mcomponents" in get_vars:
            mcomponents = get_vars["mcomponents"]
            if str(mcomponents).lower() == "none":
                mcomponents = None
            elif not isinstance(mcomponents, list):
                mcomponents = mcomponents.split(",")
        else:
            mcomponents = [] # all

        # Components of referenced resources (tablenames)
        if "rcomponents" in get_vars:
            rcomponents = get_vars["rcomponents"]
            if str(rcomponents).lower() == "none":
                rcomponents = None
            elif not isinstance(rcomponents, list):
                rcomponents = rcomponents.split(",")
        else:
            rcomponents = None

        # Maximum reference resolution depth
        if "maxdepth" in get_vars:
            try:
                args["maxdepth"] = int(get_vars["maxdepth"])
            except ValueError:
                pass

        # References to resolve (field names)
        if "references" in get_vars:
            references = get_vars["references"]
            if str(references).lower() == "none":
                references = []
            elif not isinstance(references, list):
                references = references.split(",")
        else:
            references = None # all

        # Export field selection
        if "fields" in get_vars:
            fields = get_vars["fields"]
            if str(fields).lower() == "none":
                fields = []
            elif not isinstance(fields, list):
                fields = fields.split(",")
        else:
            fields = None # all

        # Find XSLT stylesheet
        stylesheet = r.stylesheet()

        # Add stylesheet parameters
        if stylesheet is not None:
            if r.component:
                args.update(id=r.id,
                            component=r.component.tablename)
                if r.component.alias:
                    args.update(alias=r.component.alias)
            mode = get_vars.get("xsltmode")
            if mode is not None:
                args.update(mode=mode)

        # Set response headers
        response = current.response
        s3 = response.s3
        headers = response.headers
        representation = r.representation
        if representation in s3.json_formats:
            as_json = True
            default = "application/json"
        else:
            as_json = False
            default = "text/xml"
        headers["Content-Type"] = s3.content_type.get(representation,
                                                      default)

        # Export the resource
        output = r.resource.export_xml(start=start,
                                       limit=limit,
                                       msince=msince,
                                       fields=fields,
                                       dereference=True,
                                       # maxdepth in args
                                       references=references,
                                       mcomponents=mcomponents,
                                       rcomponents=rcomponents,
                                       stylesheet=stylesheet,
                                       as_json=as_json,
                                       maxbounds=maxbounds,
                                       **args)
        # Transformation error?
        if not output:
            r.error(400, "XSLT Transformation Error: %s " % current.xml.error)

        return output

    # -------------------------------------------------------------------------
    @staticmethod
    def put_tree(r, **attr):
        """
            XML Element tree import method

            @param r: the S3Request method
            @param attr: controller attributes
        """

        get_vars = r.get_vars

        # Skip invalid records?
        if "ignore_errors" in get_vars:
            ignore_errors = True
        else:
            ignore_errors = False

        # Find all source names in the URL vars
        def findnames(get_vars, name):
            nlist = []
            if name in get_vars:
                names = get_vars[name]
                if isinstance(names, (list, tuple)):
                    names = ",".join(names)
                names = names.split(",")
                for n in names:
                    if n[0] == "(" and ")" in n[1:]:
                        nlist.append(n[1:].split(")", 1))
                    else:
                        nlist.append([None, n])
            return nlist
        filenames = findnames(get_vars, "filename")
        fetchurls = findnames(get_vars, "fetchurl")
        source_url = None

        # Get the source(s)
        s3 = current.response.s3
        json_formats = s3.json_formats
        csv_formats = s3.csv_formats
        source = []
        format = r.representation
        if format in json_formats or format in csv_formats:
            if filenames:
                try:
                    for f in filenames:
                        source.append((f[0], open(f[1], "rb")))
                except:
                    source = []
            elif fetchurls:
                import urllib
                try:
                    for u in fetchurls:
                        source.append((u[0], urllib.urlopen(u[1])))
                except:
                    source = []
            elif r.http != "GET":
                source = r.read_body()
        else:
            if filenames:
                source = filenames
            elif fetchurls:
                source = fetchurls
                # Assume only 1 URL for GeoRSS feed caching
                source_url = fetchurls[0][1]
            elif r.http != "GET":
                source = r.read_body()
        if not source:
            if filenames or fetchurls:
                # Error: source not found
                r.error(400, "Invalid source")
            else:
                # No source specified => return resource structure
                return r.get_struct(r, **attr)

        # Find XSLT stylesheet
        stylesheet = r.stylesheet(method="import")
        # Target IDs
        if r.method == "create":
            _id = None
        else:
            _id = r.id

        # Transformation mode?
        if "xsltmode" in get_vars:
            args = dict(xsltmode=get_vars["xsltmode"])
        else:
            args = dict()
        # These 3 options are called by gis.show_map() & read by the
        # GeoRSS Import stylesheet to populate the gis_cache table
        # Source URL: For GeoRSS/KML Feed caching
        if source_url:
            args["source_url"] = source_url
        # Data Field: For GeoRSS/KML Feed popups
        if "data_field" in get_vars:
            args["data_field"] = get_vars["data_field"]
        # Image Field: For GeoRSS/KML Feed popups
        if "image_field" in get_vars:
            args["image_field"] = get_vars["image_field"]

        # Format type?
        if format in json_formats:
            format = "json"
        elif format in csv_formats:
            format = "csv"
        else:
            format = "xml"

        try:
            output = r.resource.import_xml(source,
                                           id=_id,
                                           format=format,
                                           files=r.files,
                                           stylesheet=stylesheet,
                                           ignore_errors=ignore_errors,
                                           **args)
        except IOError:
            current.auth.permission.fail()
        except SyntaxError:
            e = sys.exc_info()[1]
            if hasattr(e, "message"):
                e = e.message
            r.error(400, e)

        return output

    # -------------------------------------------------------------------------
    @staticmethod
    def get_struct(r, **attr):
        """
            Resource structure introspection method

            @param r: the S3Request instance
            @param attr: controller attributes
        """

        response = current.response
        json_formats = response.s3.json_formats
        if r.representation in json_formats:
            as_json = True
            content_type = "application/json"
        else:
            as_json = False
            content_type = "text/xml"
        get_vars = r.get_vars
        meta = str(get_vars.get("meta", False)).lower() == "true"
        opts = str(get_vars.get("options", False)).lower() == "true"
        refs = str(get_vars.get("references", False)).lower() == "true"
        stylesheet = r.stylesheet()
        output = r.resource.export_struct(meta=meta,
                                          options=opts,
                                          references=refs,
                                          stylesheet=stylesheet,
                                          as_json=as_json)
        if output is None:
            # Transformation error
            r.error(400, current.xml.error)
        response.headers["Content-Type"] = content_type
        return output

    # -------------------------------------------------------------------------
    @staticmethod
    def get_fields(r, **attr):
        """
            Resource structure introspection method (single table)

            @param r: the S3Request instance
            @param attr: controller attributes
        """

        representation = r.representation
        if representation == "xml":
            output = r.resource.export_fields(component=r.component_name)
            content_type = "text/xml"
        elif representation == "s3json":
            output = r.resource.export_fields(component=r.component_name,
                                              as_json=True)
            content_type = "application/json"
        else:
            r.error(501, current.ERROR.BAD_FORMAT)
        response = current.response
        response.headers["Content-Type"] = content_type
        return output

    # -------------------------------------------------------------------------
    @staticmethod
    def get_options(r, **attr):
        """
            Field options introspection method (single table)

            @param r: the S3Request instance
            @param attr: controller attributes
        """

        get_vars = r.get_vars
        if "field" in get_vars:
            items = get_vars["field"]
            if not isinstance(items, (list, tuple)):
                items = [items]
            fields = []
            add_fields = fields.extend
            for item in items:
                f = item.split(",")
                if f:
                    add_fields(f)
        else:
            fields = None

        if "hierarchy" in get_vars:
            hierarchy = get_vars["hierarchy"].lower() not in ("false", "0")
        else:
            hierarchy = False

        if "only_last" in get_vars:
            only_last = get_vars["only_last"].lower() not in ("false", "0")
        else:
            only_last = False

        if "show_uids" in get_vars:
            show_uids = get_vars["show_uids"].lower() not in ("false", "0")
        else:
            show_uids = False

        representation = r.representation
        if representation == "xml":
            only_last = False
            as_json = False
            content_type = "text/xml"
        elif representation == "s3json":
            show_uids = False
            as_json = True
            content_type = "application/json"
        else:
            r.error(501, current.ERROR.BAD_FORMAT)

        component = r.component_name
        output = r.resource.export_options(component=component,
                                           fields=fields,
                                           show_uids=show_uids,
                                           only_last=only_last,
                                           hierarchy=hierarchy,
                                           as_json=as_json)

        current.response.headers["Content-Type"] = content_type
        return output

    # -------------------------------------------------------------------------
    # Tools
    # -------------------------------------------------------------------------
    def factory(self, **args):
        """
            Generate a new request for the same resource

            @param args: arguments for request constructor
        """

        return s3_request(r=self, **args)

    # -------------------------------------------------------------------------
    def __getattr__(self, key):
        """
            Called upon S3Request.<key> - looks up the value for the <key>
            attribute. Falls back to current.request if the attribute is
            not defined in this S3Request.

            @param key: the key to lookup
        """

        if key in self.__dict__:
            return self.__dict__[key]

        sentinel = object()
        value = getattr(current.request, key, sentinel)
        if value is sentinel:
            raise AttributeError
        return value

    # -------------------------------------------------------------------------
    def transformable(self, method=None):
        """
            Check the request for a transformable format

            @param method: "import" for import methods, else None
        """

        if self.representation in ("html", "aadata", "popup", "iframe"):
            return False

        stylesheet = self.stylesheet(method=method, skip_error=True)

        if not stylesheet and self.representation != "xml":
            return False
        else:
            return True

    # -------------------------------------------------------------------------
    def actuate_link(self, component_id=None):
        """
            Determine whether to actuate a link or not

            @param component_id: the component_id (if not self.component_id)
        """

        if not component_id:
            component_id = self.component_id
        if self.component:
            single = component_id != None
            component = self.component
            if component.link:
                actuate = self.component.actuate
                if "linked" in self.get_vars:
                    linked = self.get_vars.get("linked", False)
                    linked = linked in ("true", "True")
                    if linked:
                        actuate = "replace"
                    else:
                        actuate = "hide"
                if actuate == "link":
                    if self.method != "delete" and self.http != "DELETE":
                        return single
                    else:
                        return not single
                elif actuate == "replace":
                    return True
                #elif actuate == "embed":
                    #raise NotImplementedError
                else:
                    return False
            else:
                return True
        else:
            return False

    # -------------------------------------------------------------------------
    @staticmethod
    def unauthorised():
        """
            Action upon unauthorised request
        """

        current.auth.permission.fail()

    # -------------------------------------------------------------------------
    def error(self, status, message, tree=None, next=None):
        """
            Action upon error

            @param status: HTTP status code
            @param message: the error message
            @param tree: the tree causing the error
        """

        if self.representation == "html":
            current.session.error = message
            if next is not None:
                redirect(next)
            else:
                redirect(URL(r=self, f="index"))
        else:
            headers = {"Content-Type":"application/json"}
            current.log.error(message)
            raise HTTP(status,
                       body=current.xml.json_message(success=False,
                                                     statuscode=status,
                                                     message=message,
                                                     tree=tree),
                       web2py_error=message,
                       **headers)

    # -------------------------------------------------------------------------
    def url(self,
            id=None,
            component=None,
            component_id=None,
            target=None,
            method=None,
            representation=None,
            vars=None,
            host=None):
        """
            Returns the URL of this request, use parameters to override
            current requests attributes:

                - None to keep current attribute (default)
                - 0 or "" to set attribute to NONE
                - value to use explicit value

            @param id: the master record ID
            @param component: the component name
            @param component_id: the component ID
            @param target: the target record ID (choose automatically)
            @param method: the URL method
            @param representation: the representation for the URL
            @param vars: the URL query variables
            @param host: string to force absolute URL with host (True means http_host)

            Particular behavior:
                - changing the master record ID resets the component ID
                - removing the target record ID sets the method to None
                - removing the method sets the target record ID to None
                - [] as id will be replaced by the "[id]" wildcard
        """

        if vars is None:
            vars = self.get_vars
        elif vars and isinstance(vars, str):
            # We've come from a dataTable_vars which has the vars as
            # a JSON string, but with the wrong quotation marks
            vars = json.loads(vars.replace("'", "\""))

        if "format" in vars:
            del vars["format"]

        args = []

        cname = self.component_name

        # target
        if target is not None:
            if cname and (component is None or component == cname):
                component_id = target
            else:
                id = target

        # method
        default_method = False
        if method is None:
            default_method = True
            method = self.method
        elif method == "":
            # Switch to list? (= method="" and no explicit target ID)
            if component_id is None:
                if self.component_id is not None:
                    component_id = 0
                elif not self.component:
                    if id is None:
                        if self.id is not None:
                            id = 0
            method = None

        # id
        if id is None:
            id = self.id
        elif id in (0, ""):
            id = None
        elif id in ([], "[id]", "*"):
            id = "[id]"
            component_id = 0
        elif str(id) != str(self.id):
            component_id = 0

        # component
        if component is None:
            component = cname
        elif component == "":
            component = None
        if cname and cname != component or not component:
            component_id = 0

        # component_id
        if component_id is None:
            component_id = self.component_id
        elif component_id == 0:
            component_id = None
            if self.component_id and default_method:
                method = None

        if id is None and self.id and \
           (not component or not component_id) and default_method:
            method = None

        if id:
            args.append(id)
        if component:
            args.append(component)
        if component_id:
            args.append(component_id)
        if method:
            args.append(method)

        # representation
        if representation is None:
            representation = self.representation
        elif representation == "":
            representation = self.DEFAULT_REPRESENTATION
        f = self.function
        if not representation == self.DEFAULT_REPRESENTATION:
            if len(args) > 0:
                args[-1] = "%s.%s" % (args[-1], representation)
            else:
                f = "%s.%s" % (f, representation)

        return URL(r=self,
                   c=self.controller,
                   f=f,
                   args=args,
                   vars=vars,
                   host=host)

    # -------------------------------------------------------------------------
    def target(self):
        """
            Get the target table of the current request

            @return: a tuple of (prefix, name, table, tablename) of the target
                resource of this request

            @todo: update for link table support
        """

        component = self.component
        if component is not None:
            link = self.component.link
            if link and not self.actuate_link():
                return(link.prefix,
                       link.name,
                       link.table,
                       link.tablename)
            return (component.prefix,
                    component.name,
                    component.table,
                    component.tablename)
        else:
            return (self.prefix,
                    self.name,
                    self.table,
                    self.tablename)

    # -------------------------------------------------------------------------
    def stylesheet(self, method=None, skip_error=False):
        """
            Find the XSLT stylesheet for this request

            @param method: "import" for data imports, else None
            @param skip_error: do not raise an HTTP error status
                               if the stylesheet cannot be found
        """

        stylesheet = None
        format = self.representation
        if self.component:
            resourcename = self.component.name
        else:
            resourcename = self.name

        # Native S3XML?
        if format == "xml":
            return stylesheet

        # External stylesheet specified?
        if "transform" in self.vars:
            return self.vars["transform"]

        # Stylesheet attached to the request?
        extension = self.XSLT_EXTENSION
        filename = "%s.%s" % (resourcename, extension)
        if filename in self.post_vars:
            p = self.post_vars[filename]
            import cgi
            if isinstance(p, cgi.FieldStorage) and p.filename:
                stylesheet = p.file
            return stylesheet

        # Internal stylesheet?
        folder = self.folder
        path = self.XSLT_PATH
        if method != "import":
            method = "export"
        filename = "%s.%s" % (method, extension)
        stylesheet = os.path.join(folder, path, format, filename)
        if not os.path.exists(stylesheet):
            if not skip_error:
                self.error(501, "%s: %s" % (current.ERROR.BAD_TEMPLATE,
                                            stylesheet))
            else:
                stylesheet = None

        return stylesheet

    # -------------------------------------------------------------------------
    def read_body(self):
        """
            Read data from request body
        """

        self.files = Storage()
        content_type = self.env.get("content_type")

        source = []
        if content_type and content_type.startswith("multipart/"):
            import cgi
            ext = ".%s" % self.representation
            post_vars = self.post_vars
            for v in post_vars:
                p = post_vars[v]
                if isinstance(p, cgi.FieldStorage) and p.filename:
                    self.files[p.filename] = p.file
                    if p.filename.endswith(ext):
                        source.append((v, p.file))
                elif v.endswith(ext):
                    if isinstance(p, cgi.FieldStorage):
                        source.append((v, p.value))
                    elif isinstance(p, basestring):
                        source.append((v, StringIO(p)))
        else:
            s = self.body
            s.seek(0)
            source.append(s)

        return source

    # -------------------------------------------------------------------------
    def customise_resource(self, tablename=None):
        """
            Invoke the customization callback for a resource.

            @param tablename: the tablename of the resource; if called
                              without tablename it will invoke the callbacks
                              for the target resources of this request:
                                - master
                                - active component
                                - active link table
                              (in this order)

            Resource customization functions can be defined like:

                def customise_resource_my_table(r, tablename):

                    current.s3db.configure(tablename,
                                           my_custom_setting = "example")
                    return

                settings.customise_resource_my_table = \
                                        customise_resource_my_table

            @note: the hook itself can call r.customise_resource in order
                   to cascade customizations as necessary
            @note: if a table is customised that is not currently loaded,
                   then it will be loaded for this process
        """

        if tablename is None:
            customise = self.customise_resource

            customise(self.resource.tablename)
            component = self.component
            if component:
                customise(component.tablename)
            link = self.link
            if link:
                customise(link.tablename)
        else:
            # Always load the model first (otherwise it would
            # override the custom settings when loaded later)
            db = current.db
            if tablename not in db:
                db.table(tablename)
            customise = current.deployment_settings.customise_resource(tablename)
            if customise:
                customise(self, tablename)
        return

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
    def __call__(self, r, method=None, widget_id=None, **attr):
        """
            Entry point for the REST interface

            @param r: the S3Request
            @param method: the method established by the REST interface
            @param widget_id: widget ID
            @param attr: dict of parameters for the method handler

            @return: output object to send to the view
        """

        # Environment of the request
        self.request = r

        # Settings
        response = current.response
        self.download_url = response.s3.download_url

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
            resource = component
            self.record_id = self._record_id(r)
            if not self.method:
                if r.multiple and not r.component_id:
                    self.method = "list"
                else:
                    self.method = "read"
            if component.link:
                actuate_link = r.actuate_link()
                if not actuate_link:
                    resource = component.link
        else:
            self.record_id = r.id
            resource = r.resource
            if not self.method:
                if r.id or r.method in ("read", "display"):
                    self.method = "read"
                else:
                    self.method = "list"

        self.prefix = resource.prefix
        self.name = resource.name
        self.tablename = resource.tablename
        self.table = resource.table
        self.resource = resource

        if self.method == "_init":
            return None

        if r.interactive:
            # hide_filter policy:
            #
            #   None            show filters on master,
            #                   hide for components (default)
            #   False           show all filters (on all tabs)
            #   True            hide all filters (on all tabs)
            #
            #   dict(alias=setting)     setting per component, alias
            #                           None means master resource,
            #                           use special alias _default
            #                           to specify an alternative
            #                           default
            #
            hide_filter = attr.get("hide_filter")
            if isinstance(hide_filter, dict):
                component_name = r.component_name
                if component_name in hide_filter:
                    hide_filter = hide_filter[component_name]
                elif "_default" in hide_filter:
                    hide_filter = hide_filter["_default"]
                else:
                    hide_filter = None
            if hide_filter is None:
                hide_filter = r.component is not None
            self.hide_filter = hide_filter
        else:
            self.hide_filter = True

        # Apply method
        if widget_id and hasattr(self, "widget"):
            output = self.widget(r,
                                 method=self.method,
                                 widget_id=widget_id,
                                 **attr)
        else:
            output = self.apply_method(r, **attr)

            # Redirection
            if self.next and resource.lastid:
                self.next = str(self.next)
                placeholder = "%5Bid%5D"
                self.next = self.next.replace(placeholder, resource.lastid)
                placeholder = "[id]"
                self.next = self.next.replace(placeholder, resource.lastid)
            if not response.error:
                r.next = self.next

            # Add additional view variables (e.g. rheader)
            self._extend_view(output, r, **attr)

        return output

    # -------------------------------------------------------------------------
    def apply_method(self, r, **attr):
        """
            Stub, to be implemented in subclass. This method is used
            to get the results as a standalone page.

            @param r: the S3Request
            @param attr: dictionary of parameters for the method handler

            @return: output object to send to the view
        """

        output = dict()
        return output

    # -------------------------------------------------------------------------
    def widget(self, r, method=None, widget_id=None, visible=True, **attr):
        """
            Stub, to be implemented in subclass. This method is used
            by other method handlers to embed this method as widget.

            @note:

                For "html" format, the widget method must return an XML
                component that can be embedded in a DIV. If a dict is
                returned, it will be rendered against the view template
                of the calling method - the view template selected by
                the widget method will be ignored.

                For other formats, the data returned by the widget method
                will be rendered against the view template selected by
                the widget method. If no view template is set, the data
                will be returned as-is.

                The widget must use the widget_id as HTML id for the element
                providing the Ajax-update hook and this element must be
                visible together with the widget.

                The widget must include the widget_id as ?w=<widget_id> in
                the URL query of the Ajax-update call, and Ajax-calls should
                not use "html" format.

                If visible==False, then the widget will initially be hidden,
                so it can be rendered empty and Ajax-load its data layer
                upon a separate refresh call. Otherwise, the widget should
                receive its data layer immediately. Widgets can ignore this
                parameter if delayed loading of the data layer is not
                all([possible, useful, supported]).

            @param r: the S3Request
            @param method: the URL method
            @param widget_id: the widget ID
            @param visible: whether the widget is initially visible
            @param attr: dictionary of parameters for the method handler

            @return: output
        """

        return None

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

        if not method:
            method = self.method
        if method in ("list", "datatable", "datalist"):
            # Rest handled in S3Permission.METHODS
            method = "read"

        if r.component is None:
            table = r.table
            record_id = r.id
        else:
            table = r.component.table
            record_id = r.component_id

            if method == "create":
                # Must have permission to update the master record
                # in order to create a new component record...
                master_access = has_permission("update",
                                               r.table,
                                               record_id=r.id)

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
    def _view(r, default):
        """
            Get the path to the view template

            @param r: the S3Request
            @param default: name of the default view template
        """

        folder = r.folder
        prefix = r.controller

        exists = os.path.exists
        join = os.path.join

        theme = current.deployment_settings.get_theme()
        if theme != "default":
            # See if there is a Custom View for this Theme
            view = join(folder, "private", "templates", theme, "views",
                        "%s_%s_%s" % (prefix, r.name, default))
            if exists(view):
                # There is a view specific to this page
                # NB This should normally include {{extend layout.html}}
                # Pass view as file not str to work in compiled mode
                return open(view, "rb")
            else:
                if "/" in default:
                    subfolder, _default = default.split("/", 1)
                else:
                    subfolder = ""
                    _default = default
                if exists(join(folder, "private", "templates", theme, "views",
                               subfolder, "_%s" % _default)):
                    # There is a general view for this page type
                    # NB This should not include {{extend layout.html}}
                    if subfolder:
                        subfolder = "%s/" % subfolder
                    # Pass this mapping to the View
                    current.response.s3.views[default] = \
                        "../private/templates/%s/views/%s_%s" % (theme,
                                                                 subfolder,
                                                                 _default)

        if r.component:
            view = "%s_%s_%s" % (r.name, r.component_name, default)
            path = join(folder, "views", prefix, view)
            if exists(path):
                return "%s/%s" % (prefix, view)
            else:
                view = "%s_%s" % (r.name, default)
                path = join(folder, "views", prefix, view)
        else:
            view = "%s_%s" % (r.name, default)
            path = join(folder, "views", prefix, view)

        if exists(path):
            return "%s/%s" % (prefix, view)
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
                    resolve = False
                    display = handler
                if isinstance(display, dict) and resolve:
                    output.update(**display)
                elif display is not None:
                    output.update(**{key: display})
                elif key in output and callable(handler):
                    del output[key]

    # -------------------------------------------------------------------------
    @staticmethod
    def _remove_filters(vars):
        """
            Remove all filters from URL vars

            @param vars: the URL vars as dict
        """

        return Storage((k, v) for k, v in vars.iteritems()
                              if not REGEX_FILTER.match(k))

    # -------------------------------------------------------------------------
    @staticmethod
    def crud_string(tablename, name):
        """
            Get a CRUD info string for interactive pages

            @param tablename: the table name
            @param name: the name of the CRUD string
        """

        crud_strings = current.response.s3.crud_strings
        # CRUD strings for this table
        _crud_strings = crud_strings.get(tablename, crud_strings)
        return _crud_strings.get(name,
                                 # Default fallback
                                 crud_strings.get(name))

# =============================================================================
# Global functions
#
def s3_request(*args, **kwargs):

    xml = current.xml
    headers = {"Content-Type":"application/json"}
    try:
        r = S3Request(*args, **kwargs)
    except SyntaxError:
        message = sys.exc_info()[1]
        current.log.error(message)
        raise HTTP(400,
                    body=xml.json_message(False, 400, message=message),
                    web2py_header=message,
                    **headers)
    except KeyError:
        message = sys.exc_info()[1]
        current.log.error(message)
        raise HTTP(404,
                    body=xml.json_message(False, 404, message=message),
                    web2py_header=message,
                    **headers)
    except:
        raise
    return r

# END =========================================================================
