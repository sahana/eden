# -*- coding: utf-8 -*-

""" S3 Mobile Forms API

    @copyright: 2016 (c) Sahana Software Foundation
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

    @todo: integrate S3XForms API
"""

__all__ = ("S3MobileFormList",
           "S3MobileForm",
           "S3MobileCRUD",
           )

import datetime
import json
import sys

try:
    from lxml import etree
except ImportError:
    print >> sys.stderr, "ERROR: lxml module needed for XML handling"
    raise

from gluon import *
from gluon.dal import Query
from s3datetime import s3_encode_iso_datetime
from s3error import S3PermissionError
from s3forms import S3SQLDefaultForm, S3SQLField
from s3query import S3ResourceField
from s3rest import S3Method
from s3utils import s3_str, s3_unicode
from s3validators import JSONERRORS, SEPARATORS

# =============================================================================
class S3MobileFormList(object):
    """
        Form List Generator
    """

    def __init__(self):
        """
            Constructor
        """

        T = current.T
        s3db = current.s3db
        settings = current.deployment_settings

        formlist = []

        forms = settings.get_mobile_forms()
        if forms:
            keys = set()
            for item in forms:

                options = {}
                if isinstance(item, (tuple, list)):

                    if len(item) == 2:
                        title, tablename = item
                        if isinstance(tablename, dict):
                            tablename, options = title, tablename
                            title = None
                    elif len(item) == 3:
                        title, tablename, options = item
                    else:
                        continue
                else:
                    title, tablename = None, item

                # Make sure table exists
                table = s3db.table(tablename)
                if not table:
                    current.log.warning("Mobile forms: non-existent resource %s" % tablename)
                    continue

                # Determine controller and function
                c, f = tablename.split("_", 1)
                c = options.get("c") or c
                f = options.get("f") or f

                # Only expose if target module is enabled
                if not settings.has_module(c):
                    continue

                # Determine the form name
                name = options.get("name")
                if not name:
                    name = "%s_%s" % (c, f)

                # Stringify URL query vars
                url_vars = options.get("vars")
                if url_vars:
                    items = []
                    for k in url_vars:
                        v = s3_str(url_vars[k])
                        url_vars[k] = v
                        items.append("%s=%s" % (k, v))
                    query = "&".join(sorted(items))
                else:
                    query = ""

                # Deduplicate by target URL
                key = (c, f, query)
                if key in keys:
                    continue
                keys.add(key)

                # Determine form title
                if title is None:
                    title = " ".join(w.capitalize() for w in f.split("_"))
                if isinstance(title, basestring):
                    title = T(title)

                # Append to form list
                url = {"c": c, "f": f}
                if url_vars:
                    url["v"] = url_vars
                formlist.append({"n": name,
                                 "l": s3_str(title),
                                 "t": tablename,
                                 "r": url,
                                 })

        self.formlist = formlist

    # -------------------------------------------------------------------------
    def json(self):
        """
            Serialize the form list as JSON (EdenMobile)

            @returns: a JSON string
        """

        return json.dumps(self.formlist, separators=SEPARATORS)

# =============================================================================
class S3MobileForm(object):
    """
        Mobile representation of an S3SQLForm
    """

    def __init__(self, resource, form=None):
        """
            Constructor

            @param resource: the S3Resource
            @param form: an S3SQLForm instance to override settings
        """

        self.resource = resource
        self._form = form

    # -------------------------------------------------------------------------
    @property
    def form(self):
        """
            The form configuration (lazy property), fallback cascade:
                1. the form specified in constructor
                2. "mobile_form" config
                3. "crud_form" config
                4. all readable fields

            @returns: an S3SQLForm instance
        """

        form = self._form
        if form is None:

            resource = self.resource
            form = resource.get_config("mobile_form")

            if form is None:
                form = resource.get_config("crud_form")

            if form is None:
                # Construct a custom form from all readable fields
                readable_fields = self.resource.readable_fields()
                fields = [field.name for field in readable_fields]
                form = S3SQLCustomForm(*fields)

            self._form = form

        return form

    # -------------------------------------------------------------------------
    def schema(self):
        """
            Convert the form configuration into an EdenMobile schema dict

            @returns: a JSON-serializable dict with the schema definition
        """

        form = self.form
        resource = self.resource

        schema = {}
        form_fields = []

        for element in form.elements:
            if isinstance(element, S3SQLField):

                # Resolve the selector
                rfield = resource.resolve_selector(element.selector)

                if rfield.tname == resource.tablename:

                    description = self.describe(rfield)
                    if description:
                        fname = rfield.fname
                        schema[fname] = description
                        form_fields.append(fname)
                else:
                    # Subtable field
                    # => skip until implemented @todo
                    continue
            else:
                # Inline component or other form element
                # => skip until implemented @todo
                continue

        if form_fields:
            schema["_form"] = form_fields

        return schema

    # -------------------------------------------------------------------------
    def describe(self, rfield):
        """
            Generate a description of a resource field (for mobile schemas)

            @param rfield: the S3ResourceField

            @returns: a JSON-serializable dict describing the field
        """

        field = rfield.field
        if not field:
            # Virtual field
            return None

        # Basic field description
        description = {"type": rfield.ftype,
                       "label": s3_str(field.label),
                       }

        # Field settings
        if field.notnull:
            description["notnull"] = True
        if not field.readable:
            description["readable"] = False
        if not field.writable:
            description["writable"] = False

        # @todo: options
        # @todo: minimum
        # @todo: maximum
        # @todo: default value
        # @todo: readable, writable
        # @todo: placeholder?
        # @todo: required

        return description

# =============================================================================
class S3MobileCRUD(S3Method):
    """
        Mobile Data Handler

        responds to GET /prefix/name/mdata.json     (Data download)
                    POST /prefix/name/mdata.json    (Data upload)
                    GET /prefix/name/mform.json     (Schema download)
                    GET /prefix/name/xform.xml      (XForms analogously, later...)
    """

    # -------------------------------------------------------------------------
    def apply_method(self, r, **attr):
        """
            Entry point for REST interface.

            @param r: the S3Request instance
            @param attr: controller attributes
        """

        http = r.http
        method = r.method
        representation = r.representation

        output = {}

        if method == "mdata":
            if representation == "json":
                if http == "GET":
                    # Data download
                    output = self.mdata_export(r, **attr)

                elif http == "POST":
                    # Data upload
                    output = self.mdata_import(r, **attr)

                else:
                    r.error(405, current.ERROR.BAD_METHOD)
            else:
                r.error(415, current.ERROR.BAD_FORMAT)

        elif method == "mform":
            if representation == "json":
                if http == "GET":
                    # Form download
                    output = self.mform(r, **attr)

                else:
                    r.error(405, current.ERROR.BAD_METHOD)
            else:
                r.error(415, current.ERROR.BAD_FORMAT)
        else:
            r.error(405, current.ERROR.BAD_METHOD)

        return output

    # -------------------------------------------------------------------------
    @staticmethod
    def mdata_export(r, **attr):
        """
            Provide data for mobile app

            @param r: the S3Request instance
            @param attr: controller attributes

            @returns: a JSON string
        """

        ID = "id"
        PID = "pe_id"
        UID = current.xml.UID
        s3db = current.s3db
        resource = r.resource
        resource_tablename = resource.tablename
        
        # Output in mdata format
        output = {resource_tablename: []}
        # Lookup to ensure we extract ID, UID fields & joining FKs for all tables
        tablenames = [resource_tablename]
        # Keep track of which FKs we have so that we can replace them with UID
        fks = {resource_tablename: {}}

        # Default to the 'mobile_list_fields' setting
        list_fields = resource.get_config("mobile_list_fields")
        if not list_fields:
            # Fallback to the 'list_fields' setting
            list_fields = resource.get_config("list_fields")
        if not list_fields:
            # Fallback to all readable fields
            list_fields = [field.name for field in resource.readable_fields()]
        else:
            # Ensure that we have all UID fields included
            # Ensure we have FKs between all linked records
            components = resource.components
            def find_fks(join):
                """
                    Helper function to get the FKs from a Join
                """
                for q in (join.first, join.second):
                    if isinstance(q, Field):
                        if q.referent:
                            # FK
                            if q.tablename == resource_tablename:
                                fieldname = q.name
                                if fieldname not in list_fields:
                                    list_fields.append(fieldname)
                                    fks[resource_tablename][fieldname] = str(q.referent)
                            else:
                                tn = q.tablename
                                if tn not in fks:
                                    fks[tn] = {} 
                                fks[tn][q.name] = str(q.referent)
                    elif isinstance(q, Query):
                        find_fks(q)

            for selector in list_fields:
                rfield = S3ResourceField(resource, selector)
                tablename = rfield.tname
                if tablename not in tablenames:
                    output[tablename] = []
                    tablenames.append(tablename)
                    # Find the FKs
                    if tablename in fks:
                        this_fks = fks[tablename]
                    else:
                        fks[tablename] = this_fks = {}

                    for tn in rfield.join:
                        join = rfield.join[tn]
                        find_fks(join)

                    # Add the ID, UUID & any FKs to list_fields
                    if "." in selector:
                        component, fieldname = selector.split(".", 1)
                        id_field = "%s.%s" % (component, ID) 
                        if id_field not in list_fields:
                            list_fields.append(id_field)
                        uuid_field = "%s.%s" % (component, UID) 
                        if uuid_field not in list_fields:
                            list_fields.append(uuid_field)
                        if "$" in fieldname:
                            fk, fieldname = fieldname.split("$", 1)
                            fk_field = "%s.%s" % (component, fk)
                            if fk_field not in list_fields:
                                list_fields.append(fk_field)
                            ctablename = components[component].table._tablename # Format to handle Aliases 
                            if ctablename not in fks:
                                fks[ctablename] = {}
                            #referent = s3db[ctablename][fk].referent
                            if fk not in fks[ctablename]:
                                #fks[ctablename][fk] = str(referent) 
                                fks[ctablename][fk] = str(s3db[ctablename][fk].referent) 
                            id_field = "%s.%s$%s" % (component, fk, ID) 
                            if id_field not in list_fields:
                                list_fields.append(id_field)
                            uuid_field = "%s.%s$%s" % (component, fk, UID) 
                            if uuid_field not in list_fields:
                                list_fields.append(uuid_field)
                            # Restore once list_fields working
                            #if "$" in fieldname:
                            #    # e.g. address.location_id$parent$uuid
                            #    fk2, fieldname = fieldname.split("$", 1)
                            #    tablename = referent.tablename
                            #    if fk2 not in fks[tablename]:
                            #        fks[tablename][fk2] = str(s3db[tablename][fk2].referent)
                            #    id_field = "%s.%s$%s$%s" % (component, fk, fk2, ID) 
                            #    if id_field not in list_fields:
                            #        list_fields.append(id_field)
                            #    uuid_field = "%s.%s$%s$%s" % (component, fk, fk2, UID) 
                            #    if uuid_field not in list_fields:
                            #        list_fields.append(uuid_field)
                        else:
                            for fk in this_fks:
                                fk_field = "%s.%s" % (component, fk)
                                if fk_field not in list_fields:
                                    list_fields.append(fk_field)

                    elif "$" in selector:
                        fk, fieldname = selector.split("$", 1)
                        if fk not in list_fields:
                            list_fields.append(fk)
                        #referent = s3db[resource_tablename][fk].referent
                        if fk not in fks[resource_tablename]:
                            #fks[resource_tablename][fk] = str(referent)
                            fks[resource_tablename][fk] = str(s3db[resource_tablename][fk].referent)
                        id_field = "%s$%s" % (fk, ID) 
                        if id_field not in list_fields:
                            list_fields.append(id_field)
                        uuid_field = "%s$%s" % (fk, UID) 
                        if uuid_field not in list_fields:
                            list_fields.append(uuid_field)
                        # Restore once list_fields working
                        #if "$" in fieldname:
                        #    # e.g. location_id$parent$uuid
                        #    fk2, fieldname = fieldname.split("$", 1)
                        #    tablename = referent.tablename
                        #    if fk2 not in fks[tablename]:
                        #        fks[tablename][fk2] = str(s3db[tablename][fk2].referent)
                        #    id_field = "%s$%s$%s" % (fk, fk2, ID) 
                        #    if id_field not in list_fields:
                        #        list_fields.append(id_field)
                        #    uuid_field = "%s$%s$%s" % (fk, fk2, UID) 
                        #    if uuid_field not in list_fields:
                        #        list_fields.append(uuid_field)
                            

        if ID not in list_fields:
            list_fields.append(ID)
        if UID not in list_fields:
            list_fields.append(UID)

        data = resource.select(list_fields, raw_data=True)
        rows = data.rows

        # Build lookups of IDs to UIDs & PIDs to UIDs
        id_lookup = {}
        pid_lookup = {}
        for record in rows:
            tablenames = {}
            for field in record:
                value = record[field]
                tablename, field = field.split(".", 1)
                if tablename not in tablenames:
                    tablenames[tablename] = {ID: None,
                                             PID: None,
                                             UID: None,
                                             }
                if field == ID:
                    tablenames[tablename][ID] = value
                elif field == PID:
                    tablenames[tablename][PID] = value
                elif field == UID:
                    tablenames[tablename][UID] = value
            for tablename in tablenames:
                if tablename not in id_lookup:
                    id_lookup[tablename] = {}
                id_lookup[tablename][tablenames[tablename][ID]] = tablenames[tablename][UID]
                pid = tablenames[tablename][PID]
                if pid:
                    pid_lookup[pid] = tablenames[tablename][UID]

        # Convert to S3Mobile format
        # & replace FKs with UUID
        for record in rows:
            # Keep track of which tables have no data
            empty = []
            row = {tablename: [] for tablename in tablenames}
            for field in record:
                value = record[field]
                tablename, field = field.split(".", 1)
                if field == ID:
                    # Don't include these in output
                    continue
                this_fks = fks[tablename]
                if field in this_fks:
                    if value:
                        # Replace ID with UUID:
                        referent = this_fks[field]
                        tn, fn = referent.split(".", 1)
                        if fn == PID:
                            value = pid_lookup[value]
                        else:
                            value = id_lookup[tn][value]

                elif field == "uuid":
                    if value is None:
                        empty.append(tablename)
                        continue
                elif isinstance(value, datetime.date) or \
                     isinstance(value, datetime.datetime):
                    value = s3_encode_iso_datetime(value).decode("utf-8")
                row[tablename].append((field, value))
            for tablename in tablenames:
                if tablename not in empty:
                    output[tablename].append(row[tablename])

        output = json.dumps(output, separators=SEPARATORS)
        current.response.headers = {"Content-Type": "application/json"}
        return output

    # -------------------------------------------------------------------------
    def mdata_import(self, r, **attr):
        """
            Process data submission from mobile app

            @param r: the S3Request instance
            @param attr: controller attributes

            @returns: JSON message
        """

        output = {}

        # Extract the data
        content_type = r.env.get("content_type")
        if content_type and content_type.startswith("multipart/"):
            s = r.post_vars.get("data")
            try:
                data = json.loads(s)
            except JSONERRORS:
                msg = sys.exc_info()[1]
                r.error(400, msg)
        else:
            s = r.body
            s.seek(0)
            try:
                data = json.load(s)
            except JSONERRORS:
                msg = sys.exc_info()[1]
                r.error(400, msg)

        xml = current.xml

        resource = r.resource
        tablename = resource.tablename

        records = data.get(tablename)
        if records:

            # Create import tree
            TAG = xml.TAG
            ATTRIBUTE = xml.ATTRIBUTE
            IGNORE_FIELDS = xml.IGNORE_FIELDS
            FIELDS_TO_ATTRIBUTES = xml.FIELDS_TO_ATTRIBUTES

            RESOURCE = TAG.resource
            DATA = TAG.data
            NAME = ATTRIBUTE.name
            FIELD = ATTRIBUTE.field

            rfields = resource.fields

            root = etree.Element(TAG.root)
            SubElement = etree.SubElement

            for record in records:

                row = SubElement(root, RESOURCE)
                row.set(NAME, tablename)

                for fieldname, value in record.items():
                    if value is None:
                        continue
                    elif fieldname not in rfields:
                        continue
                    elif fieldname in IGNORE_FIELDS:
                        continue
                    elif fieldname in FIELDS_TO_ATTRIBUTES:
                        row.set(fieldname, value)
                    else:
                        col = SubElement(row, DATA)
                        col.set(FIELD, fieldname)
                        col.text = s3_unicode(value)

            tree = etree.ElementTree(root)

            # Try importing the tree
            # @todo: error handling
            try:
                resource.import_xml(tree)
            except IOError:
                r.unauthorised()
            else:
                import_result = self.import_result(resource)

            output = xml.json_message(**import_result)
        else:
            output = xml.json_message(True, 200, "No records to import")

        current.response.headers = {"Content-Type": "application/json"}
        return output

    # -------------------------------------------------------------------------
    @staticmethod
    def mform(r, **attr):
        """
            Get the schema definition (as JSON)

            @param r: the S3Request instance
            @param attr: controller attributes

            @returns: a JSON string
        """

        resource = r.resource

        form = S3MobileForm(resource)

        schema = form.schema()
        schema["_controller"] = r.controller
        schema["_function"] = r.function

        name = resource.tablename
        output = json.dumps({name: schema})

        current.response.headers = {"Content-Type": "application/json"}
        return output

    # -------------------------------------------------------------------------
    @staticmethod
    def import_result(resource):
        """
            Extract import results from the resource to report back
            to the mobile client

            @param resource: the S3Resource that has been imported to

            @returns: a dict with import result details
        """

        info = {}

        if "uuid" not in resource.fields:
            return info

        db = current.db

        created_ids = resource.import_created
        updated_ids = resource.import_updated

        uuid_field = resource.table.uuid

        if created_ids:
            query = (resource._id.belongs(created_ids))
            rows = db(query).select(uuid_field,
                                    limitby = (0, len(created_ids)),
                                    )
            info["created"] = [row.uuid for row in rows]

        if updated_ids:
            query = (resource._id.belongs(updated_ids))
            rows = db(query).select(uuid_field,
                                    limitby = (0, len(updated_ids)),
                                    )
            info["updated"] = [row.uuid for row in rows]

        return info

# END =========================================================================
