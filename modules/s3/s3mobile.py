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
from s3datetime import s3_encode_iso_datetime, s3_parse_datetime
from s3error import S3PermissionError
from s3forms import S3SQLCustomForm, S3SQLDefaultForm, S3SQLField
from s3query import S3ResourceField
from s3rest import S3Method
from s3utils import s3_get_foreign_key, s3_str, s3_unicode
from s3validators import JSONERRORS, SEPARATORS

DEFAULT = lambda: None

# JSON-serializable table settings (SERIALIZABLE_OPTS)
# which require preprocessing before they can be passed
# to the mobile client (e.g. i18n)
PREPROCESS_OPTS = ("subheadings", )

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

                # Exposed for data entry (or just for reference)?
                main = False if options.get("data_only", False) else True

                # Append to form list
                url = {"c": c, "f": f}
                if url_vars:
                    url["v"] = url_vars
                mform = {"n": name,
                         "l": s3_str(title),
                         "t": tablename,
                         "r": url,
                         "d": data,
                         "m": main,
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
                            "upload",
                            )

    # -------------------------------------------------------------------------
    def __init__(self, resource):
        """
            Constructor

            @param resource - the S3Resource
        """

        self.resource = resource

        # Initialize reference map
        self._references = {}

        # Initialize the schema
        self._schema = None

        # Initialize the form description
        self._form = None

        # Initialize subheadings
        self._subheadings = DEFAULT

        # Initialize settings
        self._settings = None

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
    @property
    def subheadings(self):
        """
            The subheadings for the mobile form (lazy property)
        """

        subheadings = self._subheadings

        if subheadings is DEFAULT:
            setting = self.resource.get_config("subheadings")
            subheadings = self._subheadings \
                        = self.subheadings_l10n(setting)

        return subheadings

    # -------------------------------------------------------------------------
    @property
    def settings(self):
        """
            Directly-serializable settings from s3db.configure (lazy property)
        """

        settings = self._settings

        if settings is None:

            settings = self._settings = {}
            resource = self.resource

            from s3model import SERIALIZABLE_OPTS
            for key in SERIALIZABLE_OPTS:
                if key not in PREPROCESS_OPTS:
                    setting = resource.get_config(key, DEFAULT)
                    if setting is not DEFAULT:
                        settings[key] = setting

        return settings

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
        superkey = False
        reftype = None
        if fieldtype[:9] == "reference":

            s3db = current.s3db

            is_foreign_key = True

            # Get referenced table/field name
            ktablename, key = s3_get_foreign_key(field)[:2]

            # Get referenced table
            ktable = current.s3db.table(ktablename)
            if not ktable:
                return None

            if "instance_type" in ktable.fields:
                # Super-key

                tablename = str(field).split(".", 1)[0]
                supertables = s3db.get_config(tablename, "super_entity")
                if not supertables:
                    supertables = set()
                elif not isinstance(supertables, (list, tuple)):
                    supertables = [supertables]

                if ktablename in supertables and key == ktable._id.name:
                    # This is the super-id of the instance table => skip
                    return None
                else:
                    # This is a super-entity reference
                    fieldtype = "objectkey"

                    # @todo: add instance types if limited in validator
                    superkey = True
                    reftype = {ktablename: []}
            else:
                # Regular foreign key

                # Store schema reference
                references = self._references
                if ktablename not in references:
                    references[ktablename] = set()
        else:
            is_foreign_key = False
            ktablename = None

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

        # Add type for super-entity references (=object keys)
        if reftype:
            description["reftype"] = reftype

        # Add field options to description
        options = self.get_options(field, lookup=ktablename)
        if options:
            # @todo: if reference, store the returned options
            #        as representation labels rather than as
            #        options
            description["options"] = options

        # Add default value to description
        default = self.get_default(field, lookup=ktablename, superkey=superkey)
        if default:
            description["default"] = default

        # Add readable/writable settings if False (True is assumed)
        if not field.readable:
            description["readable"] = False
        if not field.writable:
            description["writable"] = False

        # Add required flag if True (False is assumed)
        if self.is_required(field):
            description["required"] = True

        # @todo: add tooltip to description

        # @todo: if field.represent is a base-class S3Represent
        #        (i.e. no custom lookup, no custom represent),
        #        and its field list is not just "name" => pass
        #        that field list as description["represent"]

        return description

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
    def get_options(self, field, lookup=None):
        """
            Get the options for a field with IS_IN_SET

            @param field: the Field
            @param lookup: the name of the lookup table

            @return: a list of tuples (key, label) with the field options
        """

        requires = field.requires
        if not requires:
            return None
        if isinstance(requires, (list, tuple)):
            requires = requires[0]
        if isinstance(requires, IS_EMPTY_OR):
            requires = requires.other

        fieldtype = str(field.type)
        if fieldtype[:9] == "reference":

            # Foreign keys have no fixed options
            # => must expose the lookup table with data=True in order
            #    to share current field options with the mobile client;
            #    this is better done explicitly in order to run the
            #    data download through the lookup table's controller
            #    for proper authorization, customise_* and filtering

            # @todo: deliver store uuid<=>label map instead, so that the
            #        mobile client has labels for fk options - unless the
            #        field has a base-class S3Represent with a field list
            #        that can be encoded in the field description
            return None

        elif fieldtype in ("string", "integer"):

            # Check for IS_IN_SET, and extract the options
            if isinstance(requires, IS_IN_SET):
                options = []
                for value, label in requires.options():
                    if value is not None:
                        options.append((value, s3_str(label)))
                return options
            else:
                return None

        else:
            # @todo: add other types (may require special option key encoding)
            return None

    # -------------------------------------------------------------------------
    def get_default(self, field, lookup=None, superkey=False):
        """
            Get the default value for a field

            @param field: the Field
            @param lookup: the name of the lookup table
            @param superkey: lookup table is a super-entity

            @returns: the default value for the field
        """

        default = field.default

        if default is not None:

            fieldtype = str(field.type)

            if fieldtype[:9] == "reference":

                # Look up the UUID for the default
                uuid = self.get_uuid(lookup, default)
                if uuid:

                    if super_key:
                        # Get the instance record ID
                        prefix, name, record_id = current.s3db.get_instance(lookup, default)
                        if record_id:
                            tablename = "%s_%s" % (prefix, name)
                    else:
                        record_id = default
                        tablename = lookup

                    if record_id:

                        # Export the default lookup record as dependency
                        # (make sure the corresponding table schema is exported)
                        if tablename not in self._references:
                            references = self.references[tablename] = set()
                        else:
                            references = self.references[tablename]
                        references.add(record_id)

                        # Resolve as UUID
                        default = uuid

                    else:
                        default = None

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
    def has_mobile_form(tablename):
        """
            Check whether a table exposes a mobile form

            @param tablename: the table name

            @return: True|False
        """

        from s3model import DYNAMIC_PREFIX
        if tablename.startswith(DYNAMIC_PREFIX):

            ttable = current.s3db.s3_table
            query = (ttable.name == tablename) & \
                    (ttable.mobile_form == True) & \
                    (ttable.deleted != True)
            row = current.db(query).select(ttable.id,
                                           limitby = (0, 1),
                                           ).first()
            if row:
                return True
        else:

            forms = current.deployment_settings.get_mobile_forms()
            for spec in forms:
                if isinstance(spec, (tuple, list)):
                    if len(spec) > 1 and not isinstance(spec[1], dict):
                        tn = spec[1]
                    else:
                        tn = spec[0]
                else:
                    tn = spec
                if tn == tablename:
                    return True

        return False

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

    # -------------------------------------------------------------------------
    @classmethod
    def subheadings_l10n(cls, setting):
        """
            Helper to translate form subheadings

            @param setting: the subheadings-setting (a dict)

            @return: the subheadings dict with translated headers
        """

        if setting is None:
            return None

        T = current.T
        output = {}

        for header, fields in setting.items():
            if isinstance(fields, dict):
                # Nested format => recurse
                subheadings = fields.get("subheadings")
                fields = {"fields": fields.get("fields"),
                          }
                if subheadings:
                    fields["subheadings"] = cls.subheadings_l10n(subheadings)
            output[s3_str(T(header))] = fields

        return output

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
    def serialize(self, msince=None):
        """
            Serialize the mobile form configuration for the target resource

            @param msince: include look-up records only if modified
                           after this datetime ("modified since")

            @return: a JSON-serialiable dict containing the mobile form
                     configuration for export to the mobile client
        """

        s3db = current.s3db
        resource = self.resource
        tablename = resource.tablename

        super_entities = self.super_entities

        ms = S3MobileSchema(resource)
        schema = ms.serialize()

        main = {"tablename": tablename,
                "schema": schema,
                "types": super_entities(tablename),
                "form": ms.form,
                }

        # Add CRUD strings
        strings = self.strings()
        if strings:
            main["strings"] = strings

        # Add subheadings
        subheadings = ms.subheadings
        if subheadings:
            main["subheadings"] = subheadings

        # Add directly-serializable settings
        settings = ms.settings
        if settings:
            main["settings"] = settings

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
            ctablename = cresource.tablename

            # Get the schema for the component
            cschema = S3MobileSchema(cresource)
            hook = components[alias]
            hook["schema"] = cschema.serialize()

            # Add super entity declarations
            hook["types"] = super_entities(cresource)

            # Add directly-serializable settings
            settings = cschema.settings
            if settings:
                hook["settings"] = settings

            # Mark as provided
            provided.add(tablename)

            for tname in cschema.references:
                required.add(tname)

        # Add schemas for referenced tables
        references = {}
        required = list(required)
        while required:

            ktablename = required.pop()
            if ktablename in provided:
                continue

            # Check if we need to include any records
            record_ids = ms.references[ktablename]
            if record_ids:
                rresource = s3db.resource(ktablename, id=list(record_ids))
            else:
                rresource = s3db.resource(ktablename)

            # Serialize the table schema
            rs = S3MobileSchema(rresource)
            schema = rs.serialize()
            spec = {"schema": schema,
                    "types": super_entities(ktablename),
                    }

            # Add directly-serializable settings
            settings = rs.settings
            if settings:
                spec["settings"] = settings

            # Include records as required
            if record_ids:
                fields = schema.keys()
                tree = rresource.export_tree(fields = fields,
                                             references = fields,
                                             msince = msince,
                                             )
                if len(tree.getroot()):
                    data = current.xml.tree2json(tree, as_dict=True)
                    spec["data"] = data

            references[ktablename] = spec

            # Check for dependencies
            for reference in rs.references:
                if reference not in provided:
                    required.append(reference)

            provided.add(ktablename)

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

    # -------------------------------------------------------------------------
    @staticmethod
    def super_entities(tablename):
        """
            Helper method to determine the super entities of a table

            @param tablename: the table name

            @return: a dict {super-table: super-key}
        """

        s3db = current.s3db

        supertables = s3db.get_config(tablename, "super_entity")
        if not supertables:
            supertables = set()
        elif not isinstance(supertables, (tuple, list)):
            supertables = [supertables]

        super_entities = {}
        for tablename in supertables:
            table = s3db.table(tablename)
            if table:
                super_entities[tablename] = table._id.name

        return super_entities

# =============================================================================
class S3MobileCRUD(S3Method):
    """
        Mobile Data Handler

        responds to GET /prefix/name/mform.json     (Schema download)
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

        if method == "mform":
            if representation == "json":
                if http == "GET":
                    output = self.mform(r, **attr)
                else:
                    r.error(405, current.ERROR.BAD_METHOD)
            else:
                r.error(415, current.ERROR.BAD_FORMAT)
        else:
            r.error(405, current.ERROR.BAD_METHOD)

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

        msince = r.get_vars.get("msince")
        if msince:
            msince = s3_parse_datetime(msince)

        # Get the mobile form
        mform = S3MobileForm(resource).serialize(msince=msince)

        # Add controller and function for data exchange
        mform["controller"] = r.controller
        mform["function"] = r.function

        # Convert to JSON
        output = json.dumps(mform, separators=SEPARATORS)

        current.response.headers = {"Content-Type": "application/json"}
        return output

# END =========================================================================
