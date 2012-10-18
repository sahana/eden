# -*- coding: utf-8 -*-

""" S3 RESTful API

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

import sys
import datetime
import time
try:
    from cStringIO import StringIO    # Faster, where available
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
# Here are dependencies listed for reference:
#from gluon.dal import Field
#from gluon.globals import current
#from gluon.html import A, DIV, URL
#from gluon.http import HTTP, redirect
#from gluon.validators import IS_EMPTY_OR, IS_NOT_IN_DB, IS_DATE, IS_TIME
from gluon.dal import Row
from gluon.storage import Storage
from gluon.tools import callback

from s3resource import S3Resource
from s3utils import S3MarkupStripper

DEBUG = False
if DEBUG:
    print >> sys.stderr, "S3REST: DEBUG MODE"
    def _debug(m):
        print >> sys.stderr, m
else:
    _debug = lambda m: None

# =============================================================================
class S3RequestManager(object):
    """
        Request Manager
    """

    DELETED = "deleted"
    RCVARS = "rcvars"

    MAX_DEPTH = 10

    # Prefixes of resources that must not be manipulated from remote
    # Can be amended from CLI using: s3mgr.PROTECTED = []
    PROTECTED = ("admin",)

    # -------------------------------------------------------------------------
    def __init__(self):
        """
            Constructor
        """

        self.deployment_settings = current.deployment_settings

        # Ensure we have a "s3" Storage in response
        if "s3" not in current.response:
            current.response.s3 = Storage()

        # Error messages
        T = current.T
        self.ERROR = Storage(
            BAD_RECORD = T("Record not found"),
            BAD_METHOD = T("Unsupported method"),
            BAD_FORMAT = T("Unsupported data format"),
            BAD_REQUEST = T("Invalid request"),
            BAD_TEMPLATE = T("XSLT stylesheet not found"),
            BAD_RESOURCE = T("Nonexistent or invalid resource"),
            PARSE_ERROR = T("XML parse error"),
            TRANSFORMATION_ERROR = T("XSLT transformation error"),
            BAD_SOURCE = T("Invalid source"),
            NO_MATCH = T("No matching element found in the data source"),
            VALIDATION_ERROR = T("Validation error"),
            DATA_IMPORT_ERROR = T("Data import error"),
            NOT_PERMITTED = T("Operation not permitted"),
            NOT_IMPLEMENTED = T("Not implemented"),
            INTEGRITY_ERROR = T("Integrity error: record can not be deleted while it is referenced by other records")
        )

        self.LABEL = Storage(CREATE=T("CREATE"),
                             READ=T("READ"),
                             UPDATE=T("UPDATE"),
                             DELETE=T("DELETE"),
                             COPY=T("COPY"))

        # Settings
        self.s3 = current.response.s3
        self.domain = current.request.env.server_name
        self.rlink_tablename = "s3_rlink"

        self.show_urls = True
        self.show_ids = False

        # Errors
        self.error = None

        # Toolkits
        self.audit = current.s3_audit
        self.auth = auth = current.auth

        # Register
        current.manager = self

        # Codecs
        self.codecs = Storage()

        # Default method handlers (override in config)
        self.crud = S3Method()
        self.search = S3Method()

        # Hooks
        self.permit = auth.s3_has_permission
        self.messages = None
        self.import_prep = None
        self.log = None

        # JSON/CSV formats and content-type headers
        self.json_formats = []
        self.csv_formats = []
        self.content_type = Storage()

    # -------------------------------------------------------------------------
    # Session variables
    # -------------------------------------------------------------------------
    def get_session(self, prefix, name):
        """
            Reads the last record ID for a resource from a session

            @param prefix: the prefix of the resource name (=module name)
            @param name: the name of the resource (=without prefix)
        """

        session = current.session

        tablename = "%s_%s" % (prefix, name)
        if self.RCVARS in session and tablename in session[self.RCVARS]:
            return session[self.RCVARS][tablename]
        else:
            return None

    # -------------------------------------------------------------------------
    def store_session(self, prefix, name, id):
        """
            Stores a record ID for a resource in a session

            @param prefix: the prefix of the resource name (=module name)
            @param name: the name of the resource (=without prefix)
            @param id: the ID to store
        """

        session = current.session

        RCVARS = self.RCVARS

        if RCVARS not in session:
            session[RCVARS] = Storage()
        if RCVARS in session:
            tablename = "%s_%s" % (prefix, name)
            session[RCVARS][tablename] = id
        return True # always return True to make this chainable

    # -------------------------------------------------------------------------
    def clear_session(self, prefix=None, name=None):
        """
            Clears one or all record IDs stored in a session

            @param prefix: the prefix of the resource name (=module name)
            @param name: the name of the resource (=without prefix)
        """

        session = current.session

        RCVARS = self.RCVARS

        if prefix and name:
            tablename = "%s_%s" % (prefix, name)
            if RCVARS in session and tablename in session[RCVARS]:
                del session[RCVARS][tablename]
        else:
            if RCVARS in session:
                del session[RCVARS]

        return True # always return True to make this chainable

    # -------------------------------------------------------------------------
    # Utilities
    # -------------------------------------------------------------------------
    @staticmethod
    def validate(table, record, fieldname, value):
        """
            Validates a single value

            @param table: the database table
            @param record: the existing database record, if available
            @param fieldname: name of the field
            @param value: value to check

            @status: deprecated, use S3Resource.validate instead
        """

        try:
            field = table[fieldname]
        except:
            raise AttributeError("No field %s in %s" % (fieldname,
                                                        table._tablename))
        if field:
            if record:
                v = record.get(fieldname, None)
                if v and v == value:
                    return (value, None)
                self_id = record[table._id.name]
                requires = field.requires
                if field.unique and not requires:
                    field.requires = IS_NOT_IN_DB(current.db, str(field))
                    field.requires.set_self_id(self_id)
                else:
                    if not isinstance(requires, (list, tuple)):
                        requires = [requires]
                    for r in requires:
                        if hasattr(r, "set_self_id"):
                            r.set_self_id(self_id)
                        if hasattr(r, "other") and \
                            hasattr(r.other, "set_self_id"):
                            r.other.set_self_id(self_id)
            try:
                value, error = field.validate(value)
            except:
                return (None, None)
            else:
                return (value, error)

    # -------------------------------------------------------------------------
    def represent(self, field,
                  value=None,
                  record=None,
                  linkto=None,
                  strip_markup=False,
                  xml_escape=False,
                  non_xml_output=False,
                  extended_comments=False):
        """
            Represent a field value

            @param field: the field (Field)
            @param value: the value
            @param record: record to retrieve the value from
            @param linkto: function or format string to link an ID column
            @param strip_markup: strip away markup from representation
            @param xml_escape: XML-escape the output
            @param non_xml_output: Needed for output such as pdf or xls
            @param extended_comments: Typically the comments are abbreviated
        """

        xml_encode = current.xml.xml_encode

        NONE = str(current.T("None")).decode("utf-8")
        cache = current.cache
        fname = field.name

        # Get the value
        if record is not None:
            tablename = str(field.table)
            if tablename in record and isinstance(record[tablename], Row):
                text = val = record[tablename][field.name]
            else:
                text = val = record[field.name]
        else:
            text = val = value

        # Always XML-escape content markup if it is intended for xml output
        # This code is needed (for example) for a data table that includes a link
        # Such a table can be seen at inv/inv_item
        # where the table displays a link to the warehouse
        if non_xml_output == False:
            if not xml_escape and val is not None:
                ftype = str(field.type)
                if ftype in ("string", "text"):
                    try:
                        val = unicode(val)
                    except:
                        val = unicode(val.decode("utf-8"))
                    val = text = xml_encode(val)
                elif ftype == "list:string":
                    vals = []
                    for v in val:
                        try:
                            vals.append(xml_encode(unicode(v)))
                        except:
                            vals.append(xml_encode(unicode(v.decode("utf-8"))))
                    val = text = vals

        # Get text representation
        if field.represent:
            try:
                key = "%s_repr_%s" % (field, val)
                unicode(key)
            except (UnicodeEncodeError, UnicodeDecodeError):
                text = field.represent(val)
            else:
                text = cache.ram(key,
                                 lambda: field.represent(val),
                                 time_expire=60)
                if isinstance(text, DIV):
                    text = str(text)
                elif not isinstance(text, basestring):
                    text = unicode(text)
        else:
            if val is None:
                text = NONE
            elif fname == "comments" and not extended_comments:
                ur = unicode(text)
                if len(ur) > 48:
                    text = "%s..." % ur[:45].encode("utf8")
            else:
                text = unicode(text)

        # Strip away markup from text
        if strip_markup and "<" in text:
            stripper = S3MarkupStripper()
            stripper.feed(text)
            text = stripper.stripped()

        # Link ID field
        if fname == "id" and linkto:
            id = str(val)
            try:
                href = linkto(id)
            except TypeError:
                href = linkto % id
            href = str(href).replace(".aadata", "")
            return A(text, _href=href).xml()

        # XML-escape text
        elif xml_escape:
            text = xml_encode(text)

        try:
            text = text.decode("utf-8")
        except:
            pass

        return text

    # -------------------------------------------------------------------------
    def onaccept(self, table, record, method="create"):

        s3db = current.s3db
        if hasattr(table, "_tablename"):
            tablename = table._tablename
        else:
            tablename = table

        onaccept = s3db.get_config(tablename, "%s_onaccept" % method,
                   s3db.get_config(tablename, "onaccept"))
        if onaccept:
            callback(onaccept, record, tablename=tablename)
        return

    # -------------------------------------------------------------------------
    def onvalidation(self, table, record, method="create"):

        s3db = current.s3db
        if hasattr(table, "_tablename"):
            tablename = table._tablename
        else:
            tablename = table

        onvalidation = s3db.get_config(tablename, "%s_onvalidation" % method,
                       s3db.get_config(tablename, "onvalidation"))
        if onaccept:
            callback(onvalidation, record, tablename=tablename)
        return

# =============================================================================
class S3Request(object):
    """
        Class to handle RESTful requests
    """

    INTERACTIVE_FORMATS = ("html", "iframe", "popup")
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

        manager = current.manager

        # Common settings
        self.UNAUTHORISED = current.T("Not Authorized")
        self.ERROR = manager.ERROR

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
        auth = manager.auth
        if c or f:
            if not auth.permission.has_permission("read",
                                                  c=self.controller,
                                                  f=self.function):
                auth.permission.fail()

        # Allow override of request attributes
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
            self.post_vars = dict()
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
        vars = Storage(self.get_vars)

        # Interactive representation format?
        self.interactive = self.representation in self.INTERACTIVE_FORMATS

        # Show information on deleted records?
        include_deleted = False
        if self.representation=="xml" and "include_deleted" in vars:
            include_deleted = True
        if "components" in vars:
            cnames = vars["components"]
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
            if varname in vars:
                var = vars[varname]
                if not isinstance(var, (list, tuple)):
                    var = [var]
                var.append(component_id)
                vars[varname] = var
            else:
                vars[varname] = component_id

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
                                   vars=vars,
                                   components=components,
                                   approved=approved,
                                   unapproved=unapproved,
                                   include_deleted=include_deleted)

        self.tablename = self.resource.tablename
        table = self.table = self.resource.table

        # Try to load the master record
        self.record = None
        uid = self.vars.get("%s.uid" % self.name, None)
        if self.id or uid and not isinstance(uid, (list, tuple)):
            # Single record expected
            self.resource.load()
            if len(self.resource) == 1:
                self.record = self.resource.records().first()
                id = table._id.name
                self.id = self.record[id]
                manager.store_session(self.resource.prefix,
                                      self.resource.name,
                                      self.id)
            else:
                manager.error = manager.ERROR.BAD_RECORD
                if self.representation == "html":
                    current.session.error = manager.error
                    self.component = None # => avoid infinite loop
                    redirect(URL(r=current.request, c=self.controller))
                else:
                    raise KeyError(manager.error)

        # Identify the component
        self.component = None
        self.pkey = None # @todo: deprecate
        self.fkey = None # @todo: deprecate
        self.multiple = True # @todo: deprecate

        if self.component_name:
            c = self.resource.components.get(self.component_name, None)
            if c:
                self.component = c
                self.pkey, self.fkey = c.pkey, c.fkey # @todo: deprecate
                self.multiple = c.multiple # @todo: deprecate
            else:
                manager.error = "%s not a component of %s" % (
                                        self.component_name,
                                        self.resource.tablename)
                raise SyntaxError(manager.error)

        # Identify link table and link ID
        self.link = None
        self.link_id = None

        if self.component is not None:
            self.link = self.component.link
        if self.link and self.id and self.component_id:
            self.link_id = self.link.link_id(self.id, self.component_id)
            if self.link_id is None:
                manager.error = manager.ERROR.BAD_RECORD
                if self.representation == "html":
                    current.session.error = manager.error
                    self.component = None # => avoid infinite loop
                    redirect(URL(r=current.request, c=self.controller))
                else:
                    raise KeyError(manager.error)

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
            @returns: the handler function
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
            return method_hooks[method]

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

        # ?format= overrides extensions
        if "format" in self.vars:
            ext = self.vars["format"]
            if isinstance(ext, list):
                ext = ext[-1]
            representation = ext or representation
        if not representation:
            self.representation = self.DEFAULT_REPRESENTATION
        else:
            self.representation = representation.lower()
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
        hooks = response.s3
        self.next = None

        bypass = False
        output = None
        preprocess = None
        postprocess = None

        # Enforce primary record ID
        if not self.id and self.representation == "html":
            if self.component or self.method in ("read", "update"):
                count = self.resource.count()
                if self.vars is not None and count == 1:
                    self.resource.load()
                    self.record = self.resource._rows[0]
                else:
                    if hasattr(self.resource.search, "search_interactive"):
                        redirect(URL(r=self, f=self.name, args="search",
                                     vars={"_next": self.url(id="[id]")}))
                    else:
                        current.session.error = self.ERROR.BAD_RECORD
                        redirect(URL(r=self, c=self.prefix, f=self.name))

        # Pre-process
        if hooks is not None:
            preprocess = hooks.get("prep", None)
        if preprocess:
            pre = preprocess(self)
            if pre and isinstance(pre, dict):
                bypass = pre.get("bypass", False) is True
                output = pre.get("output", None)
                if not bypass:
                    success = pre.get("success", True)
                    if not success:
                        if self.representation == "html" and output:
                            if isinstance(output, dict):
                                output.update(r=self)
                            return output
                        else:
                            status = pre.get("status", 400)
                            message = pre.get("message",
                                              self.ERROR.BAD_REQUEST)
                            self.error(status, message)
            elif not pre:
                self.error(400, self.ERROR.BAD_REQUEST)

        # Default view
        if self.representation not in ("html", "popup"):
            response.view = "xml.html"

        # Content type
        response.headers["Content-Type"] = \
            current.manager.content_type.get(self.representation, "text/html")

        # Custom action?
        if not self.custom_action:
            self.custom_action = current.s3db.get_method(self.prefix, self.name,
                                                         component_name=self.component_name,
                                                         method=self.method)

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
                self.error(405, self.ERROR.BAD_METHOD)
            # Invoke the method handler
            if handler is not None:
                output = handler(self, **attr)
            elif self.method == "search":
                output = self.resource.search(self, **attr)
            else:
                # Fall back to CRUD
                output = self.resource.crud(self, **attr)

        # Post-process
        if hooks is not None:
            postprocess = hooks.get("postp", None)
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
                form = output.get("form", None)
                if form:
                    if not hasattr(form, "errors"):
                        form = form[0]
                    if form.errors:
                        return output

            session = current.session
            session.flash = response.flash
            session.confirmation = response.confirmation
            session.error = response.error
            session.warning = response.warning
            redirect(self.next)

        return output

    # -------------------------------------------------------------------------
    def __GET(self):
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
                    self.error(404, self.ERROR.BAD_RECORD)
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
            current.manager.clear_session(self.prefix, self.name)
            if "_next" in self.vars:
                request_vars = dict(_next=self._next)
            else:
                request_vars = {}
            if self.representation == "html" and \
               self.resource.search.search_interactive:
                self.next = URL(r=self,
                                f=self.name,
                                args="search",
                                vars=request_vars)
            else:
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

        manager = current.manager
        _vars = r.get_vars

        # Slicing
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

        # msince
        msince = _vars.get("msince", None)
        if msince is not None:
            tfmt = current.xml.ISOFORMAT
            try:
                (y, m, d, hh, mm, ss, t0, t1, t2) = \
                    time.strptime(msince, tfmt)
                msince = datetime.datetime(y, m, d, hh, mm, ss)
            except ValueError:
                msince = None

        # Show IDs (default: False)
        if "show_ids" in _vars:
            if _vars["show_ids"].lower() == "true":
                manager.show_ids = True

        # Show URLs (default: True)
        if "show_urls" in _vars:
            if _vars["show_urls"].lower() == "false":
                manager.show_urls = False

        # Maxbounds (default: False)
        maxbounds = False
        if "maxbounds" in _vars:
            if _vars["maxbounds"].lower() == "true":
                maxbounds = True
        if r.representation in ("gpx", "osm"):
            maxbounds = True

        # Components of the master resource (tablenames)
        if "mcomponents" in _vars:
            mcomponents = _vars["mcomponents"]
            if str(mcomponents).lower() == "none":
                mcomponents = None
            elif not isinstance(mcomponents, list):
                mcomponents = mcomponents.split(",")
        else:
            mcomponents = [] # all

        # Components of referenced resources (tablenames)
        if "rcomponents" in _vars:
            rcomponents = _vars["rcomponents"]
            if str(rcomponents).lower() == "none":
                rcomponents = None
            elif not isinstance(rcomponents, list):
                rcomponents = rcomponents.split(",")
        else:
            rcomponents = None

        # Maximum reference resolution depth
        if "maxdepth" in _vars:
            maxdepth = _vars["maxdepth"]
            try:
                manager.MAX_DEPTH = int(maxdepth)
            except ValueError:
                pass

        # References to resolve (field names)
        if "references" in _vars:
            references = _vars["references"]
            if str(references).lower() == "none":
                references = []
            elif not isinstance(references, list):
                references = references.split(",")
        else:
            references = None # all

        # Export field selection
        if "fields" in _vars:
            fields = _vars["fields"]
            if str(fields).lower() == "none":
                fields = []
            elif not isinstance(fields, list):
                fields = fields.split(",")
        else:
            fields = None # all

        # Find XSLT stylesheet
        stylesheet = r.stylesheet()

        # Add stylesheet parameters
        args = Storage()
        if stylesheet is not None:
            if r.component:
                args.update(id=r.id, component=r.component.tablename)
            mode = _vars.get("xsltmode", None)
            if mode is not None:
                args.update(mode=mode)

        # Set response headers
        headers = current.response.headers
        representation = r.representation
        if representation in manager.json_formats:
            as_json = True
            default = "application/json"
        else:
            as_json = False
            default = "text/xml"
        headers["Content-Type"] = manager.content_type.get(representation,
                                                           default)

        # Export the resource
        output = r.resource.export_xml(start=start,
                                       limit=limit,
                                       msince=msince,
                                       fields=fields,
                                       dereference=True,
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

        _vars = r.get_vars

        # Skip invalid records?
        if "ignore_errors" in _vars:
            ignore_errors = True
        else:
            ignore_errors = False

        # Find all source names in the URL vars
        def findnames(_vars, name):
            nlist = []
            if name in _vars:
                names = _vars[name]
                if isinstance(names, (list, tuple)):
                    names = ",".join(names)
                names = names.split(",")
                for n in names:
                    if n[0] == "(" and ")" in n[1:]:
                        nlist.append(n[1:].split(")", 1))
                    else:
                        nlist.append([None, n])
            return nlist
        filenames = findnames(_vars, "filename")
        fetchurls = findnames(_vars, "fetchurl")
        source_url = None

        # Get the source(s)
        manager = current.manager
        json_formats = manager.json_formats
        csv_formats = manager.csv_formats
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
            id = None
        else:
            id = r.id

        # Transformation mode?
        if "xsltmode" in _vars:
            args = dict(xsltmode=_vars["xsltmode"])
        else:
            args = dict()
        # These 3 options are called by gis.show_map() & read by the
        # GeoRSS Import stylesheet to populate the gis_cache table
        # Source URL: For GeoRSS/KML Feed caching
        if source_url:
            args["source_url"] = source_url
        # Data Field: For GeoRSS/KML Feed popups
        if "data_field" in _vars:
            args["data_field"] = _vars["data_field"]
        # Image Field: For GeoRSS/KML Feed popups
        if "image_field" in _vars:
            args["image_field"] = _vars["image_field"]

        # Format type?
        if format in json_formats:
            format = "json"
        elif format in csv_formats:
            format = "csv"
        else:
            format = "xml"

        try:
            output = r.resource.import_xml(source,
                                           id=id,
                                           format=format,
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

        json_formats = current.manager.json_formats
        if format in json_formats:
            as_json = True
            content_type = "application/json"
        else:
            as_json = False
            content_type = "text/xml"
        _vars = r.get_vars
        meta = str(_vars.get("meta", False)).lower() == "true"
        opts = str(_vars.get("options", False)).lower() == "true"
        refs = str(_vars.get("references", False)).lower() == "true"
        stylesheet = r.stylesheet()
        output = r.resource.export_struct(meta=meta,
                                          options=opts,
                                          references=refs,
                                          stylesheet=stylesheet,
                                          as_json=as_json)
        if output is None:
            # Transformation error
            r.error(400, current.xml.error)
        response = current.response
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
            r.error(501, r.ERROR.BAD_FORMAT)
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

        _vars = r.get_vars
        if "field" in _vars:
            items = _vars["field"]
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
        only_last = False
        if "only_last" in _vars:
            only_last = _vars["only_last"]
        show_uids = False
        if "show_uids" in _vars:
            v = _vars["show_uids"]
            if isinstance(v, (list, tuple)):
                v = v[-1]
            if v.lower() == "true":
                show_uids = True
        component = r.component_name
        representation = r.representation
        if representation == "xml":
            output = r.resource.export_options(component=component,
                                               fields=fields,
                                               show_uids=show_uids)
            content_type = "text/xml"
        elif representation == "s3json":
            output = r.resource.export_options(component=component,
                                               fields=fields,
                                               only_last=only_last,
                                               as_json=True)
            content_type = "application/json"
        else:
            r.error(501, r.ERROR.BAD_FORMAT)
        response = current.response
        response.headers["Content-Type"] = content_type
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
    def __getattr__(self, name):
        """
            Called upon r.<name>:
                - returns the value of the attribute
                - falls back to current.request if the attribute is not
                  defined here.
                This allows to seamlessly replace web2py's request object
                with this instance, and to override certain attributes of it.

            @param name: the attribute name
        """

        request = current.request
        if name in self.__dict__:
            return self.__dict__[name]
        elif name in (request or {}):
            return request[name]
        else:
            raise AttributeError

    # -------------------------------------------------------------------------
    def transformable(self, method=None):
        """
            Check the request for a transformable format

            @param method: "import" for import methods, else None
        """

        if self.representation in ("html", "aadata", "popup", "iframe"):
            return False

        stylesheet = self.stylesheet(method=method, skip_error=True)

        if self.representation != "xml" and not stylesheet:
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
            print >> sys.stderr, "ERROR: %s" % message
            raise HTTP(status,
                       body=current.xml.json_message(success=False,
                                                     status_code=status,
                                                     message=message,
                                                     tree=tree),
                       web2py_header=message,
                       **headers)

    # -------------------------------------------------------------------------
    def url(self, id=None, method=None, representation=None, vars=None):
        """
            Returns the URL of this request

            @param id: the record ID
            @param method: the URL method
            @param representation: the representation for the URL
            @param vars: the URL query variables
        """

        if vars is None:
            vars = self.get_vars
        elif isinstance(vars, str):
            # We've come from a dataTable_vars which has the vars as
            # a JSON string, but with the wrong quotation marks
            vars = json.loads(vars.replace("'", "\""))

        if "format" in vars:
            del vars["format"]

        args = []
        read = False

        component_id = self.component_id
        if id is None:
            id = self.id
        else:
            read = True

        if not representation:
            representation = self.representation
        if method is None:
            method = self.method
        elif method == "":
            method = None
            if not read:
                if self.component:
                    component_id = None
                else:
                    id = None
        else:
            if id is None:
                id = self.id
            elif id == 0:
                id = None
            else:
                id = str(id)
                if len(id) == 0:
                    id = "[id]"

        if self.component:
            if id:
                args.append(id)
            args.append(self.component_name)
            if component_id:
                args.append(component_id)
            if method:
                args.append(method)
        else:
            if id:
                args.append(id)
            if method:
                args.append(method)

        f = self.function
        if not representation == self.DEFAULT_REPRESENTATION:
            if len(args) > 0:
                args[-1] = "%s.%s" % (args[-1], representation)
            else:
                f = "%s.%s" % (f, representation)

        return URL(r=self,
                   c=self.controller,
                   f=f,
                   args=args, vars=vars)

    # -------------------------------------------------------------------------
    def target(self):
        """
            Get the target table of the current request

            @returns: a tuple of (prefix, name, table, tablename) of the target
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
        import os
        stylesheet = os.path.join(folder, path, format, filename)
        if not os.path.exists(stylesheet):
            if not skip_error:
                self.error(501, "%s: %s" % (self.ERROR.BAD_TEMPLATE,
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
        content_type = self.env.get("content_type", None)

        source = []
        if content_type and content_type.startswith("multipart/"):
            import cgi
            ext = ".%s" % self.representation
            vars = self.post_vars
            for v in vars:
                p = vars[v]
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

            ## In interactive single-record CRUD, open the
            ## instance record instead of a super-entity record
            #if r.interactive and \
               #self.record_id and \
               #self.method in ("read", "update") and \
               #self.resource.table._id.name != "id":
                #record = self.resource[self.record_id]
                #tablename = record.instance_type
                #resource = current.s3db.resource(tablename
                                                 #uid=record.uuid)
                #resource.load()
                #if resource.count() == 1:
                    #self.resource = resource
                    #self.record_id = resource.records().first()[resource.table._id]

        self.prefix = resource.prefix
        self.name = resource.name
        self.tablename = resource.tablename
        self.table = resource.table
        self.resource = resource

        if self.method == "_init":
            return None

        # Apply method
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

        if not method:
            method = self.method
        if method == "list":
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

        import os
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

# =============================================================================
# Global functions
#
def s3_request(*args, **kwargs):

    manager = current.manager
    xml = current.xml

    manager.error = None
    headers = {"Content-Type":"application/json"}
    try:
        r = S3Request(*args, **kwargs)
    except SyntaxError:
        error = manager.error
        print >> sys.stderr, "ERROR: %s" % error
        raise HTTP(400,
                    body=xml.json_message(False, 400, message=error),
                    web2py_header=error,
                    **headers)
    except KeyError:
        error = manager.error
        print >> sys.stderr, "ERROR: %s" % error
        raise HTTP(404,
                    body=xml.json_message(False, 404, message=error),
                    web2py_header=error,
                    **headers)
    except:
        raise
    return r

# END =========================================================================
