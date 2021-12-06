# -*- coding: utf-8 -*-

""" S3 Mobile Forms API

    @copyright: 2016-2021 (c) Sahana Software Foundation
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
           "S3MobileSchema",
           "S3MobileForm",
           "S3MobileCRUD",
           )

import json

from gluon import IS_EMPTY_OR, IS_IN_SET, current

from .s3datetime import s3_parse_datetime
from .s3forms import S3SQLCustomForm, S3SQLDummyField, S3SQLField, \
                     S3SQLForm, S3SQLInlineInstruction, S3SQLSectionBreak
from .s3rest import S3Method
from .s3rtb import S3ResourceTree
from .s3utils import s3_get_foreign_key, s3_str
from .s3validators import SEPARATORS

DEFAULT = lambda: None

# JSON-serializable table settings (SERIALIZABLE_OPTS)
# which require preprocessing before they can be passed
# to the mobile client (e.g. i18n)
#PREPROCESS_OPTS = ("subheadings", )
PREPROCESS_OPTS = []

# =============================================================================
class S3MobileFormList:
    """
        Form List Generator
    """

    def __init__(self, masterkey_id=None):
        """
            Args:
                masterkey_id: auth_masterkey record ID to filter the form
                              list by
        """

        T = current.T
        s3db = current.s3db
        settings = current.deployment_settings

        formlist = []
        formdict = {}

        forms = settings.get_mobile_forms()
        if callable(forms):
            forms = forms(masterkey_id)
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
                if isinstance(title, str):
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
                    (ttable.deleted == False)
            if masterkey_id is not None:
                query = (ttable.masterkey_id == masterkey_id) & query
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
                formdict[tablename] = mform

        self.formlist = formlist
        self.forms = formdict

    # -------------------------------------------------------------------------
    def json(self):
        """
            Serialize the form list as JSON (EdenMobile)

            Returns:
                a JSON string
        """

        return json.dumps(self.formlist, separators=SEPARATORS)

# =============================================================================
class S3MobileSchema:
    """
        Table schema for a mobile resource
    """

    # Field types supported for mobile resources
    SUPPORTED_FIELD_TYPES = ("string",
                             "text",
                             "integer",
                             "double",
                             "date",
                             "datetime",
                             "boolean",
                             "reference",
                             "upload",
                             "json",
                             "list:string",
                             "list:integer",
                             )

    # -------------------------------------------------------------------------
    def __init__(self, resource):
        """
            Args:
                resource - the S3Resource
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

        # Initialize lookup list attributes
        self._lookup_only = None
        self._llrepr = None

    # -------------------------------------------------------------------------
    def serialize(self):
        """
            Serialize the table schema

            Returns:
                a JSON-serializable dict containing the table schema
        """

        schema = self._schema
        if schema is None:

            # Initialize
            schema = {}
            self._references = {}

            if not self.lookup_only:
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

            Returns:
                a dict {tablename: [recordID, ...]} of all
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
            subheadings = self._subheadings = self.resource.get_config("subheadings")

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

            from .s3model import SERIALIZABLE_OPTS
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

            Args:
                field: a Field instance

            Returns:
                The field description as JSON-serializable dict
        """

        if not field:
            return None

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
                    reftype = (ktablename,) # [])
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
        if not is_foreign_key and fieldtype not in SUPPORTED_FIELD_TYPES:
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

        if hasattr(field.widget, "mobile"):
            description["widget"] = field.widget.mobile

        # Add required flag if True (False is assumed)
        if self.is_required(field):
            description["required"] = True

        # @todo: add tooltip to description

        # @todo: if field.represent is a base-class S3Represent
        #        (i.e. no custom lookup, no custom represent),
        #        and its field list is not just "name" => pass
        #        that field list as description["represent"]

        # Add field's mobile settings to description (Dynamic Fields)
        msettings = hasattr(field, "s3_settings") and \
                    field.s3_settings and \
                    field.s3_settings.get("mobile")
        if msettings:
            description["settings"] = msettings

        return description

    # -------------------------------------------------------------------------
    @staticmethod
    def is_required(field):
        """
            Determine whether a value is required for a field

            Args:
                field: the Field

            Returns:
                True|False
        """

        required = field.notnull

        if not required and field.requires:
            error = field.validate("")[1]
            if error is not None:
                required = True

        return required

    # -------------------------------------------------------------------------
    @staticmethod
    def get_options(field, lookup=None):
        """
            Get the options for a field with IS_IN_SET

            Args:
                field: the Field
                lookup: the name of the lookup table

            Returns:
                A list of tuples (key, label) with the field options
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
            return None

        elif fieldtype in ("string", "integer", "list:string", "list:integer"):

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

            Args:
                field: the Field
                lookup: the name of the lookup table
                superkey: lookup table is a super-entity

            Returns:
                The default value for the field
        """

        default = field.default

        if default is not None:

            fieldtype = str(field.type)

            if fieldtype[:9] == "reference":

                # Look up the UUID for the default
                uuid = self.get_uuid(lookup, default)
                if uuid:

                    if superkey:
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
                        references = self.references.get(tablename) or set()
                        references.add(record_id)
                        self.references[tablename] = references

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

            Returns:
                A list of Field instances
        """

        resource = self.resource
        resolve_selector = resource.resolve_selector

        table = resource.table
        tablename = resource.tablename

        fields = []
        mobile_form = self._form = []
        mappend = mobile_form.append

        # Prevent duplicates
        fnames = set()
        include = fnames.add

        form = self.mobile_form(resource)

        if isinstance(form, list):
            for element in form:

                selector = None
                if isinstance(element, dict):
                    etype = element.get("type")
                    if etype == "input":
                        selector = element.get("field")
                    elif etype:
                        mappend(element)
                elif isinstance(element, str):
                    selector = element
                else:
                    continue

                if selector:
                    rfield = resolve_selector(selector)
                    fname = rfield.fname
                    if rfield.field and \
                       rfield.tname == tablename and fname not in fnames:
                        fields.append(rfield.field)
                        mappend(element)
                        include(fname)

                        # Other-field
                        other = self.get_other_field(table, rfield.field)
                        if other and other not in fnames:
                            fields.append(table[other])
                            include(other)

        else:
            for element in form.elements:
                if isinstance(element, S3SQLField):
                    rfield = resolve_selector(element.selector)

                    fname = rfield.fname

                    if rfield.field and \
                       rfield.tname == tablename and fname not in fnames:
                        fields.append(rfield.field)
                        mappend(fname)
                        include(fname)

                        # Other-field
                        other = self.get_other_field(table, rfield.field)
                        if other and other not in fnames:
                            fields.append(table[other])
                            include(other)

                elif isinstance(element, S3SQLDummyField):
                    field = {"type": "dummy",
                             "name": element.selector,
                             }
                    mappend(field)

                elif isinstance(element, S3SQLInlineInstruction):
                    field = {"type": "instructions",
                             "do": element.do,
                             "say": element.say,
                             #"name": element.selector,
                             }
                    mappend(field)

                elif isinstance(element, S3SQLSectionBreak):
                    field = {"type": "section-break",
                             #"name": element.selector,
                             }
                    mappend(field)

        if resource.parent and not resource.linktable:

            # Include the parent key
            fkey = resource.fkey
            if fkey not in fnames:
                fields.append(resource.table[fkey])
                #include(fkey)

        return fields

    # -------------------------------------------------------------------------
    @staticmethod
    def get_other_field(table, field):
        """
            Check for an "other"-field
            - additional input for option-widgets when the user chooses
              the "other"-option
            - other-field must be in the schema, but not in the mobile_form

            Args:
                table: the table
                field: the option-field

            Returns:
                The name of the other-field, or None
        """

        other = None

        if hasattr(field, "s3_settings"):
            mobile_settings = field.s3_settings.get("mobile")
            if mobile_settings:
                other = mobile_settings.get("other")

        if other and other in table.fields:
            return other
        else:
            return None

    # -------------------------------------------------------------------------
    @staticmethod
    def has_mobile_form(tablename):
        """
            Check whether a table exposes a mobile form

            Args:
                tablename: the table name

            Returns:
                True|False
        """

        from .s3model import DYNAMIC_PREFIX
        if tablename.startswith(DYNAMIC_PREFIX):

            ttable = current.s3db.s3_table
            query = (ttable.name == tablename) & \
                    (ttable.mobile_form == True) & \
                    (ttable.deleted == False)
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

            Args:
                resource: the S3Resource

            Returns:
                an S3SQLForm instance
        """

        # Get the form definition from "mobile_form" table setting
        form = resource.get_config("mobile_form")
        if not form or not isinstance(form, (S3SQLCustomForm, list)):
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
    @property
    def lookup_only(self):
        """
            Whether the resource shall be exposed as mere lookup list
            without mobile form (lazy property)
        """

        lookup_only = self._lookup_only
        if lookup_only is None:

            resource = self.resource

            mform = resource.get_config("mobile_form")
            if mform is False:
                from .s3fields import S3Represent
                self._llrepr = S3Represent(lookup=resource.tablename)
                lookup_only = True
            elif callable(mform) and not isinstance(mform, S3SQLForm):
                self._llrepr = mform
                lookup_only = True
            else:
                lookup_only = False

            self._lookup_only = lookup_only

        return lookup_only

    # -------------------------------------------------------------------------
    @property
    def llrepr(self):
        """
            The lookup list representation method for the resource
        """

        return self._llrepr if self.lookup_only else None

    # -------------------------------------------------------------------------
    # Utility functions
    # -------------------------------------------------------------------------
    @staticmethod
    def get_uuid(tablename, record_id):
        """
            Look up the UUID of a record

            Args:
                tablename: the table name
                record_id: the record ID

            Returns:
                The UUID of the specified record, or None if
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
class S3MobileForm:
    """
        Mobile representation of an S3SQLForm
    """

    def __init__(self, resource, form=None):
        """
            Args:
                resource: the S3Resource
                form: an S3SQLForm instance to override settings
        """

        self.resource = resource
        self._form = form

        self._config = DEFAULT

    # -------------------------------------------------------------------------
    @property
    def config(self):
        """
            The mobile form configuration (lazy property)

            Returns:
                a dict {tablename, title, options}
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

            Args:
                msince: include look-up records only if modified
                        after this datetime ("modified since")

            Returns:
                A JSON-serialiable dict containing the mobile form
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
        provided = {resource.tablename: (ms, main)}

        # Add schemas for components
        components = self.components()
        for alias in components:

            # Get the component resource
            cresource = resource.components.get(alias)
            if not cresource:
                continue
            ctablename = cresource.tablename

            # Serialize the table schema
            schema = S3MobileSchema(cresource)

            # Add schema, super entities and directly-serializable settings
            spec = components[alias]
            spec["schema"] = schema.serialize()
            spec["types"] = super_entities(ctablename)
            settings = schema.settings
            if settings:
                spec["settings"] = settings

            # If the component has a link table, add it to required schemas
            link = spec.get("link")
            if link:
                required.add(link)

            # Add component reference schemas
            for tname in schema.references:
                required.add(tname)

            # Mark as provided
            provided[tablename] = (schema, spec)

        # Add schemas for referenced tables
        references = {}
        required = list(required)
        while required:

            # Get the referenced resource
            ktablename = required.pop()
            if ktablename in provided:
                # Already provided
                continue
            kresource = s3db.resource(ktablename)

            # Serialize the table schema
            schema = S3MobileSchema(kresource)

            # Add schema, super entities and directly-serializable settings
            spec = {"schema": schema.serialize(),
                    "types": super_entities(ktablename),
                    }
            settings = schema.settings
            if settings:
                spec["settings"] = settings

            # Check for unresolved dependencies
            for reference in schema.references:
                if reference not in provided:
                    required.append(reference)

            # Add to references
            references[ktablename] = spec

            # Mark as provided
            provided[ktablename] = (schema, spec)

        # Collect all required records (e.g. foreign key defaults)
        required_records = {}
        for ktablename in provided:
            schema = provided[ktablename][0]
            for tn, record_ids in schema.references.items():
                if record_ids:
                    all_ids = (required_records.get(tn) or set()) | record_ids
                    required_records[tn] = all_ids

        # Export required records and add them to the specs
        for tn, record_ids in required_records.items():
            kresource = s3db.resource(tn, id=list(record_ids))
            spec = provided[tn][1]
            fields = list(spec["schema"].keys())
            tree = S3ResourceTree(kresource).build(fields = fields,
                                                   references = fields,
                                                   msince = msince,
                                                   )
            if len(tree.getroot()):
                data = current.xml.tree2json(tree, as_dict=True)
                spec["data"] = data

        # Complete the mobile schema spec
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

            Returns:
                a dict with CRUD strings for the resource
        """

        tablename = self.resource.tablename

        # Use the label/plural specified in deployment setting
        config = self.config
        options = config["options"]
        label = options.get("label")
        plural = options.get("plural")

        # Fall back to CRUD title_list
        if not plural or not label:
            crud_strings = current.response.s3.crud_strings.get(tablename)
            if crud_strings:
                if not label:
                    label = crud_strings.get("title_display")
                if not plural:
                    plural = crud_strings.get("title_list")

        # Fall back to the title specified in deployment setting
        if not plural:
            plural = config.get("title")

        # Fall back to capitalized table name
        if not label:
            name = tablename.split("_", 1)[-1]
            label = " ".join(word.capitalize() for word in name.split("_"))

        # Build strings-dict
        strings = {}
        if label:
            strings["label"] = s3_str(label)
        if plural:
            strings["plural"] = s3_str(plural)

        return strings

    # -------------------------------------------------------------------------
    def components(self):
        """
            Add component declarations to the mobile form

            Returns:
                a dict with component declarations for the resource
        """

        resource = self.resource
        tablename = resource.tablename
        pkey = resource._id.name

        options = self.config.get("options")

        aliases = set()
        components = {}

        # Dynamic components, exposed if:
        # - "dynamic_components" is True for the master table, and
        # - "mobile_component" for the component key is not set to False
        dynamic_components = resource.get_config("dynamic_components")
        if dynamic_components:

            # Dynamic components of this table and all its super-entities
            tablenames = [tablename]
            supertables = resource.get_config("super_entity")
            if supertables:
                if isinstance(supertables, (list, tuple)):
                    tablenames.extend(supertables)
                elif supertables:
                    tablenames.append(supertables)

            # Look up corresponding component keys in s3_fields
            s3db = current.s3db
            ftable = s3db.s3_field
            ttable = s3db.s3_table
            join = ttable.on(ttable.id == ftable.table_id)
            query = (ftable.component_key == True) & \
                    (ftable.master.belongs(tablenames)) & \
                    (ftable.deleted == False)
            rows = current.db(query).select(ftable.name,
                                            ftable.component_alias,
                                            ftable.settings,
                                            ttable.name,
                                            join = join,
                                            )

            for row in rows:
                component_key = row.s3_field

                # Skip if mobile_component is set to False
                settings = component_key.settings
                if settings and settings.get("mobile_component") is False:
                    continue

                alias = component_key.component_alias
                if not alias:
                    # Default component alias
                    alias = row.s3_table.name.split("_", 1)[-1]
                aliases.add(alias)

        # Static components, exposed if
        # - configured in "components" option of settings.mobile.forms
        static = options.get("components") if options else None
        if static:
            aliases |= set(static)

        # Construct component descriptions for schema export
        if aliases:
            T = current.T
            hooks = current.s3db.get_components(tablename, names=aliases)
            for alias, hook in hooks.items():

                description = {"table": hook.tablename,
                               "multiple": hook.multiple,
                               }
                if hook.label:
                    description["label"] = s3_str(T(hook.label))
                if hook.plural:
                    description["plural"] =  s3_str(T(hook.plural))

                if hook.pkey != pkey:
                    description["pkey"] = hook.pkey

                linktable = hook.linktable
                if linktable:
                    description.update({"link": str(linktable),
                                        "joinby": hook.lkey,
                                        "key": hook.rkey,
                                        })
                    if hook.fkey != "id":
                        description["fkey"] = hook.fkey
                else:
                    description["joinby"] = hook.fkey

                components[alias] = description

        return components

    # -------------------------------------------------------------------------
    @staticmethod
    def super_entities(tablename):
        """
            Helper method to determine the super entities of a table

            Args:
                tablename: the table name

            Returns:
                a dict {super-table: super-key}
        """

        s3db = current.s3db

        supertables = s3db.get_config(tablename, "super_entity")
        if not supertables:
            supertables = set()
        elif not isinstance(supertables, (tuple, list)):
            supertables = [supertables]

        super_entities = {}
        for super_tablename in supertables:
            super_table = s3db.table(super_tablename)
            if super_table:
                super_entities[super_tablename] = super_table._id.name

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

            Args:
                r: the S3Request instance
                attr: controller attributes
        """

        if r.method == "mform":
            if r.representation == "json":
                if r.http == "GET":
                    return self.mform(r, **attr)
                else:
                    r.error(405, current.ERROR.BAD_METHOD)
            else:
                r.error(415, current.ERROR.BAD_FORMAT)
        else:
            r.error(405, current.ERROR.BAD_METHOD)

    # -------------------------------------------------------------------------
    def mform(self, r, **attr):
        """
            Get the mobile form for the target resource

            Args:
                r: the S3Request instance
                attr: controller attributes

            Returns:
                A JSON string
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
