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
from s3forms import S3SQLCustomForm, S3SQLDefaultForm, S3SQLField
from s3query import S3ResourceField
from s3rest import S3Method
from s3utils import s3_get_foreign_key, s3_str, s3_unicode
from s3validators import JSONERRORS, SEPARATORS

DEFAULT = lambda: None

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
        formdict = {}

        forms = settings.get_mobile_forms()
        if forms:
            keys = set()
            for item in forms:

                # Parse the configuration
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

                # Provides (master-)data for download?
                data = True if options.get("data") else False

                # Append to form list
                url = {"c": c, "f": f}
                if url_vars:
                    url["v"] = url_vars
                mform = {"n": name,
                         "l": s3_str(title),
                         "t": tablename,
                         "r": url,
                         "d": data,
                         }
                formlist.append(mform)
                formdict[name] = mform

        dynamic_tables = settings.get_mobile_dynamic_tables()
        if dynamic_tables:

            # Select all dynamic tables which have mobile_form=True
            ttable = s3db.s3_table
            query = (ttable.mobile_form == True) & \
                    (ttable.deleted != True)
            rows = current.db(query).select(ttable.name,
                                            ttable.title,
                                            ttable.mobile_data,
                                            )
            for row in rows:

                tablename = row.name
                suffix = tablename.split("_", 1)[-1]

                # Form title
                title = row.title
                if not title:
                    title = " ".join(s.capitalize() for s in suffix.split("_"))

                # URL
                # @todo: make c+f configurable?
                url = {"c": "default",
                       "f": "table/%s" % suffix,
                       }

                # Append to form list
                mform = {"n": tablename,
                         "l": title,
                         "t": tablename,
                         "r": url,
                         "d": row.mobile_data,
                         }
                formlist.append(mform)
                formdict[name] = mform

        self.formlist = formlist
        self.forms = formdict

    # -------------------------------------------------------------------------
    def json(self):
        """
            Serialize the form list as JSON (EdenMobile)

            @returns: a JSON string
        """

        return json.dumps(self.formlist, separators=SEPARATORS)

# =============================================================================
class S3MobileSchema(object):
    """
        Table schema for a mobile resource
    """

    # Field types supported for mobile resources
    SUPPORTED_FIELD_TYPES =("string",
                            "text",
                            "integer",
                            "double",
                            "date",
                            "datetime",
                            "boolean",
                            "reference",
                            )

    # -------------------------------------------------------------------------
    def __init__(self, resource):
        """
            Constructor

            @param resource - the S3Resource
        """

        self.resource = resource

        # Initialize reference map
        self._references = None

        # Initialize the schema
        self._schema = None

        # Initialize the form description
        self._form = None

    # -------------------------------------------------------------------------
    def serialize(self):
        """
            Serialize the table schema

            @return: a JSON-serializable dict containing the table schema
        """

        schema = self._schema
        if schema is None:

            # Initialize
            schema = {}
            self._references = {}

            # Introspect and build schema
            fields = self.fields()
            for field in fields:
                description = self.describe(field)
                if description:
                    schema[field.name] = description

            # Store schema
            self._schema = schema

        return schema

    # -------------------------------------------------------------------------
    @property
    def references(self):
        """
            Tables (and records) referenced in this schema (lazy property)

            @return: a dict {tablename: [recordID, ...]} of all
                     referenced tables and records
        """

        if self._references is None:
            # Trigger introspection to gather all references
            self.serialize()

        return self._references

    # -------------------------------------------------------------------------
    @property
    def form(self):
        """
            The mobile form (field order) for the resource (lazy property)
        """

        if self._form is None:
            self.serialize()

        return self._form

    # -------------------------------------------------------------------------
    # Introspection methods
    # -------------------------------------------------------------------------
    def describe(self, field):
        """
            Construct a field description for the schema

            @param field: a Field instance

            @return: the field description as JSON-serializable dict
        """

        fieldtype = str(field.type)
        SUPPORTED_FIELD_TYPES = set(self.SUPPORTED_FIELD_TYPES)

        # Check if foreign key
        if fieldtype[:9] == "reference":

            # Skip super-entity references until supported by mobile client
            key = s3_get_foreign_key(field)[1]
            if key and key != "id":
                return None

            is_foreign_key = True

            # Store schema reference
            lookup = fieldtype[10:].split(".")[0]
            references = self._references
            if lookup not in references:
                references[lookup] = set()
        else:
            is_foreign_key = False
            lookup = None

        # Check that field type is supported
        if fieldtype in SUPPORTED_FIELD_TYPES or is_foreign_key:
            supported = True
        else:
            supported = False
        if not supported:
            return None

        # Create a field description
        description = {"type": fieldtype,
                       "label": str(field.label),
                       }

        # Add field settings to description
        settings = self.settings(field)
        if settings:
            description["settings"] = settings

        # Add field options to description
        options = self.get_options(field)
        if options:
            description["options"] = options

        # Add default value to description
        default = self.get_default(field, lookup=lookup)
        if default:
            description["default"] = default

        # @todo: add tooltip to description

        return description

    # -------------------------------------------------------------------------
    @classmethod
    def settings(cls, field):
        """
            Encode settings for the field description

            @param field: a Field instance

            @return: a dict with the field settings
        """

        settings = {}

        # Add readable/writable settings if False (True is assumed)
        if not field.readable:
            settings["readable"] = False
        if not field.writable:
            settings["writable"] = False

        # Add required flag if True (False is assumed)
        if cls.is_required(field):
            settings["required"] = True

        # @todo: min/max settings for numeric and date/time fields

        return settings

    # -------------------------------------------------------------------------
    @staticmethod
    def is_required(field):
        """
            Determine whether a value is required for a field

            @param field: the Field

            @return: True|False
        """

        required = field.notnull

        if not required and field.requires:
            error = field.validate("")[1]
            if error is not None:
                required = True

        return required

    # -------------------------------------------------------------------------
    @staticmethod
    def get_options(field):
        """
            Get the options for a field with IS_IN_SET

            @param field: the Field
            @return: a list of tuples (key, label) with the field options
        """

        # Check supported field types
        # @todo: add other types (may require special option key encoding)
        #        => foreign keys must report all valid options as record
        #           references so they can be resolved
        if str(field.type) not in ("string", "integer"):
            return None

        # Get field validator
        requires = field.requires
        if not requires:
            return None
        if not isinstance(requires, (tuple, list)):
            requires = [requires]

        # Check for IS_IN_SET, and extract the options
        requires = requires[0]
        if isinstance(requires, IS_EMPTY_OR):
            requires = requires.other
        if isinstance(requires, IS_IN_SET):
            options = []
            for key, label in requires.options():
                if not key:
                    continue
                options.append((key, s3_str(label)))
            return options
        else:
            return None

    # -------------------------------------------------------------------------
    def get_default(self, field, lookup=None):
        """
            Get the default value for a field

            @param field: the Field

            @returns: the default value for the field
        """

        default = field.default
        if default is not None:

            fieldtype = str(field.type)

            if fieldtype[:9] == "reference":

                # Convert the default value into a UUID
                uuid = self.get_uuid(lookup, default)
                if uuid:
                    # Store record reference for later resolution
                    self._references[lookup].add(default)
                    default = uuid
                else:
                    default = None

            elif fieldtype in ("date", "datetime", "time"):

                # @todo: implement this
                # => typically using a dynamic default (e.g. "now"), which
                #    will need special encoding and handling on the mobile
                #    side
                # => static defaults must be encoded in ISO-Format
                default = None

            else:

                # Use field default as-is
                default = field.default

        return default

    # -------------------------------------------------------------------------
    def fields(self):
        """
            Determine which fields need to be included in the schema

            @returns: a list of Field instances
        """

        resource = self.resource
        tablename = resource.tablename

        fields = []
        mobile_form = self._form = []

        # Prevent duplicates
        fnames = set()
        include = fnames.add

        form = self.mobile_form(resource)
        for element in form.elements:

            if isinstance(element, S3SQLField):
                rfield = resource.resolve_selector(element.selector)

                fname = rfield.fname

                if rfield.tname == tablename and fname not in fnames:
                    fields.append(rfield.field)
                    mobile_form.append(fname)
                    include(fname)

        if resource.parent and \
           not resource.linktable and \
           resource.pkey == resource.parent._id.name:

            # Include the parent key
            fkey = resource.fkey
            if fkey not in fnames:
                fields.append(resource.table[fkey])
                include(fkey)

        return fields

    # -------------------------------------------------------------------------
    @staticmethod
    def mobile_form(resource):
        """
            Get the mobile form for a resource

            @param resource: the S3Resource
            @returns: an S3SQLForm instance
        """

        # Get the form definition from "mobile_form" table setting
        form = resource.get_config("mobile_form")
        if form is None:
            # Fallback
            form = resource.get_config("crud_form")

        # @todo: if resource is a dynamic table, establish
        #        the mobile form from the "form" table setting
        #        before falling back to all readable fields

        if not form:
            # No mobile form configured, or is a S3SQLDefaultForm
            # => construct a custom form that includes all readable fields
            readable_fields = resource.readable_fields()
            fields = [field.name for field in readable_fields
                                 if field.type != "id"]
            form = S3SQLCustomForm(*fields)

        return form

    # -------------------------------------------------------------------------
    # Utility functions
    # -------------------------------------------------------------------------
    @staticmethod
    def get_uuid(tablename, record_id):
        """
            Look up the UUID of a record

            @param tablename: the table name
            @param record_id: the record ID

            @return: the UUID of the specified record, or None if
                     the record does not exist or has no UUID
        """

        table = current.s3db.table(tablename)
        if not table or "uuid" not in table.fields:
            return None

        query = (table._id == record_id)
        if "deleted" in table.fields:
            query &= (table.deleted == False)

        row = current.db(query).select(table.uuid,
                                       limitby = (0, 1),
                                       ).first()

        return row.uuid or None if row else None

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

        self._config = DEFAULT

    # -------------------------------------------------------------------------
    @property
    def config(self):
        """
            The mobile form configuration (lazy property)

            @returns: a dict {tablename, title, options}
        """

        config = self._config
        if config is DEFAULT:

            tablename = self.resource.tablename
            config = {"tablename": tablename,
                      "title": None,
                      "options": {},
                      }

            forms = current.deployment_settings.get_mobile_forms()
            if forms:
                for form in forms:
                    options = None
                    if isinstance(form, (tuple, list)):
                        if len(form) == 2:
                            title, tablename_ = form
                            if isinstance(tablename_, dict):
                                tablename_, options = title, tablename_
                                title = None
                        elif len(form) == 3:
                            title, tablename_, options = form
                        else:
                            # Invalid => skip
                            continue
                    else:
                        title, tablename_ = None, form

                    if tablename_ == tablename:
                        config["title"] = title
                        if options:
                            config["options"] = options
                        break

            self._config = config

        return config

    # -------------------------------------------------------------------------
    def serialize(self):
        """
            Serialize the mobile form configuration for the target resource

            @return: a JSON-serialiable dict containing the mobile form
                     configuration for export to the mobile client
        """

        s3db = current.s3db
        resource = self.resource

        ms = S3MobileSchema(resource)
        schema = ms.serialize()

        main = {"tablename": resource.tablename,
                "schema": schema,
                "form": ms.form,
                }

        # Add CRUD strings
        strings = self.strings()
        if strings:
            main["strings"] = strings

        # Required and provided schemas
        required = set(ms.references.keys())
        provided = set([resource.tablename])

        # Add schemas for components
        components = self.components()
        for alias in components:

            # Generate a resource for the component table
            cresource = resource.components.get(alias)
            if not cresource:
                continue

            # Get the schema for the component
            cschema = S3MobileSchema(cresource)
            hook = components[alias]
            hook["schema"] = cschema.serialize()

            # Mark as provided
            provided.add(cresource.tablename)

            for tname in cschema.references:
                required.add(tname)

        # Add schemas for referenced tables
        references = {}
        required = list(required)
        while required:

            tablename = required.pop()
            if tablename in provided:
                continue

            rresource = s3db.resource(tablename)
            rs = S3MobileSchema(rresource)
            references[tablename] = {"schema": rs.serialize()}

            for reference in rs.references:
                if reference not in provided:
                    required.append(reference)

            provided.add(tablename)

        # @todo: add default lookup records

        form = {"main": main,
                }
        if references:
            form["references"] = references
        if components:
            form["components"] = components

        return form

    # -------------------------------------------------------------------------
    def strings(self):
        """
            Add CRUD strings for mobile form

            @return: a dict with CRUD strings for the resource
        """

        tablename = self.resource.tablename

        # Use the title specified in deployment setting
        config = self.config
        title = config.get("title")

        # Fall back to CRUD title_list
        if not title:
            crud_strings = current.response.s3.crud_strings.get(tablename)
            if crud_strings:
                title = crud_strings.get("title_list")

        # Fall back to capitalized table name
        if not title:
            name = tablename.split("_", 1)[-1]
            title = " ".join(word.capitalize() for word in name.split("_"))

        # Build strings-dict
        strings = {}
        if title:
            title = s3_str(title)
            strings["name"] = title
            strings["namePlural"] = title

        return strings

    # -------------------------------------------------------------------------
    def components(self):
        """
            Add component declarations to the mobile form

            @return: a dict with component declarations for the resource
        """

        resource = self.resource
        tablename = resource.tablename
        pkey = resource._id.name

        options = self.config.get("options")
        components = {}

        # Expose static components
        aliases = options.get("components") if options else None
        if aliases:
            hooks = current.s3db.get_components(tablename, names=aliases)
            for alias, hook in hooks.items():
                if hook.linktable or hook.pkey != pkey:
                    # Link table or super-component => not supported (yet)
                    continue
                components[alias] = {"resource": hook.tablename,
                                     "joinby": hook.fkey,
                                     "multiple": hook.multiple,
                                     }

        # Expose dynamic components
        ftable = current.s3db.s3_field
        ttable = current.s3db.s3_table
        join = ttable.on(ttable.id == ftable.table_id)
        query = (ftable.component_key == True) & \
                (ftable.master == tablename) & \
                (ftable.deleted == False)
        rows = current.db(query).select(ftable.name,
                                        ftable.component_alias,
                                        ftable.settings,
                                        ttable.name,
                                        join = join,
                                        )
        for row in rows:
            component_key = row.s3_field
            settings = component_key.settings
            if not settings or \
               settings.get("mobile_component") is not False:
                alias = component_key.component_alias
                multiple = settings.get("multiple", True)
                components[alias] = {"resource": row.s3_table.name,
                                     "joinby": component_key.name,
                                     "multiple": multiple,
                                     }

        return components

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
        files = {}
        content_type = r.env.get("content_type")
        if content_type and content_type.startswith("multipart/"):

            # Record data
            s = r.post_vars.get("data")
            try:
                data = json.loads(s)
            except JSONERRORS:
                msg = sys.exc_info()[1]
                r.error(400, msg)

            # Attached files
            import cgi
            for key in r.post_vars:
                value = r.post_vars[key]
                if isinstance(value, cgi.FieldStorage) and value.filename:
                    files[value.filename] = value.file
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
            table = resource.table

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
                        ftype = table[fieldname].type
                        if ftype == "upload":
                            # Field value is name of attached file
                            filename = s3_unicode(value)
                            if filename in files:
                                col.set("filename", filename)
                        else:
                            col.text = s3_unicode(value)

            tree = etree.ElementTree(root)

            # Try importing the tree
            # @todo: error handling
            try:
                resource.import_xml(tree, files=files)
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
    def mform(self, r, **attr):
        """
            Get the mobile form for the target resource

            @param r: the S3Request instance
            @param attr: controller attributes

            @returns: a JSON string
        """

        resource = self.resource

        # Get the mobile form
        mform = S3MobileForm(resource).serialize()

        # Add controller and function for data exchange
        mform["controller"] = r.controller
        mform["function"] = r.function

        # Convert to JSON
        output = json.dumps(mform, separators=SEPARATORS)

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
