# -*- coding: utf-8 -*-

"""
    S3 RESTful API

    @see: U{B{I{S3XRC}} <http://eden.sahanafoundation.org/wiki/S3XRC>}

    @requires: U{B{I{gluon}} <http://web2py.com>}
    @requires: U{B{I{lxml}} <http://codespeak.net/lxml>}

    @author: Dominic König <dominic[at]aidiq.com>

    @copyright: 2009-2011 (c) Sahana Software Foundation
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

__all__ = ["S3RequestManager",
           "S3Request",
           "S3QueryBuilder",
           "S3Resource"]

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

from gluon.storage import Storage
from gluon.sql import Row, Rows
from gluon import *
from gluon.tools import callback
import gluon.contrib.simplejson as json

from s3validators import IS_ONE_OF
from s3tools import SQLTABLES3
from s3xml import S3XML
from s3model import S3Model, S3ModelExtensions, S3RecordLinker
from s3export import S3Exporter
from s3method import S3Method

from s3import import S3ImportJob
from s3sync import S3Sync

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

    HOOKS = "s3"
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
            BAD_SOURCE = T("Invalid XML source"),
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
        self.auth = current.auth
        self.gis = current.gis

        # Register
        current.manager = self

        # Helpers
        self.query_builder = S3QueryBuilder()
        self.model = S3ModelExtensions()
        self.configure = self.model.configure
        self.load = S3Model.table
        self.loader = self.model.loader

        self.linker = S3RecordLinker()
        self.xml = S3XML()
        self.exporter = S3Exporter()
        self.sync = S3Sync()

        # Codecs
        self.codecs = Storage()

        # Default method handlers (override in config)
        self.crud = S3Method()
        self.search = S3Method()

        # Hooks
        self.permit = self.auth.s3_has_permission
        self.messages = None
        self.import_prep = None
        self.log = None

        # JSON/CSV formats and content-type headers
        self.json_formats = []
        self.csv_formats = []
        self.content_type = Storage()


    # -------------------------------------------------------------------------
    # REST interface wrappers
    # -------------------------------------------------------------------------
    def define_resource(self, prefix, name,
                        id=None,
                        uid=None,
                        filter=None,
                        vars=None,
                        parent=None,
                        components=None,
                        include_deleted=False):
        """
            Defines a resource

            @param prefix: the application prefix
            @param name: the resource name (without application prefix)
            @param id: record ID or list of record IDs
            @param uid: record UID or list of record UIDs
            @param filter: web2py query to filter the resource query
            @param vars: dict of URL query parameters
            @param parent: the parent resource (if this is a component)
            @param components: list of component (names)
        """

        resource = S3Resource(self, prefix, name,
                              id=id,
                              uid=uid,
                              filter=filter,
                              vars=vars,
                              parent=parent,
                              components=components,
                              include_deleted=include_deleted)

        return resource

    # -------------------------------------------------------------------------
    def parse_request(self, *args, **vars):
        """
            Wrapper function for S3Request

            @see: S3Request.__init__() for argument list details
        """

        self.error = None
        headers={"Content-Type":"application/json"}
        try:
            r = S3Request(self, *args, **vars)
        except SyntaxError:
            print >> sys.stderr, "ERROR: %s" % self.error
            raise HTTP(400, body=self.xml.json_message(False, 400,
                                                       message=self.error),
                       web2py_header=self.error,
                       **headers)
        except KeyError:
            print >> sys.stderr, "ERROR: %s" % self.error
            raise HTTP(404, body=self.xml.json_message(False, 404,
                                                       message=self.error),
                       web2py_header=self.error,
                       **headers)
        except:
            raise
        return r

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

        xml = self.xml

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
                    val = text = xml.xml_encode(str(val))
                elif ftype == "list:string":
                    val = text = [xml.xml_encode(str(v)) for v in val]

        # Get text representation
        if field.represent:
            try:
                key = "%s_repr_%s" % (field, val)
                unicode(key)
            except (UnicodeEncodeError, UnicodeDecodeError):
                text = field.represent(val)
            else:
                text = str(cache.ram(key,
                                     lambda: field.represent(val),
                                     time_expire=5))
        else:
            if val is None:
                text = NONE
            elif fname == "comments" and not extended_comments:
                ur = unicode(text, "utf8")
                if len(ur) > 48:
                    text = "%s..." % ur[:45].encode("utf8")
            else:
                text = str(text)

        # Strip away markup from text
        if strip_markup and "<" in text:
            try:
                markup = etree.XML(text)
                text = markup.xpath(".//text()")
                if text:
                    text = " ".join(text)
                else:
                    text = ""
            except etree.XMLSyntaxError:
                text = text.replace("<", "<!-- <").replace(">", "> -->")

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
            text = xml.xml_encode(text)

        try:
            text = text.decode("utf-8")
        except:
            pass

        return text

    # -------------------------------------------------------------------------
    def original(self, table, record):
        """
            Find the original record for a possible duplicate:
                - if the record contains a UUID, then only that UUID is used
                  to match the record with an existing DB record
                - otherwise, if the record contains some values for unique
                  fields, all of them must match the same existing DB record

            @param table: the table
            @param record: the record as dict or S3XML Element
        """

        xml = self.xml
        UID = xml.UID
        db = current.db

        # Get primary keys
        pkeys = [f for f in table.fields if table[f].unique]
        pvalues = Storage()

        # Get the values from record
        if isinstance(record, etree._Element):
            for f in pkeys:
                v = None
                if f == UID or f in xml.ATTRIBUTES_TO_FIELDS:
                    v = record.get(f, None)
                else:
                    xexpr = "%s[@%s='%s']" % (xml.TAG.data,
                                              xml.ATTRIBUTE.field, f)
                    child = record.xpath(xexpr)
                    if child:
                        child = child[0]
                        v = child.get(xml.ATTRIBUTE.value,
                                      xml.xml_decode(child.text))
                if v:
                    pvalues[f] = v
        elif isinstance(record, dict):
            for f in pkeys:
                v = record.get(f, None)
                if v:
                    pvalues[f] = v
        else:
            raise TypeError

        # Build match query
        query = None
        for f in pvalues:
            if f == UID:
                continue
            _query = (table[f] == pvalues[f])
            if query is not None:
                query = query | _query
            else:
                query = _query

        # Try to find exactly one match by non-UID unique keys
        if query:
            original = db(query).select(table.ALL, limitby=(0, 2))
            if len(original) == 1:
                return original.first()

        # If no match, then try to find a UID-match
        if UID in pvalues:
            uid = self.xml.import_uid(pvalues[UID])
            query = (table[UID] == uid)
            original = db(query).select(table.ALL, limitby=(0, 1)).first()
            if original:
                return original

        # No match or multiple matches
        return None

# =============================================================================

class S3Request(object):
    """
        Class to handle RESTful requests
    """

    def __init__(self,
                 manager,
                 prefix=None,
                 name=None,
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

            @param manager: the S3RequestManager
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
        self.INTERACTIVE_FORMATS = manager.s3.interactive_view_formats
        self.DEFAULT_REPRESENTATION = "html"
        self.ERROR = manager.ERROR
        self.HOOKS = manager.HOOKS # HOOKS = "s3"

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
            if not auth.permission(c=self.controller, f=self.function):
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
        if self.component_name and self.component_id:
            varname = "%s.id" % self.component_name
            if varname in vars:
                var = vars[varname]
                if not isinstance(var, (list, tuple)):
                    var = [var]
                var.append(self.component_id)
                vars[varname] = var
            else:
                vars[varname] = self.component_id

        # Define the target resource
        _filter = current.response[manager.HOOKS].filter # manager.HOOKS="s3"
        components = self.component_name
        if components is None:
            components = cnames
        self.resource = manager.define_resource(self.prefix,
                                                self.name,
                                                id=self.id,
                                                filter=_filter,
                                                vars=vars,
                                                components=components,
                                                include_deleted=include_deleted)

        self.tablename = self.resource.tablename
        self.table = self.resource.table

        # Try to load the master record
        self.record = None
        uid = self.vars.get("%s.uid" % self.name, None)
        if self.id or uid and not isinstance(uid, (list, tuple)):
            # Single record expected
            self.resource.load()
            if len(self.resource) == 1:
                self.record = self.resource.records().first()
                self.id = self.record.id
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
        self.set_handler("export_tree", self.get_tree,
                         http=["GET"], transform=True)
        self.set_handler("import_tree", self.put_tree,
                         http=["GET", "PUT", "POST"], transform=True)
        self.set_handler("fields", self.get_fields,
                         http=["GET"], transform=True)
        self.set_handler("options", self.get_options,
                         http=["GET"], transform=True)
        self.set_handler("sync", manager.sync,
                         http=["GET", "PUT", "POST"], transform=True)

        self.set_handler("sync_log", manager.sync.log,
                         http=["GET"], transform=True)
        self.set_handler("sync_log", manager.sync.log,
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

        for h in http:
            if h not in HTTP:
                continue
            if h not in self._handler:
                self._handler[h] = Storage()
            format_hooks = self._handler[h]
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
        """
            Parses the web2py request object
        """

        request = current.request
        manager = current.manager

        self.id = None
        self.component_name = None
        self.component_id = None
        self.method = None

        representation = self.extension

        # Get the names of all components
        model = manager.model
        tablename = "%s_%s" % (self.prefix, self.name)
        components = model.get_components(tablename)
        if components:
            components = components.keys()
        else:
            components = []

        # Map request args, catch extensions
        f = []
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
                f.append((method, arg))
                method = None
            else:
                f.append((method, None))
                method = arg
        if method:
            f.append((method, None))

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

    # -------------------------------------------------------------------------
    # REST Interface
    # -------------------------------------------------------------------------
    def __call__(self, **attr):
        """
            Execute this request

            @param attr: Parameters for the method handler
        """

        manager = current.manager
        request = current.request
        response = current.response
        session = current.session

        hooks = current.response.get(self.HOOKS, None)
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
                    self.record = self.resource._rows.first()
                else:
                    if hasattr(self.resource.search, "search_interactive"):
                        redirect(URL(r=self, f=self.name, args="search",
                                     vars={"_next": self.url(id="[id]")}))
                    else:
                        session.error = self.ERROR.BAD_RECORD
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
        content_type = manager.content_type
        response.headers["Content-Type"] = \
            content_type.get(self.representation, "text/html")

        # Custom action?
        if not self.custom_action:
            model = manager.model
            self.custom_action = model.get_method(self.prefix, self.name,
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
        manager = current.manager
        model = manager.model

        tablename = self.component and self.component.tablename or self.tablename

        transform = False
        if method is None or method in ("read", "display"):
            if self.transformable():
                method = "export_tree"
                transform = True
            elif self.component:
                if self.interactive and self.resource.count() == 1:
                    # Load the record
                    if not self.resource._rows:
                        self.resource.load(start=0, limit=1)
                    if self.resource._rows:
                        self.record = self.resource._rows[0]
                        self.id = self.resource.get_id()
                        self.uid = self.resource.get_uid()
                if self.multiple and not self.component_id:
                    method = "list"
                else:
                    method = "read"
            else:
                if self.id or method in ("read", "display"):
                    # Enforce single record
                    if not self.resource._rows:
                        self.resource.load(start=0, limit=1)
                    if self.resource._rows:
                        self.record = self.resource._rows[0]
                        self.id = self.resource.get_id()
                        self.uid = self.resource.get_uid()
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

        elif method == "clear" and not r.component:
            manager.clear_session(self.prefix, self.name)
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
                    original = current.manager.original(table, post_vars)
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
        resource = r.resource
        _vars = r.get_vars

        xml = manager.xml
        json_formats = manager.json_formats
        content_type = manager.content_type

        # Find XSLT stylesheet
        stylesheet = r.stylesheet()

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

        # Default GIS marker
        marker = _vars.get("marker", None)

        # msince
        msince = _vars.get("msince", None)
        if msince is not None:
            tfmt = xml.ISOFORMAT
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
        if representation in json_formats:
            as_json = True
            default = "application/json"
        else:
            as_json = False
            default = "text/xml"
        headers["Content-Type"] = content_type.get(representation, default)

        # Export the resource
        output = resource.export_xml(start=start,
                                     limit=limit,
                                     msince=msince,
                                     marker=marker,
                                     dereference=True,
                                     mcomponents=mcomponents,
                                     rcomponents=rcomponents,
                                     stylesheet=stylesheet,
                                     as_json=as_json,
                                     **args)
        # Transformation error?
        if not output:
            r.error(400, "XSLT Transformation Error: %s " % xml.error)

        return output

    # -------------------------------------------------------------------------
    @staticmethod
    def put_tree(r, **attr):
        """
            XML Element tree import method

            @param r: the S3Request method
            @param attr: controller attributes
        """

        manager = current.manager
        auth = manager.auth
        xml = manager.xml

        resource = r.resource
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
            output = resource.import_xml(source,
                                         id=id,
                                         format=format,
                                         stylesheet=stylesheet,
                                         ignore_errors=ignore_errors,
                                         **args)
        except IOError:
            auth.permission.fail()
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

        manager = current.manager
        resource = r.resource
        stylesheet = r.stylesheet()
        json_formats = manager.json_formats
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
        output = resource.struct(meta=meta,
                                 options=opts,
                                 references=refs,
                                 stylesheet=stylesheet,
                                 as_json=as_json)
        if output is None:
            # Transformation error
            xml = manager.xml
            r.error(400, xml.error)
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

        resource = r.resource
        representation = r.representation
        if representation == "xml":
            output = resource.fields(component=r.component_name)
            content_type = "text/xml"
        elif representation == "s3json":
            output = resource.fields(component=r.component_name,
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

        resource = r.resource
        _vars = r.get_vars
        if "field" in _vars:
            items = _vars["field"]
            if not isinstance(items, (list, tuple)):
                items = [items]
            fields = []
            for item in items:
                f = item.split(",")
                if f:
                    fields.extend(f)
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
            output = resource.options(component=component,
                                      fields=fields,
                                      show_uids=show_uids)
            content_type = "text/xml"
        elif representation == "s3json":
            output = resource.options(component=component,
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
    def unauthorised(self):
        """
            Action upon unauthorised request
        """

        auth = current.manager.auth
        auth.permission.fail()

    # -------------------------------------------------------------------------
    def error(self, status, message, tree=None, next=None):
        """
            Action upon error

            @param status: HTTP status code
            @param message: the error message
            @param tree: the tree causing the error
        """

        xml = current.manager.xml

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
                       body=xml.json_message(success=False,
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
        elif method=="":
            method = None
            if not read:
                if self.component:
                    component_id = None
                else:
                    id = None
        else:
            if id is None:
                id = self.id
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
        if not representation==self.DEFAULT_REPRESENTATION:
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

        import cgi

        self.files = Storage()
        content_type = self.env.get("content_type", None)

        source = []
        if content_type and content_type.startswith("multipart/"):
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

class S3QueryBuilder(object):
    """
        Query Builder
    """

    # -------------------------------------------------------------------------
    def parse_bbox_query(self, resource, vars):
        """
            Build a BBOX filter query
            Syntax ?bbox{.fkfield}=minLon,minLat,maxLon,maxLat

            @param resource: the resource
            @param vars: dict of URL vars
        """

        s3db = current.s3db
        locations = s3db.gis_location
        table = resource.table
        bbox_query = None

        if vars:
            for k in vars:
                if k[:4] == "bbox":
                    fname = None
                    if k.find(".") != -1:
                        fname = k.split(".")[1]
                    elif resource.tablename != "gis_location":
                        for f in resource.table.fields:
                            if str(table[f].type) == "reference gis_location":
                                fname = f
                                break
                    if fname is None or fname not in resource.table.fields:
                        # Field not found - ignore
                        continue
                    try:
                        minLon, minLat, maxLon, maxLat = vars[k].split(",")
                    except:
                        # Badly-formed bbox - ignore
                        continue
                    else:
                        bbox_filter = ((locations.lon > minLon) & \
                                       (locations.lon < maxLon) & \
                                       (locations.lat > minLat) & \
                                       (locations.lat < maxLat))
                        if fname is not None:
                            # Need a join
                            join = (locations.id == table[fname])
                            bbox = (join & bbox_filter)
                        else:
                            bbox = bbox_filter
                    if bbox_query is None:
                        bbox_query = bbox
                    else:
                        bbox_query = bbox_query & bbox

        return bbox_query

    # -------------------------------------------------------------------------
    def parse_url_rlinks(self, resource, vars):
        """
            Parse URL resource link queries. Syntax:
            ?linked{.<component>}.<from|to>.<table>={link_class},
                <ANY|ALL|list_of_ids>

            @param resource: the resource
            @param vars: dict of URL vars

            @status: currently unused
            @todo: deprecate?
        """

        db = current.db
        linker = current.manager.linker
        q = None

        for k in vars:
            if k[:7] == "linked.":
                link = k.split(".")
                if len(link) < 3:
                    continue
                else:
                    link = link[1:]
                o_tn = link.pop()
                if o_tn in db:
                    link_table = db[o_tn]
                else:
                    continue
                operator = link.pop()
                if not operator in ("from", "to"):
                    continue
                table = resource.table
                join = None
                if link and link[0] in resource.components:
                    component = components[link[0]]
                    table = component.table
                    pkey, fkey = component.pkey, component.fkey
                    join = (resource.table[pkey] == table[fkey])
                link_class = None
                union = False
                val = vars[k]
                if isinstance(val, (list, tuple)):
                    val = ",".join(val)
                ids = val.split(",")
                if ids:
                    if not ids[0].isdigit() and ids[0] not in ("ANY", "ALL"):
                        link_class = ids.pop(0)
                if ids:
                    if ids.count("ANY"):
                        link_id = None
                        union = True
                    elif ids.count("ALL"):
                        link_id = None
                    else:
                        link_id = filter(str.isdigit, ids)
                if operator == "from":
                    query = linker.get_target_query(link_table, link_id, table,
                                                    link_class=link_class,
                                                    union=union)
                else:
                    query = linker.get_origin_query(table, link_table, link_id,
                                                    link_class=link_class,
                                                    union=union)
                if query is not None:
                    if join is not None:
                        query = (join & query)
                    q = q and (q & query) or query
        return q

    # -------------------------------------------------------------------------
    def parse_url_query(self, resource, vars):
        """
            Parse URL query

            @param resource: the resource
            @param vars: dict of URL vars
        """

        s3db = current.s3db
        manager = current.manager
        xml = manager.xml
        model = manager.model
        settings = manager.deployment_settings

        q = Storage()

        queries = [(k, vars[k]) for k in vars if k.find(".") > 0]
        for k, val in queries:

            # Parse the URL variable name:
            # Format: cn.{fk$}fn{__op}
            # cn - component name
            # fk - foreign key
            # fn - field name
            # op - operator
            cn, fn = k.split(".", 1)
            fk = None
            op = "eq"
            if fn.find("$") > 0:
                fk, fn = fn.split("$", 1)
            if fn.find("__") > 0:
                fn, op = fn.split("__", 1)

            cjoin = None
            if cn == resource.alias:
                table = resource.table
            elif cn in resource.components:
                component = resource.components[cn]
                table = component.table
                cjoin = component.get_join()
            elif cn in resource.links:
                link = resource.links[cn]
                table = link.table
                cjoin = link.linked.get_join()
            else:
                continue
            if cjoin and manager.DELETED in table.fields:
                cjoin = cjoin & (table[manager.DELETED] != True)
            if cn not in q:
                q[cn] = Storage(join = cjoin,
                                table = table)
            hook = q[cn]

            if fn == "uid":
                fn = manager.xml.UID
            fjoin = None
            if fk is not None:
                if fk not in table.fields:
                    continue
                ftype = str(table[fk].type)
                if ftype[:9] == "reference":
                    ktablename = ftype[10:]
                    multiple = False
                elif ftype[:14] == "list:reference":
                    ktablename = ftype[15:]
                    multiple = True
                else:
                    continue
                try:
                    ktable = s3db[ktablename]
                except:
                    continue
                if multiple:
                    fjoin = (ktable._id.belongs(table[fk]))
                else:
                    fjoin = (ktable._id == table[fk])
                if manager.DELETED in ktable.fields:
                    fjoin = fjoin & (ktable[manager.DELETED] != True)
                table = ktable
            if (fk, fn) not in hook:
                hook[(fk, fn)] = Storage(join = fjoin,
                                         table = table)
            hook = hook[(fk, fn)]
            if "filter" not in hook:
                hook.filter = Storage()

            # parse value list
            if fn not in table.fields:
                continue
            ftype = str(table[fn].type)
            values = val
            if op in ("lt", "le", "gt", "ge"):
                if ftype not in ("id",
                                 "integer",
                                 "double",
                                 "date",
                                 "time",
                                 "datetime"):
                    continue
                if not isinstance(values, (list, tuple)):
                    values = [values]
                vlist = []
                for v in values:
                    if v.find(",") > 0:
                        v = v.split(",", 1)[-1]
                    vlist.append(v)
                values = vlist
            elif op == "eq":
                if isinstance(values, (list, tuple)):
                    values = values[-1]
                if values.find(",") > 0:
                    values = values.split(",")
                else:
                    values = [values]
            elif op == "ne":
                if not isinstance(values, (list, tuple)):
                    values = [values]
                vlist = []
                for v in values:
                    if v.find(",") > 0:
                        v = v.split(",")
                        vlist.extend(v)
                    else:
                        vlist.append(v)
                values = vlist
            elif op in ("like", "unlike"):
                if ftype not in ("string", "text"):
                    continue
                if not isinstance(values, (list, tuple)):
                    values = [values]
            elif op in ("in", "ex"):
                if not ftype.startswith("list:"):
                    continue
                if not isinstance(values, (list, tuple)):
                    values = [values]
            else:
                continue

            # parse values
            vlist = []
            for v in values:
                value = v
                if op in ("eq", "ne") and v.upper() == "NONE":
                    value = None
                    vlist.append(value)
                    continue
                if ftype == "boolean":
                    if v in ("true", "True"):
                        value = True
                    else:
                        value = False
                elif ftype in ("integer"):
                    try:
                        value = int(v)
                    except ValueError:
                        continue
                elif ftype.startswith("reference") or ftype == "id":
                    try:
                        value = long(v)
                    except ValueError:
                        continue
                elif ftype == "double":
                    try:
                        value = float(v)
                    except ValueError:
                        continue
                elif ftype == "date":
                    validator = IS_DATE(format=settings.get_L10n_date_format())
                    value, error = validator(v)
                    if error:
                        continue
                elif ftype == "time":
                    validator = IS_TIME()
                    value, error = validator(v)
                    if error:
                        continue
                elif ftype == "datetime":
                    tfmt = xml.ISOFORMAT
                    try:
                        (y,m,d,hh,mm,ss,t0,t1,t2) = time.strptime(v, tfmt)
                        value = datetime.datetime(y,m,d,hh,mm,ss)
                    except ValueError:
                        continue
                vlist.append(value)

            if vlist:
                hook.filter[op] = vlist

        return q

    # -------------------------------------------------------------------------
    def query(self, resource, id=None, uid=None, filter=None, vars=None):
        """
            Query builder

            @param resource: the resource
            @param id: record ID or list of record IDs to include
            @param uid: record UID or list of record UIDs to include
            @param filter: filtering query (DAL only)
            @param vars: dict of URL query variables
        """

        # Initialize
        resource.clear()
        resource.clear_query()

        manager = current.manager
        xml = manager.xml
        DELETED = manager.DELETED

        if vars:
            queries = self.parse_url_query(resource, vars)
            if queries:
                resource.vars = vars
        else:
            queries = Storage()

        # multiple results expected by default
        resource._multiple = True

        db = current.db
        table = resource.table
        name = resource.name

        # Accessible/available query
        if resource.accessible_query is not None:
            mquery = resource.accessible_query("read", table)
        else:
            mquery = (table._id > 0)

        # Deletion status
        if DELETED in table.fields and not resource.include_deleted:
            remaining = (table[DELETED] != True)
            mquery = remaining & mquery

        # Master query
        resource._mquery = None
        if id is not None:
            if not isinstance(id, (list, tuple)):
                resource._multiple = False
                mquery = mquery & (table._id == id)
            else:
                mquery = mquery & (table._id.belongs(id))
            resource._mquery = mquery
        if uid is not None and xml.UID in table:
            if not isinstance(uid, (list, tuple)):
                resource._multiple = False
                mquery = mquery & (table[xml.UID] == uid)
            else:
                mquery = mquery & (table[xml.UID].belongs(uid))
            resource._mquery = mquery

        # Component or link table query
        parent = resource.parent
        if parent:
            # Parent master query
            if parent._mquery:
                mquery &= parent._mquery
                mquery &= resource.get_join()
                if resource.alias in parent._cquery:
                    mquery &= parent._cquery[resource.alias]
                if resource.link is not None:
                    lname = resource.link.name
                    if lname in parent._cquery:
                        mquery &= parent._cquery[lname]
                elif resource.linked is not None:
                    cname = resource.linked.alias
                    if cname in parent._cquery:
                        mquery &= parent._cquery[cname]
            else:
                mquery = mquery & parent._query
                join = resource.get_join()
                if str(mquery).find(str(join)) == -1:
                    mquery = mquery & (join)
            # Component filter
            if resource.filter is not None:
                mquery = mquery & (resource.filter)
            # Cardinality
            resource._multiple = resource.multiple
            resource._query = mquery
        else:
            # BBOX query
            bbox = self.parse_bbox_query(resource, vars)
            if bbox is not None:
                mquery = mquery & bbox
                if resource._mquery:
                    resource._mquery &= bbox
            for cn in queries:
                hook = queries[cn]
                if hook.join is not None:
                    cjoin = hook.join
                else:
                    cjoin = None
                table = hook.table
                cquery = None
                for key in hook:
                    if key in ("table", "join"):
                        continue
                    fk, fn = key
                    subhook = hook[(fk, fn)]
                    if subhook.join is not None:
                        table = subhook.table
                        fjoin = subhook.join
                    else:
                        fjoin = None
                    if subhook.filter is None:
                        continue
                    if fn not in table.fields:
                        continue
                    fquery = None
                    for op in subhook.filter:
                        query = None

                        values = subhook.filter[op]
                        if fn == xml.UID:
                            uids = map(xml.import_uid, values)
                            values = uids
                        f = table[fn]
                        if op == "eq":
                            if len(values) == 1:
                                if values[0] is None:
                                    query = (f == None)
                                else:
                                    query = (f == values[0])
                            elif len(values):
                                if None in values:
                                    values.remove(None)
                                    query = ((f.belongs(values)) | (f == None))
                                else:
                                    query = (f.belongs(values))
                        elif op == "ne":
                            if len(values) == 1:
                                if values[0] is None:
                                    query = (f != None)
                                else:
                                    query = ((f != values[0]) | (f == None))
                            elif len(values):
                                query = ((~(f.belongs(values))) | (f == None))
                        elif op == "lt":
                            v = values[-1]
                            query = (f < v)
                        elif op == "le":
                            v = values[-1]
                            query = (f <= v)
                        elif op == "gt":
                            v = values[-1]
                            query = (f > v)
                        elif op == "ge":
                            v = values[-1]
                            query = (f >= v)
                        elif op == "in":
                            for v in values:
                                q = None
                                if v.find(",") != -1:
                                    sv = v.split(",")
                                    for s in sv:
                                        sq = (f.contains(s))
                                        q = q is not None and q | sq or sq
                                else:
                                    q = (f.contains(v))
                                if query:
                                    query = query & q
                                else:
                                    query = q
                            query = (query)
                        elif op == "ex":
                            for v in values:
                                q = (~(f.contains(v)))
                                if query:
                                    query = query & q
                                else:
                                    query = q
                            query = (query)
                        elif op == "like":
                            for v in values:
                                if v.find(",") != -1:
                                    q = None
                                    sv = v.split(",")
                                    for s in sv:
                                        sq = (f.lower().contains(s.lower()))
                                        q = q is not None and q | sq or sq
                                else:
                                    q = (f.lower().contains(v.lower()))
                                if query:
                                    query = query & q
                                else:
                                    query = q
                            query = (query)
                        elif op == "unlike":
                            for v in values:
                                q = ((~(f.lower().contains(v.lower()))) | (f == None))
                                if query:
                                    query = query & q
                                else:
                                    query = q
                            query = (query)
                        else:
                            continue
                        if query is not None:
                            if fquery is None:
                                fquery = query
                            else:
                                fquery &= query
                    if fquery is not None:
                        if fjoin is not None:
                            fquery = fjoin & fquery
                        if cquery is None:
                            cquery = fquery
                        else:
                            cquery &= fquery
                if cquery is not None:
                    if cjoin is not None:
                        resource._cjoins[cn] = cjoin
                        mquery &= cjoin
                    resource._cquery[cn] = cquery
                    mquery &= cquery
            if resource._mquery is not None:
                if name in resource._cquery:
                    resource._mquery &= resource._cquery[name]
                if filter:
                    resource._mquery &= filter
                resource._query = resource._mquery
            else:
                resource._query = mquery
                if filter:
                    resource._query &= filter

        _debug("Resource=%s\nMasterQuery=%s\nQuery=%s" % (resource.table,
                                                          resource._mquery,
                                                          resource._query))
        return resource._query

# =============================================================================

class S3Resource(object):
    """
        API for resources
    """

    # -------------------------------------------------------------------------
    # Constructor
    # -------------------------------------------------------------------------
    def __init__(self, manager, prefix, name,
                 id=None,
                 uid=None,
                 filter=None,
                 vars=None,
                 parent=None,
                 linked=None,
                 linktable=None,
                 components=None,
                 include_deleted=False):
        """
            Constructor

            @param manager: the S3RequestManager
            @param prefix: prefix of the resource name (=module name)
            @param name: name of the resource (without prefix)
            @param id: record ID (or list of record IDs)
            @param uid: record UID (or list of record UIDs)
            @param filter: filter query (DAL resources only)
            @param vars: dictionary of URL query variables
            @param parent: the parent resource
            @param linked: the linked resource
            @param linktable: the link table
            @param components: component name (or list of component names)
        """

        # DB and manager
        manager = current.manager
        db = current.db
        s3db = current.s3db

        self.ERROR = manager.ERROR

        # Export/Import hooks
        self.exporter = manager.exporter
        self.xml = manager.xml

        # Authorization hooks
        self.permit = manager.permit
        self.accessible_query = manager.auth.s3_accessible_query

        # Audit hook
        self.audit = manager.audit

        # Basic properties
        self.prefix = prefix
        self.name = name
        self.alias = name

        # Table
        model = manager.model
        self.tablename = "%s_%s" % (self.prefix, self.name)
        try:
            self.table = s3db[self.tablename]
        except:
            manager.error = "Undefined table: %s" % self.tablename
            raise KeyError(manager.error)

        # The Query
        self.query_builder = manager.query_builder
        self._query = None              # Active query
        self._mquery = None             # Master query
        self._fquery = None             # Filter query
        self._cjoins = Storage()        # Component joins
        self._cquery = Storage()        # Component queries

        self._multiple = True   # multiple rows expected by default

        self.include_deleted = include_deleted
        self.values = Storage()

        # The Rows
        self._rows = None
        self._ids = []
        self._uids = []
        self._length = None
        self._slice = False

        # Request attributes
        self.vars = None # set during build_query
        self.lastid = None
        self.files = Storage()

        # Component properties
        self.link = None
        self.linktable = None
        self.actuate = None
        self.lkey = None
        self.rkey = None
        self.pkey = None
        self.fkey = None
        self.multiple = True
        self.parent = parent # the parent resource
        self.linked = linked # the linked resource

        # Primary resource - attach components
        self.components = Storage()
        self.links = Storage()
        if self.parent is None:
            # Attach components
            hooks = model.get_components(self.table, names=components)
            for alias in hooks:
                # Create as resource
                c = hooks[alias]
                component = S3Resource(manager, c.prefix, c.name,
                                       parent=self,
                                       linktable=c.linktable,
                                       include_deleted=self.include_deleted)

                # Update component properties
                component.pkey = c.pkey
                component.fkey = c.fkey
                component.linktable = c.linktable
                component.lkey = c.lkey
                component.rkey = c.rkey
                component.actuate = c.actuate
                component.autodelete = c.autodelete
                component.autocomplete = c.autocomplete
                component.alias = c.alias
                component.multiple = c.multiple
                component.values = c.values

                # Copy properties to the link
                if component.link is not None:
                    link = component.link
                    link.pkey = component.pkey
                    link.fkey = component.lkey
                    link.alias = component.alias
                    link.actuate = component.actuate
                    link.autodelete = component.autodelete
                    link.multiple = component.multiple
                    self.links[link.name] = link

                self.components[alias] = component

            # Build query
            self.build_query(id=id, uid=uid, filter=filter, vars=vars)

        # Component - attach link table
        if linktable is not None:
            # Create as resource
            tn = linktable._tablename
            prefix, name = tn.split("_", 1)
            self.link = S3Resource(manager, prefix, name,
                                   parent=self.parent,
                                   linked=self,
                                   include_deleted=self.include_deleted)

        # CRUD
        self.crud = manager.crud()
        self.crud.resource = self

        # Pending Imports
        self.skip_import = False
        self.job = None
        self.error = None
        self.error_tree = None

        # Search
        self.search = model.get_config(self.tablename, "search_method", None)
        if not self.search:
            if "name" in self.table:
                T = current.T
                self.search = manager.search(
                                name="search_simple",
                                label=T("Name"),
                                comment=T("Enter a name to search for. You may use % as wildcard. Press 'Search' without input to list all items."),
                                field=["name"])
            else:
                self.search = manager.search()

        # Temporary fix
        self.resource = self

        # To be removed (to be replaced by _fquery)
        self.filter = None

    # -------------------------------------------------------------------------
    # Query handling
    # -------------------------------------------------------------------------
    def build_query(self, id=None, uid=None, filter=None, vars=None):
        """
            Query builder

            @param id: record ID or list of record IDs to include
            @param uid: record UID or list of record UIDs to include
            @param filter: filtering query (DAL only)
            @param vars: dict of URL query variables
        """

        # Reset the rows counter
        self._length = None

        return self.query_builder.query(self,
                                        id=id,
                                        uid=uid,
                                        filter=filter,
                                        vars=vars)

    # -------------------------------------------------------------------------
    def add_filter(self, filter=None):
        """
            Extend the current query by a filter query

            @param filter: a web2py Query object

            @todo: update to new query handling
        """

        if filter is not None:
            if self._query:
                query = self._query
                self.clear()
                self.clear_query()
                self._query = (query) & (filter)
            else:
                self.build_query(filter=filter)
        return self._query

    # -------------------------------------------------------------------------
    def add_component_filter(self, name, filter=None):
        """
            Extend the filter query of a particular component

            @param name: the name of the component
            @param filter: a web2py Query object

            @todo: update to new query handling
        """

        component = self.components.get(name, None)
        if component is not None:
            if component.filter is not None:
                component.filter = (component.filter) & (filter)
            else:
                component.filter = filter

    # -------------------------------------------------------------------------
    def get_query(self):
        """
            Get the current query for this resource
        """

        if not self._query:
            self.build_query()
        return self._query

    # -------------------------------------------------------------------------
    def clear_query(self):
        """
            Removes the current query (does not remove the set!)
        """

        self._query = None
        self._mquery = None
        self._cquery = Storage()
        self._cjoins = Storage()
        if self.components:
            for c in self.components:
                self.components[c].clear_query()

    # -------------------------------------------------------------------------
    # Data access
    # -------------------------------------------------------------------------
    def select(self, *fields, **attributes):
        """
            Select records with the current query

            @param fields: fields to select
            @param attributes: select attributes
        """

        db = current.db
        manager = current.manager
        table = self.table
        if self._query is None:
            self.build_query()
        # Get the rows
        rows = db(self._query).select(*fields, **attributes)
        # Audit
        audit = manager.audit
        try:
            # Audit "read" record by record
            if self.tablename in rows:
                ids = [r[str(self.table.id)] for r in rows]
            else:
                ids = [r.id for r in rows]
            for i in ids:
                audit("read", self.prefix, self.name, record=i)
        except KeyError:
            # Audit "list" if no IDs available
            audit("list", self.prefix, self.name)
        # Keep the rows for later access
        self._rows = rows
        self._slice = True
        return rows

    # -------------------------------------------------------------------------
    def load(self, start=None, limit=None):
        """
            Simplified syntax for select():
                - reads all fields
                - start+limit instead of limitby

            @param start: the index of the first record to load
            @param limit: the maximum number of records to load
        """

        manager = current.manager
        xml = manager.xml
        table = self.table

        if not len(table.virtualfields):
            if self.tablename == "gis_location":
                fields = [f for f in table if f.name != "wkt"]
            else:
                fields = [f for f in table]
        else:
            fields = None

        if self._rows is not None:
            self.clear()
        if not self._query:
            self.build_query()
        limitby = None
        if not self._multiple:
            if self.parent and self.parent.count() == 1:
                limitby = (0, 1)
        else:
            limitby = self.limitby(start=start, limit=limit)
        if limitby:
            if fields is not None:
                rows = self.select(limitby=limitby, *fields)
            else:
                rows = self.select(table.ALL, limitby=limitby)
            self._slice = True
        else:
            if fields is not None:
                rows = self.select(*fields)
            else:
                rows = self.select(table.ALL)
        self._ids = [row.id for row in rows]
        uid = manager.xml.UID
        if uid in table.fields:
            self._uids = [row[uid] for row in rows]
        return self

    # -------------------------------------------------------------------------
    def insert(self, **fields):
        """
            Insert a record into this resource

            @param fields: dict of field/value pairs to insert
        """

        # Check permission
        authorised = self.permit("create", self.tablename)
        if not authorised:
            raise IOError("Operation not permitted: INSERT INTO %s" %
                            self.tablename)

        # Insert new record
        record_id = self.table.insert(**fields)

        # Audit
        if record_id:
            record = Storage(fields).update(id=record_id)
            self.audit("create", self.prefix, self.name, form=record)

        return record_id

    # -------------------------------------------------------------------------
    def delete(self,
               ondelete=None,
               format=None,
               cascade=False):
        """
            Delete all (deletable) records in this resource

            @param ondelete: on-delete callback
            @param format: the representation format of the request (optional)

            @returns: number of records deleted
        """

        db = current.db
        manager = current.manager
        model = manager.model

        settings = manager.s3.crud
        archive_not_delete = settings.archive_not_delete

        table = self.table

        # Reset error
        manager.error = None

        # Get all rows
        if "uuid" in table.fields:
            rows = self.select(table.id, table.uuid)
        else:
            rows = self.select(table.id)

        if not rows:
            # No rows in this resource => return success here
            return 0

        numrows = 0 # number of rows deleted
        if archive_not_delete and "deleted" in self.table:

            # Don't delete, but set deleted-flag

            # Find deletable rows
            references = self.table._referenced_by
            rfields = [(tn, fn) for tn, fn in references
                                if db[tn][fn].ondelete == "RESTRICT"]
            restricted = []
            ids = [row.id for row in rows]
            for tn, fn in rfields:
                rtable = db[tn]
                rfield = rtable[fn]
                query = (rfield.belongs(ids))
                if "deleted" in rtable:
                    query &= (rtable.deleted != True)
                rrows = db(query).select(rfield)
                restricted += [r[fn] for r in rrows if r[fn] not in restricted]
            deletable = [row.id for row in rows if row.id not in restricted]


            # Get custom ondelete-cascade
            ondelete_cascade = model.get_config(self.tablename, "ondelete_cascade")

            for row in rows:

                # Check permission to delete this row
                if not self.permit("delete", self.table, record_id=row.id):
                    continue

                # Store prior error
                error = manager.error
                manager.error = None

                # Run custom ondelete_cascade
                if ondelete_cascade:
                    callback(ondelete_cascade, row, tablename=self.tablename)
                    if manager.error:
                        # Row is not deletable
                        continue
                    if row.id not in deletable:
                        # Check deletability again
                        restrict = False
                        for tn, fn in rfields:
                            rtable = db[tn]
                            rfield = rtable[fn]
                            query = (rfield == row.id)
                            if "deleted" in rtable:
                                query &= (rtable.deleted != True)
                            rrow = db(query).select(rfield,
                                                    limitby=(0, 1)).first()
                            if rrow:
                                restrict = True
                        if not restrict:
                            deletable.append(row.id)

                if row.id not in deletable:
                    # Row is not deletable => skip with error status
                    manager.error = self.ERROR.INTEGRITY_ERROR
                    continue

                for tn, fn in references:
                    rtable = db[tn]
                    rfield = rtable[fn]

                    if rfield.ondelete == "CASCADE":

                        # Delete the referencing records
                        rprefix, rname = tn.split("_", 1)
                        query = rfield == row.id
                        rresource = manager.define_resource(rprefix, rname, filter=query)
                        ondelete = model.get_config(tn, "ondelete")
                        rresource.delete(ondelete=ondelete, cascade=True)

                        if manager.error:
                            # Can't delete the reference
                            break

                    elif rfield.ondelete == "SET NULL":
                        try:
                            db(rfield == row.id).update(**{fn:None})
                        except:
                            # Can't set the reference to None
                            manager.error = self.ERROR.INTEGRITY_ERROR
                            break

                    elif rfield.ondelete == "SET DEFAULT":
                        try:
                            db(rfield == row.id).update(**{fn:rfield.default})
                        except:
                            # Can't set the reference to default value
                            manager.error = self.ERROR.INTEGRITY_ERROR
                            break

                if manager.error:
                    # Rollback all cascade actions on error
                    if not cascade:
                        db.rollback()
                    continue

                else:
                    # Cascade successful!

                    # Linked table auto-delete
                    component = self.linked
                    if component and self.autodelete and component.autodelete:
                        rkey = component.rkey
                        if rkey in table:
                            this = db(table._id == row[table._id.name]).select(table._id, table[rkey],
                                                                               limitby=(0, 1)).first()
                            query = (table._id != this[table._id.name]) & \
                                    (table[rkey] == this[rkey])
                            if "deleted" in table:
                                query != (table.deleted != True)
                            remaining = db(query).select(table._id, limitby=(0, 1)).first()
                            if not remaining:
                                query = component.table[component.fkey] == this[rkey]
                                linked = manager.define_resource(component.prefix,
                                                                 component.name,
                                                                 filter=query)
                                ondelete = model.get_config(component.tablename, "ondelete")
                                linked.delete(ondelete=ondelete, cascade=True)

                    # Clear session
                    if manager.get_session(prefix=self.prefix,
                                           name=self.name) == row.id:
                        manager.clear_session(prefix=self.prefix, name=self.name)

                    # Pull back prior error status
                    manager.error = error
                    error = None

                    # Collect fields
                    fields = dict(deleted=True)

                    if "deleted_fk" in self.table:
                        # "Park" foreign keys to resolve constraints,
                        # "un-delete" will have to restore valid FKs
                        # from this field!
                        record = self.table[row.id]
                        fk = {}
                        for f in self.table.fields:
                            ftype = str(self.table[f].type)
                            if record[f] is not None and \
                                (ftype[:9] == "reference" or \
                                 ftype[:14] == "list:reference"):
                                fk[f] = record[f]
                                fields[f] = None
                            else:
                                continue
                        if fk:
                            fields.update(deleted_fk=json.dumps(fk))

                    # Update the row to set deleted=True, finally
                    db(self.table.id == row.id).update(**fields)

                    numrows += 1
                    self.audit("delete", self.prefix, self.name,
                                record=row.id, representation=format)
                    model.delete_super(self.table, row)
                    if ondelete:
                        callback(ondelete, row)

                    # Commit after each row to not be rolled back by
                    # subsequent cascade errors
                    if not cascade:
                        db.commit()

        else:
            # Hard delete
            for row in rows:

                # Check permission to delete this row
                if not self.permit("delete", self.table, record_id=row.id):
                    continue

                # Clear session
                if manager.get_session(prefix=self.prefix,
                                       name=self.name) == row.id:
                    manager.clear_session(prefix=self.prefix, name=self.name)

                try:
                    del table[row.id]
                except:
                    # Row is not deletable
                    manager.error = self.ERROR.INTEGRITY_ERROR
                    continue
                else:
                    # Successfully deleted
                    numrows += 1
                    self.audit("delete", self.prefix, self.name,
                                record=row.id, representation=format)
                    model.delete_super(self.table, row)
                    if ondelete:
                        callback(ondelete, row)

        if numrows == 0 and not deletable:
            # No deletable rows found
            manager.error = self.ERROR.INTEGRITY_ERROR

        return numrows

    # -------------------------------------------------------------------------
    def update(self, **update_fields):
        """
            Update all records in this resource

            @todo: permission check
            @todo: audit

            @status: uncompleted
            @todo: implement audit
        """

        if not self._query:
            self.build_query()

        success = current.db(self._query).update(**update_fields)
        return success

    # -------------------------------------------------------------------------
    def count(self, left=None, distinct=False):
        """
            Get the total number of available records in this resource

            @param left: left joins, if required
        """

        db = current.db
        if not self._query:
            self.build_query()
        if self._length is None:
            if distinct:
                rows = db(self._query).select(self.table._id,
                                              left=left,
                                              distinct=distinct)
                self._length = len(rows)
            else:
                cnt = self.table[self.table.fields[0]].count()
                row = db(self._query).select(cnt, left=left).first()
                if row:
                    self._length = row[cnt]
        return self._length

    # -------------------------------------------------------------------------
    def clear(self):
        """
            Removes the current set
        """

        self._rows = None
        self._length = None
        self._ids = []
        self._uids = []
        self.files = Storage()
        self._slice = False

        if self.components:
            for c in self.components:
                self.components[c].clear()

    # -------------------------------------------------------------------------
    def records(self, fields=None):
        """
            Get the current set

            @returns: a Set or an empty list if no set is loaded
        """

        if self._rows is None:
            return Rows(current.db)
        else:
            if fields is not None:
                self._rows.colnames = map(str, fields)
            return self._rows

    # -------------------------------------------------------------------------
    def __getitem__(self, key):
        """
            Retrieves a record from the current set by its ID

            @param key: the record ID
            @returns: a Row
        """

        if self._rows is None:
            self.load()
        for i in xrange(len(self._rows)):
            row = self._rows[i]
            if str(row.id) == str(key):
                return row

        raise IndexError

    # -------------------------------------------------------------------------
    def __iter__(self):
        """
            Iterate over the selected rows
        """

        if self._rows is None:
            self.load()
        for i in xrange(len(self._rows)):
            yield self._rows[i]
        return

    # -------------------------------------------------------------------------
    def __call__(self, key, component=None):
        """
            Retrieves component records of a record in the current set

            @param key: the record ID
            @param component: the name of the component
                (None to get the primary record)
            @returns: a record (if component is None) or a list of records
        """

        if not component:
            return self[key]
        else:
            if isinstance(key, Row):
                master = key
            else:
                master = self[key]
            if isinstance(component, S3Resource):
                c = component
            elif component in self.components:
                c = self.components[component]
            elif component in self.links:
                c = self.links[component]
            else:
                raise AttributeError
            if c.link:
                pkey, fkey = c.pkey, c.fkey
                lkey, rkey = c.lkey, c.rkey
                lids = [r[rkey] for r in c.link if master[pkey] == r[lkey]]
                rows = [record for record in c if record[fkey] in lids]
            else:
                pkey, fkey = c.pkey, c.fkey
                rows = [record for record in c if master[pkey] == record[fkey]]
            return rows

    # -------------------------------------------------------------------------
    def get_id(self):
        """
            Returns all IDs of the current set, or, if no set is loaded,
            all IDs of the resource

            @returns: a list of record IDs
        """

        if not self._ids:
            self.__load_ids()
        if not self._ids:
            return None
        elif len(self._ids) == 1:
            return self._ids[0]
        else:
            return self._ids

    # -------------------------------------------------------------------------
    def get_uid(self):
        """
            Returns all UIDs of the current set, or, if no set is loaded,
            all UIDs of the resource

            @returns: a list of record UIDs
        """

        manager = current.manager
        if manager.xml.UID not in self.table.fields:
            return None

        if not self._uids:
            self.__load_ids()
        if not self._uids:
            return None
        elif len(self._uids) == 1:
            return self._uids[0]
        else:
            return self._uids

    # -------------------------------------------------------------------------
    def __load_ids(self):
        """
            Loads the IDs of all records matching the master query, or,
            if no query is given, all IDs in the primary table
        """

        uid = current.manager.xml.UID

        if self._query is None:
            self.build_query()
        if uid in self.table.fields:
            fields = (self.table.id, self.table[uid])
        else:
            fields = (self.table.id, )

        rows = current.db(self._query).select(*fields)

        self._ids = [row.id for row in rows]

        if uid in self.table.fields:
            self._uids = [row[uid] for row in rows]

    # -------------------------------------------------------------------------
    # Representation
    # -------------------------------------------------------------------------
    def __repr__(self):
        """
            String representation of this resource
        """

        if self._rows:
            ids = [r.id for r in self]
            return "<S3Resource %s %s>" % (self.tablename, ids)
        else:
            return "<S3Resource %s>" % self.tablename

    # -------------------------------------------------------------------------
    def __len__(self):
        """
            The number of currently loaded rows
        """

        if self._rows is not None:
            return len(self._rows)
        else:
            return 0

    # -------------------------------------------------------------------------
    def __nonzero__(self):
        """
            Boolean test of this resource
        """

        return self is not None

    # -------------------------------------------------------------------------
    def __contains__(self, item):
        """
            Tests whether a record is currently loaded
        """

        id = item.get("id", None)
        uid = item.get(current.manager.xml.UID, None)

        if (id or uid) and not self._ids:
            self.__load_ids()
        if id and id in self._ids:
            return 1
        elif uid and uid in self._uids:
            return 1
        else:
            return 0

    # -------------------------------------------------------------------------
    # XML Export
    # -------------------------------------------------------------------------
    def export_xml(self,
                   start=None,
                   limit=None,
                   msince=None,
                   marker=None,
                   dereference=True,
                   mcomponents=None,
                   rcomponents=None,
                   stylesheet=None,
                   as_tree=False,
                   as_json=False,
                   pretty_print=False, **args):
        """
            Export this resource as S3XML

            @param start: index of the first record to export (slicing)
            @param limit: maximum number of records to export (slicing)
            @param msince: export only records which have been modified
                            after this datetime
            @param marker: URL of the default map marker
            @param dereference: include referenced resources
            @param mcomponents: components of the master resource to
                                include (list of tablenames), empty list
                                for all
            @param rcomponents: components of referenced resources to
                                include (list of tablenames), empty list
                                for all
            @param stylesheet: path to the XSLT stylesheet (if required)
            @param as_tree: return the ElementTree (do not convert into string)
            @param as_json: represent the XML tree as JSON
            @param pretty_print: insert newlines/indentation in the output
            @param args: dict of arguments to pass to the XSLT stylesheet
        """

        import uuid

        manager = current.manager
        xml = manager.xml

        output = None
        args = Storage(args)

        # Export as element tree
        tree = self.export_tree(start=start,
                                limit=limit,
                                msince=msince,
                                marker=marker,
                                dereference=dereference,
                                mcomponents=mcomponents,
                                rcomponents=rcomponents)

        # XSLT transformation
        if tree and stylesheet is not None:
            tfmt = xml.ISOFORMAT
            args.update(domain=manager.domain,
                        base_url=manager.s3.base_url,
                        prefix=self.prefix,
                        name=self.name,
                        utcnow=datetime.datetime.utcnow().strftime(tfmt),
                        msguid=uuid.uuid4().urn)
            tree = xml.transform(tree, stylesheet, **args)

        # Convert into the requested format
        # (Content Headers are set by the calling function)
        if tree:
            if as_tree:
                output = tree
            elif as_json:
                output = xml.tree2json(tree, pretty_print=pretty_print)
            else:
                output = xml.tostring(tree, pretty_print=pretty_print)

        return output

    # -------------------------------------------------------------------------
    def export_tree(self,
                    start=0,
                    limit=None,
                    skip=[],
                    msince=None,
                    marker=None,
                    dereference=True,
                    mcomponents=None,
                    rcomponents=None):
        """
            Export the resource as element tree

            @param start: index of the first record to export
            @param limit: maximum number of records to export
            @param msince: minimum modification date of the records
            @param marker: URL of the default marker
            @param skip: list of fieldnames to skip
            @param show_urls: show record URLs in the export
            @param mcomponents: components of the master resource to
                                include (list of tablenames), empty list
                                for all
            @param rcomponents: components of referenced resources to
                                include (list of tablenames), empty list
                                for all
            @param dereference: also export referenced records

        """

        db = current.db
        gis = current.gis
        request = current.request

        manager = current.manager
        model = manager.model
        xml = manager.xml
        audit = manager.audit

        if manager.show_urls:
            base_url = manager.s3.base_url
        else:
            base_url = None

        # Split reference/data fields
        (rfields, dfields) = self.split_fields(skip=skip)

        # Filter for MCI>=0 (setting)
        table = self.table
        if xml.filter_mci and "mci" in table.fields:
            mci_filter = (table.mci >= 0)
            self.add_filter(mci_filter)

        # Total number of results
        results = self.count()

        # Load slice
        self.load(start=start, limit=limit)

        # See if we're being called as a GIS Feature Layer
        (popup_label, popup_fields) = gis.get_popup()

        # Build the tree
        root = etree.Element(xml.TAG.root)
        export_map = Storage()
        reference_map = []
        for record in self:
            element = self.__export_resource(record,
                                             rfields=rfields,
                                             dfields=dfields,
                                             parent=root,
                                             base_url=base_url,
                                             reference_map=reference_map,
                                             export_map=export_map,
                                             components=mcomponents,
                                             skip=skip,
                                             msince=msince,
                                             marker=marker,
                                             popup_label=popup_label,
                                             popup_fields=popup_fields)
            if element is None:
                results -= 1

        # Add referenced resources to the tree
        depth = dereference and manager.MAX_DEPTH or 0
        while reference_map and depth:
            depth -= 1
            load_map = dict()
            for ref in reference_map:
                if "table" in ref and "id" in ref:
                    tname = ref["table"]
                    ids = ref["id"]
                    if not isinstance(ids, list):
                        ids = [ids]
                    # Exclude records which are already in the tree
                    exported = export_map.get(tname, [])
                    ids = [x for x in ids if x not in exported]
                    if not ids:
                        continue
                    # Append the new ids to load_map[tname]
                    if tname in load_map:
                        ids = [x for x in ids if x not in load_map[tname]]
                        load_map[tname] += ids
                    else:
                        load_map[tname] = ids

            reference_map = []
            for tablename in load_map:
                load_list = load_map[tablename]
                prefix, name = tablename.split("_", 1)
                rresource = manager.define_resource(prefix, name,
                                                    id=load_list,
                                                    components=[])
                table = rresource.table
                if manager.s3.base_url:
                    url = "%s/%s/%s" % (manager.s3.base_url, prefix, name)
                else:
                    url = "/%s/%s" % (prefix, name)
                rfields, dfields = rresource.split_fields(skip=skip)
                rresource.load()
                for record in rresource:
                    element = rresource.__export_resource(
                                            record,
                                            rfields=rfields,
                                            dfields=dfields,
                                            parent=root,
                                            base_url=base_url,
                                            reference_map=reference_map,
                                            export_map=export_map,
                                            components=rcomponents,
                                            skip=skip,
                                            msince=msince,
                                            marker=marker)

                    # Mark as referenced element (for XSLT)
                    if element is not None:
                        element.set(xml.ATTRIBUTE.ref, "True")

        # Complete the tree
        return xml.tree(None,
                        root=root,
                        domain=manager.domain,
                        url=base_url,
                        results=results,
                        start=start,
                        limit=limit)

    # -------------------------------------------------------------------------
    def __export_resource(self,
                          record,
                          rfields=[],
                          dfields=[],
                          parent=None,
                          base_url=None,
                          reference_map=None,
                          export_map=None,
                          components=None,
                          skip=[],
                          msince=None,
                          marker=None,
                          popup_label=None,
                          popup_fields=None):
        """
            Add a <resource> to the element tree

            @param record: the record
            @param rfields: list of reference fields to export
            @param dfields: list of data fields to export
            @param parent: the parent element
            @param base_url: the base URL of the resource
            @param reference_map: the reference map of the request
            @param export_map: the export map of the request
            @param components: list of components to include from referenced
                               resources (tablenames)
            @param skip: fields to skip
            @param msince: the minimum update datetime for exported records
            @param marker: the GIS default marker URL
            @param popup_label: the popup label for GIS encoding
            @param popup_fields: the popup fields for GIS encoding
        """

        manager = current.manager
        xml = manager.xml
        download_url = manager.s3.download_url

        action = "read"
        representation = "xml"

        # Construct the record URL
        if base_url:
            record_url = "%s/%s" % (base_url, record.id)
        else:
            record_url = None

        # Export the record
        add = False
        element, rmap = self.__export_record(record,
                                             rfields=rfields,
                                             dfields=dfields,
                                             parent=parent,
                                             export_map=export_map,
                                             url=record_url,
                                             msince=msince,
                                             marker=marker,
                                             popup_label=popup_label,
                                             popup_fields=popup_fields)
        if element is not None:
            add = True

        # Export components
        if components is not None:
            for component in self.components.values():

                # Shall this component be included?
                if components and component.tablename not in components:
                    continue

                # Add MCI filter to component
                ctable = component.table
                if xml.filter_mci and xml.MCI in ctable.fields:
                    mci_filter = (ctable[xml.MCI] >= 0)
                    component.add_filter(mci_filter)

                # Split fields
                _skip = skip+[component.fkey]
                crfields, cdfields = component.split_fields(skip=_skip)

                # Load records if necessary
                if component._rows is None:
                    component.load()

                # Construct the component base URL
                if record_url:
                    component_url = "%s/%s" % (record_url, component.alias)
                else:
                    component_url = None

                # Find related records
                crecords = self(record.id, component=component.alias)
                if not component.multiple and len(crecords):
                    crecords = [crecords[0]]

                # Export records
                for crecord in crecords:
                    # Construct the component record URL
                    if component_url:
                        crecord_url = "%s/%s" % (component_url, crecord.id)
                    else:
                        crecord_url = None
                    # Export the component record
                    celement, crmap = component.__export_record(
                                            crecord,
                                            rfields=crfields,
                                            dfields=cdfields,
                                            parent=element,
                                            export_map=export_map,
                                            url=crecord_url,
                                            msince=msince,
                                            marker=marker)
                    if celement is not None:
                        add = True # keep the parent record
                        component.__map_record(crecord, crmap,
                                               reference_map, export_map)

        # Update reference_map and export_map
        if add:
            self.__map_record(record, rmap, reference_map, export_map)
        elif parent is not None and element is not None:
            idx = parent.index(element)
            if idx:
                del parent[idx]
            return None

        return element

    # -------------------------------------------------------------------------
    def __export_record(self,
                        record,
                        rfields=[],
                        dfields=[],
                        parent=None,
                        export_map=None,
                        url=None,
                        msince=None,
                        marker=None,
                        popup_label=None,
                        popup_fields=None):
        """
            Exports a single record to the element tree.

            @param record: the record
            @param rfields: list of foreign key fields to export
            @param dfields: list of data fields to export
            @param parent: the parent element
            @param export_map: the export map of the current request
            @param url: URL of the record
            @param msince: minimum last update time
            @param marker: GIS marker URL
            @param popup_label: the popup label for GIS encoding
            @param popup_fields: the popup fields for GIS encoding
        """

        manager = current.manager
        xml = manager.xml

        tablename = self.tablename
        table = self.table

        # Do not export the record if it already is in the export map
        if tablename in export_map and record.id in export_map[tablename]:
            return (None, None)

        # Do not export the record if it hasn't been modified since msince
        if msince is not None:
            if xml.MTIME in record and record[xml.MTIME] <= msince:
                return (None, None)

        # Audit read
        prefix = self.prefix
        name = self.name
        audit = manager.audit
        if audit:
            audit("read", prefix, name,
                  record=record.id, representation="xml")

        # Reference map for this record
        rmap = xml.rmap(table, record, rfields)

        # Generate the element
        element = xml.resource(parent, table, record,
                               fields=dfields,
                               url=url)
        # Add the references
        xml.add_references(element, rmap,
                           show_ids=manager.show_ids)

        # GIS-encode the element
        download_url = manager.s3.download_url
        xml.gis_encode(self, record, rmap,
                       download_url=download_url,
                       popup_label=popup_label,
                       popup_fields=popup_fields,
                       marker=marker)

        return (element, rmap)

    # -------------------------------------------------------------------------
    def __map_record(self, record, rmap, reference_map, export_map):
        """
            Add the record to the export map, and update the
            reference map with the record's references

            @param record: the record
            @param rmap: the reference map of the record
            @param reference_map: the reference map of the request
            @param export_map: the export map of the request
        """

        tablename = self.tablename

        if rmap:
            reference_map.extend(rmap)
        if export_map.get(self.tablename, None):
            export_map[self.tablename].append(record.id)
        else:
            export_map[self.tablename] = [record.id]
        return

    # -------------------------------------------------------------------------
    # XML Import
    # -------------------------------------------------------------------------
    def import_xml(self, source,
                   files=None,
                   id=None,
                   format="xml",
                   stylesheet=None,
                   extra_data=None,
                   ignore_errors=False,
                   job_id=None,
                   commit_job=True,
                   delete_job=False,
                   strategy=None,
                   update_policy=None,
                   conflict_policy=None,
                   last_sync=None,
                   onconflict=None,
                   **args):
        """
            XML Importer

            @param source: the data source, accepts source=xxx, source=[xxx, yyy, zzz] or
                           source=[(resourcename1, xxx), (resourcename2, yyy)], where the
                           xxx has to be either an ElementTree or a file-like object
            @param files: attached files (None to read in the HTTP request)
            @param id: ID (or list of IDs) of the record(s) to update (performs only update)
            @param format: type of source = "xml", "json" or "csv"
            @param stylesheet: stylesheet to use for transformation
            @param extra_data: for CSV imports, dict of extra cols to add to each row
            @param ignore_errors: skip invalid records silently
            @param job_id: resume from previous import job_id
            @param commit_job: commit the job to the database
            @param delete_job: delete the import job from the queue
            @param strategy: tuple of allowed import methods (create/update/delete)
            @param update_policy: policy for updates (sync)
            @param conflict_policy: policy for conflict resolution (sync)
            @param last_sync: last synchronization datetime (sync)
            @param onconflict: callback hook for conflict resolution (sync)
            @param args: parameters to pass to the transformation stylesheet
        """

        manager = current.manager
        xml = manager.xml
        permit = manager.permit

        tree = None

        self.job = None

        # Check permission for the resource
        authorised = permit("create", self.table) and \
                     permit("update", self.table)
        if not authorised:
            raise IOError("Insufficient permissions")

        if not job_id:

            # Resource data
            prefix = self.prefix
            name = self.name

            # Additional stylesheet parameters
            tfmt = xml.ISOFORMAT
            utcnow = datetime.datetime.utcnow().strftime(tfmt)
            domain = manager.domain
            base_url = manager.s3.base_url
            args.update(domain=domain,
                        base_url=base_url,
                        prefix=prefix,
                        name=name,
                        utcnow=utcnow)

            # Build import tree
            if not isinstance(source, (list, tuple)):
                source = [source]
            for item in source:
                if isinstance(item, (list, tuple)):
                    resourcename, s = item[:2]
                else:
                    resourcename, s = None, item
                if isinstance(s, etree._ElementTree):
                    t = s
                elif format == "json":
                    if isinstance(s, basestring):
                        source = StringIO(s)
                        t = xml.json2tree(s)
                    else:
                        t = xml.json2tree(s)
                elif format == "csv":
                    t = xml.csv2tree(s,
                                     resourcename=resourcename,
                                     extra_data=extra_data)
                else:
                    t = xml.parse(s)
                if not t:
                    if xml.error:
                        raise SyntaxError(xml.error)
                    else:
                        raise SyntaxError("Invalid source")

                if stylesheet is not None:
                    t = xml.transform(t, stylesheet, **args)
                    if not t:
                        raise SyntaxError(xml.error)

                if not tree:
                    tree = t.getroot()
                else:
                    tree.extend(list(t.getroot()))

            if files is not None and isinstance(files, dict):
                self.files = Storage(files)

        else:
            # job ID given
            pass

        success = self.import_tree(id, tree,
                                   ignore_errors=ignore_errors,
                                   job_id=job_id,
                                   commit_job=commit_job,
                                   delete_job=delete_job,
                                   strategy=strategy,
                                   update_policy=update_policy,
                                   conflict_policy=conflict_policy,
                                   last_sync=last_sync,
                                   onconflict=onconflict)

        self.files = Storage()

        # Response message
        if format == "json":
            # Whilst all Responses are JSON, it's easier to debug by having the
            # response appear in the browser than launching a text editor
            current.response.headers["Content-Type"] = "application/json"
        if self.error_tree is not None:
            tree = xml.tree2json(self.error_tree)
        else:
            tree = None
        if success is True:
            return xml.json_message(message=self.error, tree=tree)
        elif success and hasattr(success, "job_id"):
            self.job = success
            return xml.json_message(message=self.error, tree=tree)
        else:
            return xml.json_message(False, 400,
                                    message=self.error, tree=tree)

    # -------------------------------------------------------------------------
    def import_tree(self, id, tree,
                    job_id=None,
                    ignore_errors=False,
                    delete_job=False,
                    commit_job=True,
                    strategy=None,
                    update_policy=None,
                    conflict_policy=None,
                    last_sync=None,
                    onconflict=None):
        """
            Import data from an S3XML element tree.

            @param id: record ID or list of record IDs to update
            @param tree: the element tree
            @param ignore_errors: continue at errors (=skip invalid elements)

            @param job_id: restore a job from the job table (ID or UID)
            @param delete_job: delete the import job from the job table
            @param commit_job: commit the job (default)

            @todo: update for link table support
        """

        manager = current.manager
        db = current.db
        xml = manager.xml
        permit = manager.auth.s3_has_permission
        audit = manager.audit
        tablename = self.tablename
        table = self.table

        if job_id is not None:

            # Restore a job from the job table
            self.error = None
            self.error_tree = None
            try:
                import_job = S3ImportJob(manager, table,
                                         job_id=job_id,
                                         strategy=strategy,
                                         update_policy=update_policy,
                                         conflict_policy=conflict_policy,
                                         last_sync=last_sync,
                                         onconflict=onconflict)
            except:
                self.error = self.ERROR.BAD_SOURCE
                return False

            # Delete the job?
            if delete_job:
                import_job.delete()
                return True

            # Load all items
            job_id = import_job.job_id
            item_table = import_job.item_table
            items = db(item_table.job_id == job_id).select()
            for item in items:
                success = import_job.load_item(item)
                if not success:
                    self.error = import_job.error
                    self.error_tree = import_job.error_tree
            import_job.restore_references()

            # this is only relevant for commit_job=True
            if commit_job:
                if self.error and not ignore_errors:
                    return False
            else:
                return import_job

            # Call the import pre-processor to prepare tables
            # and cleanup the tree as necessary
            if manager.import_prep:
                tree = import_job.get_tree()
                callback(manager.import_prep,
                         # takes tuple (resource, tree) as argument
                         (self, tree),
                         tablename=tablename)
                # Skip import?
                if self.skip_import:
                    _debug("Skipping import to %s" % self.tablename)
                    self.skip_import = False
                    return True

        else:
            # Create a new job from an element tree
            # Do not import into tables without "id" field
            if "id" not in table.fields:
                self.error = self.ERROR.BAD_RESOURCE
                return False

            # Reset error and error tree
            self.error = None
            self.error_tree = None

            # Call the import pre-processor to prepare tables
            # and cleanup the tree as necessary
            if manager.import_prep:
                if not isinstance(tree, etree._ElementTree):
                    tree = etree.ElementTree(tree)
                callback(manager.import_prep,
                         # takes tuple (resource, tree) as argument
                         (self, tree),
                         tablename=tablename)
                # Skip import?
                if self.skip_import:
                    _debug("Skipping import to %s" % self.tablename)
                    self.skip_import = False
                    return True

            # Select the elements for this table
            elements = xml.select_resources(tree, tablename)
            if not elements:
                # nothing to import => still ok
                return True

            # Find matching elements, if a target record ID is given
            UID = xml.UID
            if id and UID in table:
                if not isinstance(id, (tuple, list)):
                    query = (table.id == id)
                else:
                    query = (table.id.belongs(id))
                originals = db(query).select(table[UID])
                uids = [row[UID] for row in originals]
                matches = []
                for element in elements:
                    element_uid = xml.import_uid(element.get(UID, None))
                    if not element_uid:
                        continue
                    if element_uid in uids:
                        matches.append(element)
                if not matches:
                    first = elements[0]
                    if len(elements) and not first.get(UID, None):
                        first.set(UID, uids[0])
                        matches = [first]
                if not matches:
                    self.error = self.ERROR.NO_MATCH
                    return False
                else:
                    elements = matches

            # Import all matching elements
            import_job = S3ImportJob(manager, table,
                                     tree=tree,
                                     files=self.files,
                                     strategy=strategy,
                                     update_policy=update_policy,
                                     conflict_policy=conflict_policy,
                                     last_sync=last_sync,
                                     onconflict=onconflict)
            for element in elements:
                success = import_job.add_item(element=element,
                                              components=self.components)
                if not success:
                    self.error = import_job.error
                    self.error_tree = import_job.error_tree
            if self.error and not ignore_errors:
                return False

        # Commit the import job
        import_job.commit(ignore_errors=ignore_errors)
        self.error = import_job.error
        if self.error:
            if ignore_errors:
                self.error = "%s - invalid items ignored" % self.error
            self.error_tree = import_job.error_tree
        if not commit_job:
            db.rollback()
            import_job.store()
            return import_job
        else:
            # Remove the job when committed
            if job_id is not None:
                import_job.delete()

        return self.error is None or ignore_errors

    # -------------------------------------------------------------------------
    # XML introspection
    # -------------------------------------------------------------------------
    def options(self,
                component=None,
                fields=None,
                only_last=False,
                show_uids=False,
                as_json=False):
        """
            Export field options of this resource as element tree

            @param component: name of the component which the options are
                requested of, None for the primary table
            @param fields: list of names of fields for which the options
                are requested, None for all fields (which have options)
            @param as_json: convert the output into JSON
            @param only_last: Obtain the latest record (performance bug fix,
                timeout at s3_tb_refresh for non-dropdown form fields)
        """

        db = current.db

        if component is not None:
            c = self.components.get(component, None)
            if c:
                tree = c.options(fields=fields,
                                 only_last=only_last,
                                 show_uids=show_uids,
                                 as_json=as_json)
                return tree
            else:
                raise AttributeError
        else:
            if as_json and only_last and len(fields) == 1:
                component_tablename = "%s_%s" % (self.prefix, self.name)
                field = db[component_tablename][fields[0]]
                req = field.requires
                if isinstance(req, IS_EMPTY_OR):
                    req = req.other
                if not isinstance(req, IS_ONE_OF):
                    raise RuntimeError, "not isinstance(req, IS_ONE_OF)"
                rows = db().select(db[req.ktable][req.kfield],
                                   orderby=~db[req.ktable][req.kfield],
                                   limitby=(0, 1))
                res = []
                for row in rows:
                    val = row[req.kfield]
                    represent = field.represent(val)
                    if isinstance(represent, A):
                        represent = represent.components[0]
                    res.append({"@value": val, "$": represent})
                return json.dumps({'option': res})

            tree = self.xml.get_options(self.prefix,
                                        self.name,
                                        show_uids=show_uids,
                                        fields=fields)

            if as_json:
                return self.xml.tree2json(tree, pretty_print=False)
            else:
                return self.xml.tostring(tree, pretty_print=False)

    # -------------------------------------------------------------------------
    def fields(self, component=None, as_json=False):
        """
            Export a list of fields in the resource as element tree

            @param component: name of the component to lookup the fields
                              (None for primary table)
            @param as_json: convert the output XML into JSON
        """

        if component is not None:
            c = self.components.get(component, None)
            if c:
                tree = c.fields()
                return tree
            else:
                raise AttributeError
        else:
            tree = self.xml.get_fields(self.prefix, self.name)

            if as_json:
                return self.xml.tree2json(tree, pretty_print=True)
            else:
                return self.xml.tostring(tree, pretty_print=True)

    # -------------------------------------------------------------------------
    def struct(self,
               meta=False,
               options=False,
               references=False,
               stylesheet=None,
               as_json=False,
               as_tree=False):
        """
            Get the structure of the resource

            @param options: include option lists in option fields
            @param references: include option lists even for reference fields
            @param stylesheet: the stylesheet to use for transformation
            @param as_json: convert into JSON after transformation
        """

        manager = current.manager
        xml = manager.xml

        # Get the structure of the main resource
        root = etree.Element(xml.TAG.root)
        main = xml.get_struct(self.prefix, self.name,
                              parent=root,
                              meta=meta,
                              options=options,
                              references=references)

        # Include the selected components
        for component in self.components.values():
            prefix = component.prefix
            name = component.name
            sub = xml.get_struct(prefix, name,
                                 parent=main,
                                 meta=meta,
                                 options=options,
                                 references=references)

        # Transformation
        tree = etree.ElementTree(root)
        if stylesheet is not None:
            tfmt = xml.ISOFORMAT
            args = dict(domain=manager.domain,
                        base_url=manager.s3.base_url,
                        prefix=self.prefix,
                        name=self.name,
                        utcnow=datetime.datetime.utcnow().strftime(tfmt))

            tree = xml.transform(tree, stylesheet, **args)
            if tree is None:
                return None

        # Return tree if requested
        if as_tree:
            return tree

        # Otherwise string-ify it
        if as_json:
            return xml.tree2json(tree, pretty_print=True)
        else:
            return xml.tostring(tree, pretty_print=True)

    # -------------------------------------------------------------------------
    # Utility functions
    # -------------------------------------------------------------------------
    def readable_fields(self, subset=None):
        """
            Get a list of all readable fields in the resource table

            @param subset: list of fieldnames to limit the selection to
        """

        fkey = None
        table = self.table

        if self.parent and self.linked is None:
            component = self.parent.components.get(self.name, None)
            if component:
                fkey = component.fkey
        elif self.linked is not None:
            component = self.linked
            if component:
                fkey = component.lkey

        if subset:
            return [table[f] for f in subset
                    if f in table.fields and table[f].readable and f != fkey]
        else:
            return [table[f] for f in table.fields
                    if table[f].readable and f != fkey]

    # -------------------------------------------------------------------------
    @staticmethod
    def get_list_fields(table, fields):
        """
            Helper to resolve list_fields

            @param table: the table
            @param fields: the list_fields array
        """

        db = current.db
        tablename = table._tablename

        joins = dict()
        lfields = []

        # Collect the extra fields
        flist = list(fields)
        for vtable in table.virtualfields:
            try:
                extra_fields = vtable.extra_fields
                for ef in extra_fields:
                    if ef not in flist:
                        flist.append(ef)
            except:
                continue

        for f in flist:
            # Allow to override the field label
            if isinstance(f, tuple):
                label, fieldname = f
            else:
                label, fieldname = None, f
            field = None
            tname = tablename
            fname = fieldname
            if "$" in fieldname:
                # Field in referenced table
                fk, fname = fieldname.split("$", 1)
                if fk in table.fields:
                    ftype = str(table[fk].type)
                    if ftype[:9] == "reference":
                        tname = ftype[10:]
                        ftable = db[tname]
                        if fname in ftable.fields:
                            field = ftable[fname]
                            if fk not in joins:
                                join = (table[fk] == ftable._id)
                                if "deleted" in ftable.fields:
                                    join &= (ftable.deleted != True)
                                joins[fk] = join
                if field is None:
                    continue
                if label is None:
                    label = field.label
            elif fieldname in table.fields:
                # Field in this table
                field = table[fieldname]
                if label is None:
                    label = field.label
            else:
                # Virtual field?
                if label is None:
                    label = fname.capitalize()
            colname = "%s.%s" % (tname, fname)
            lfields.append(Storage(fieldname = fieldname,
                                   tname = tname,
                                   fname = fname,
                                   colname = colname,
                                   field = field,
                                   label = label,
                                   show = f in fields))

        return (lfields, joins)

    # -------------------------------------------------------------------------
    def split_fields(self, skip=[]):
        """
            Split the readable fields in the resource table into
            reference and non-reference fields.

            @param skip: list of field names to skip
        """

        manager = current.manager
        xml = manager.xml

        table = self.table
        tablename = self.tablename

        if tablename == "gis_location" and "wkt" not in skip:
            # Skip Bulky WKT fields
            skip.append("wkt")

        fields = filter(lambda f:
                        f != xml.UID and
                        f not in skip and
                        f not in xml.IGNORE_FIELDS and
                        str(table[f].type) != "id",
                        table.fields)

        if manager.show_ids and table._id.name not in fields:
            fields.insert(0, table._id.name)

        rfields = filter(lambda f:
                         (str(table[f].type).startswith("reference") or
                          str(table[f].type).startswith("list:reference")) and
                         f not in xml.FIELDS_TO_ATTRIBUTES,
                         fields)

        dfields = filter(lambda f:
                         f not in rfields,
                         fields)

        return (rfields, dfields)

    # -------------------------------------------------------------------------
    def limitby(self, start=None, limit=None):
        """
            Convert start+limit parameters into a limitby tuple
                - limit without start => start = 0
                - start without limit => limit = ROWSPERPAGE
                - limit 0 (or less)   => limit = 1
                - start less than 0   => start = 0

            @param start: index of the first record to select
            @param limit: maximum number of records to select
        """

        if start is None:
            if not limit:
                return None
            else:
                start = 0

        if not limit:
            limit = current.manager.ROWSPERPAGE
            if limit is None:
                return None

        if limit <= 0:
            limit = 1
        if start < 0:
            start = 0

        return (start, start + limit)

    # -------------------------------------------------------------------------
    def get_join(self):
        """
            Get a component join query for this resource
        """

        manager = current.manager
        if self.parent is None:
            return None
        else:
            ltable = self.parent.table
        rtable = self.table
        pkey = self.pkey
        fkey = self.fkey
        if self.linked:
            return self.linked.get_join()
        elif self.linktable:
            linktable = self.linktable
            lkey = self.lkey
            rkey = self.rkey
            join = ((ltable[pkey] == linktable[lkey]) &
                    (linktable[rkey] == rtable[fkey]))
            if manager.DELETED in linktable:
                join = ((linktable[manager.DELETED] != True) & join)
        else:
            join = (ltable[pkey] == rtable[fkey])
        return join

    # -------------------------------------------------------------------------
    def link_id(self, master_id, component_id):
        """
            Helper method to find the link table entry ID for
            a pair of linked records.

            @param master_id: the ID of the master record
            @param component_id: the ID of the component record
        """

        if self.parent is None or self.linked is None:
            return None

        db = current.db

        join = self.get_join()
        ltable = self.table
        mtable = self.parent.table
        ctable = self.linked.table
        query = join & \
                (mtable._id == master_id) & \
                (ctable._id == component_id)
        row = db(query).select(ltable._id, limitby=(0, 1)).first()
        if row:
            return row[ltable._id.name]
        else:
            return None

    # -------------------------------------------------------------------------
    def component_id(self, master_id, link_id):
        """
            Helper method to find the component record ID for
            a particular link of a particular master record

            @param link: the link (S3Resource)
            @param master_id: the ID of the master record
            @param link_id: the ID of the link table entry
        """

        if self.parent is None or self.linked is None:
            return None

        db = current.db

        join = self.get_join()
        ltable = self.table
        mtable = self.parent.table
        ctable = self.linked.table
        query = join & \
                (mtable._id == master_id) & \
                (ltable._id == link_id)
        row = db(query).select(ctable._id, limitby=(0, 1)).first()
        if row:
            return row[ctable._id.name]
        else:
            return None

    # -------------------------------------------------------------------------
    def update_link(self, master, record):
        """
            Create a new link in a link table if it doesn't yet exist.
            This function is meant to also update links in "embed"
            actuation mode once this gets implemented, therefore the
            method name "update_link".

            @param master: the master record
            @param record: the new component record to be linked
        """

        if self.parent is None or self.linked is None:
            return None

        # Find the keys
        resource = self.linked
        pkey = resource.pkey
        lkey = resource.lkey
        rkey = resource.rkey
        fkey = resource.fkey
        if pkey not in master:
            return None
        _lkey = master[pkey]
        if fkey not in record:
            return None
        _rkey = record[fkey]
        if not _lkey or not _rkey:
            return None

        # Create the link if it does not already exist
        db = current.db
        ltable = self.table
        query = ((ltable[lkey] == _lkey) &
                 (ltable[rkey] == _rkey))
        row = db(query).select(ltable._id, limitby=(0, 1)).first()
        if not row:
            link_id = ltable.insert(**{lkey:_lkey, rkey:_rkey})
        else:
            link_id = row[ltable._id.name]
        return link_id

    # -------------------------------------------------------------------------
    def sqltable(self,
                 fields=None,
                 start=0,
                 limit=None,
                 left=None,
                 orderby=None,
                 distinct=False,
                 linkto=None,
                 download_url=None,
                 no_ids=False,
                 as_page=False,
                 as_list=False,
                 format=None):
        """
            DRY helper function for SQLTABLEs in CRUD

            @param fields: list of fieldnames to display
            @param start: index of the first record to display
            @param limit: maximum number of records to display
            @param left: left outer joins
            @param orderby: orderby for the query
            @param distinct: distinct for the query
            @param linkto: hook to link record IDs
            @param download_url: the default download URL of the application
            @param as_page: return the list as JSON page
            @param as_list: return the list as Python list
            @param format: the representation format
        """

        db = current.db
        manager = current.manager
        table = self.table

        if fields is None:
            fields = [f.name for f in self.readable_fields()]
        if table._id.name not in fields and not no_ids:
            fields.insert(0, table._id.name)
        lfields, joins = self.get_list_fields(table, fields)

        colnames = [f.colname for f in lfields]
        headers = dict(map(lambda f: (f.colname, f.label), lfields))

        attributes = dict(distinct=distinct)
        # Orderby
        if orderby is not None:
            attributes.update(orderby=orderby)
        # Slice
        limitby = self.limitby(start=start, limit=limit)
        if limitby is not None:
            attributes.update(limitby=limitby)
        # Joins
        query = self.get_query()
        for j in joins.values():
            query &= j
        # Left outer joins
        if left is not None:
            attributes.update(left=left)

        # Fields in the query
        qfields = [f.field for f in lfields if f.field is not None]
        if no_ids:
            qfields.insert(0, table._id)

        # Add orderby fields which are not in qfields
        if distinct and orderby is not None:
            qf = [str(f) for f in qfields]
            if isinstance(orderby, str):
                of = orderby.split(",")
            elif not isinstance(orderby, (list, tuple)):
                of = [orderby]
            else:
                of = orderby
            for e in of:
                if isinstance(e, Field) and str(e) not in qf:
                    qfields.append(e)
                    qf.append(str(e))
                elif isinstance(e, str):
                    fn = e.strip().split()[0].split(".", 1)
                    tn, fn = ([table._tablename] + fn)[-2:]
                    try:
                        t = db[tn]
                        f = t[fn]
                    except:
                        continue
                    if str(f) not in qf:
                        qfields.append(f)
                        qf.append(str(e))

        # Retrieve the rows
        rows = db(query).select(*qfields, **attributes)
        if not rows:
            return None

        # Fields to show
        row = rows.first()
        def __expand(tablename, row, lfields=lfields):
            columns = []
            for f in lfields:
                tname = f.tname
                fname = f.fname
                if tname in row and isinstance(row[tname], Row):
                    columns += __expand(tname, lfields)
                elif (tname, fname) not in columns and fname in row:
                    columns.append((tname, fname))
            return columns
        columns = __expand(table._tablename, row)
        lfields = [lf for lf in lfields
                   if lf.show and (lf.tname, lf.fname) in columns]
        colnames = [f.colname for f in lfields]
        rows.colnames = colnames

        # Representation
        def __represent(f, row, columns=columns):
            field = f.field
            if field:
                return manager.represent(field, record=row, linkto=linkto)
            else:
                tname = f.tname
                fname = f.fname
                if (tname, fname) in columns:
                    if tname in row and fname in row[tname]:
                        return str(row[tname][fname])
                    elif fname in row:
                        return str(row[fname])
                    else:
                        return None
                else:
                    return None

        # Render as...
        if as_page:
            # ...JSON page (for pagination)
            items = [[__represent(f, row) for f in lfields] for row in rows]
        elif as_list:
            # ...Python list
            items = rows.as_list()
        else:
            # ...SQLTABLE
            items = SQLTABLES3(rows,
                               headers=headers,
                               linkto=linkto,
                               upload=download_url,
                               _id="list",
                               _class="dataTable display")
        return items

# END =========================================================================
