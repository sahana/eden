# -*- coding: utf-8 -*-

""" S3 Extensions for gluon.dal.Field, reusable fields

    @requires: U{B{I{gluon}} <http://web2py.com>}

    @copyright: 2009-2019 (c) Sahana Software Foundation
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

import datetime
import sys
from itertools import chain
from uuid import uuid4

from gluon import current, A, DIV, Field, IS_EMPTY_OR, IS_IN_SET, IS_TIME, TAG, URL, XML
from gluon.sqlhtml import TimeWidget
from gluon.storage import Storage
from gluon.languages import lazyT

from s3compat import PY2, basestring
from s3dal import SQLCustomType
from .s3datetime import S3DateTime
from .s3navigation import S3ScriptItem
from .s3utils import s3_auth_user_represent, s3_auth_user_represent_name, s3_unicode, s3_str, S3MarkupStripper
from .s3validators import IS_ISO639_2_LANGUAGE_CODE, IS_ONE_OF, IS_UTC_DATE, IS_UTC_DATETIME
from .s3widgets import S3CalendarWidget, S3DateWidget

# =============================================================================
class FieldS3(Field):
    """
        S3 extensions of the gluon.sql.Field class
            - add "sortby" attribute (used by IS_ONE_OF)

        @todo: add parameters supported by newer PyDAL
    """

    def __init__(self, fieldname,
                 type="string",
                 length=None,
                 default=None,
                 required=False,
                 requires="<default>",
                 ondelete="CASCADE",
                 notnull=False,
                 unique=False,
                 uploadfield=True,
                 widget=None,
                 label=None,
                 comment=None,
                 writable=True,
                 readable=True,
                 update=None,
                 authorize=None,
                 autodelete=False,
                 represent=None,
                 uploadfolder=None,
                 compute=None,
                 sortby=None):

        self.sortby = sortby

        Field.__init__(self,
                       fieldname,
                       type=type,
                       length=length,
                       default=default,
                       required=required,
                       requires=requires,
                       ondelete=ondelete,
                       notnull=notnull,
                       unique=unique,
                       uploadfield=uploadfield,
                       widget=widget,
                       label=label,
                       comment=comment,
                       writable=writable,
                       readable=readable,
                       update=update,
                       authorize=authorize,
                       autodelete=autodelete,
                       represent=represent,
                       uploadfolder=uploadfolder,
                       compute=compute,
                       )

# =============================================================================
def s3_fieldmethod(name, f, represent=None, search_field=None):
    """
        Helper to attach a representation method to a Field.Method.

        @param name: the field name
        @param f: the field method
        @param represent: the representation function
        @param search_field: the field to use for searches
               - only used by datatable_filter currently
               - can only be a single field in the same table currently
    """

    if represent is None and search_field is None:
        fieldmethod = Field.Method(name, f)

    else:
        class Handler(object):
            def __init__(self, method, row):
                self.method=method
                self.row=row
            def __call__(self, *args, **kwargs):
                return self.method(self.row, *args, **kwargs)

        if represent is not None:
            if hasattr(represent, "bulk"):
                Handler.represent = represent
            else:
                Handler.represent = staticmethod(represent)

        if search_field is not None:
            Handler.search_field = search_field

        fieldmethod = Field.Method(name, f, handler=Handler)

    return fieldmethod

# =============================================================================
class S3ReusableField(object):
    """
        DRY Helper for reusable fields:

        This creates neither a Table nor a Field, but just
        an argument store. The field is created with the __call__
        method, which is faster than copying an existing field.
    """

    def __init__(self, name, type="string", **attr):

        self.name = name
        self.__type = type
        self.attr = Storage(attr)

    # -------------------------------------------------------------------------
    def __call__(self, name=None, **attr):

        if not name:
            name = self.name

        ia = dict(self.attr)

        DEFAULT = "default"
        widgets = ia.pop("widgets", {})

        if attr:
            empty = attr.pop("empty", True)
            if not empty:
                requires = ia.get("requires")
                if requires:
                    if not isinstance(requires, (list, tuple)):
                        requires = [requires]
                    if requires:
                        r = requires[0]
                        if isinstance(r, IS_EMPTY_OR):
                            requires = r.other
                            ia["requires"] = requires
            widget = attr.pop("widget", DEFAULT)
            ia.update(**attr)
        else:
            widget = DEFAULT

        if isinstance(widget, basestring):
            if widget == DEFAULT and "widget" in ia:
                widget = ia["widget"]
            else:
                if not isinstance(widgets, dict):
                    widgets = {DEFAULT: widgets}
                if widget != DEFAULT and widget not in widgets:
                    raise NameError("Undefined widget: %s" % widget)
                else:
                    widget = widgets.get(widget)
        ia["widget"] = widget

        script = ia.pop("script", None)
        if script:
            comment = ia.get("comment")
            if comment:
                ia["comment"] = TAG[""](comment,
                                        S3ScriptItem(script=script),
                                        )
            else:
                ia["comment"] = S3ScriptItem(script=script)

        if ia.get("sortby") is not None:
            return FieldS3(name, self.__type, **ia)
        else:
            return Field(name, self.__type, **ia)

# =============================================================================
class S3Represent(object):
    """
        Scalable universal field representation for option fields and
        foreign keys. Can be subclassed and tailored to the particular
        model where necessary.

        @group Configuration (in the model): __init__
        @group API (to apply the method): __call__,
                                          multiple,
                                          bulk,
                                          render_list
        @group Prototypes (to adapt in subclasses): lookup_rows,
                                                    represent_row,
                                                    link
        @group Internal Methods: _setup,
                                 _lookup
    """

    def __init__(self,
                 lookup = None,
                 key = None,
                 fields = None,
                 labels = None,
                 options = None,
                 translate = False,
                 linkto = None,
                 show_link = False,
                 multiple = False,
                 hierarchy = False,
                 default = None,
                 none = None,
                 field_sep = " "
                 ):
        """
            Constructor

            @param lookup: the name of the lookup table
            @param key: the field name of the primary key of the lookup table,
                        a field name
            @param fields: the fields to extract from the lookup table, a list
                           of field names
            @param labels: string template or callable to represent rows from
                           the lookup table, callables must return a string
            @param options: dictionary of options to lookup the representation
                            of a value, overrides lookup and key
            @param multiple: web2py list-type (all values will be lists)
            @param hierarchy: render a hierarchical representation, either
                              True or a string template like "%s > %s"
            @param translate: translate all representations (using T)
            @param linkto: a URL (as string) to link representations to,
                           with "[id]" as placeholder for the key
            @param show_link: whether to add a URL to representations
            @param default: default representation for unknown options
            @param none: representation for empty fields (None or empty list)
            @param field_sep: separator to use to join fields
        """

        self.tablename = lookup
        self.table = None
        self.key = key
        self.fields = fields
        self.labels = labels
        self.options = options
        self.list_type = multiple
        self.hierarchy = hierarchy
        self.translate = translate
        self.linkto = linkto
        self.show_link = show_link
        self.default = default
        self.none = none
        self.field_sep = field_sep
        self.setup = False
        self.theset = None
        self.queries = 0
        self.lazy = []
        self.lazy_show_link = False

        self.rows = {}

        self.clabels = None
        self.slabels = None
        self.htemplate = None

        # Attributes to simulate being a function for sqlhtml's count_expected_args()
        # Make sure we indicate only 1 position argument
        if PY2:
            self.func_code = Storage(co_argcount = 1)
            self.func_defaults = None
        else:
            self.__code__ = Storage(co_argcount = 1)
            self.__defaults__ = None

        # Detect lookup_rows override
        if PY2:
            self.custom_lookup = self.lookup_rows.__func__ is not S3Represent.lookup_rows.__func__
        else:
            self.custom_lookup = self.lookup_rows.__func__ is not S3Represent.lookup_rows

    # -------------------------------------------------------------------------
    def lookup_rows(self, key, values, fields=None):
        """
            Lookup all rows referenced by values.
            (in foreign key representations)

            @param key: the key Field
            @param values: the values
            @param fields: the fields to retrieve
        """

        if fields is None:
            fields = []
        fields.append(key)

        if len(values) == 1:
            query = (key == values[0])
        else:
            query = key.belongs(values)
        rows = current.db(query).select(*fields)
        self.queries += 1
        return rows

    # -------------------------------------------------------------------------
    def represent_row(self, row, prefix=None):
        """
            Represent the referenced row.
            (in foreign key representations)

            @param row: the row
            @param prefix: prefix for hierarchical representation

            @return: the representation of the Row, or None if there
                     is an error in the Row
        """

        labels = self.labels

        translated = False

        if self.slabels:
            # String Template or lazyT
            try:
                row_dict = row.as_dict()
            except AttributeError:
                # Row just a dict/Storage after all? (e.g. custom lookup)
                row_dict = row

            # Represent None as self.none
            none = self.none
            for k, v in list(row_dict.items()):
                if v is None:
                    row_dict[k] = none

            v = labels % row_dict

        elif self.clabels:
            # External Renderer
            v = labels(row)

        else:
            # Default
            values = [row[f] for f in self.fields if row[f] not in (None, "")]

            if len(values) > 1:
                # Multiple values => concatenate with separator
                if self.translate:
                    # Translate items individually before concatenating
                    T = current.T
                    values = [T(v) if not type(v) is lazyT else v for v in values]
                    translated = True
                sep = self.field_sep
                v = sep.join(s3_str(value) for value in values)
            elif values:
                v = s3_str(values[0])
            else:
                v = self.none

        if not translated and self.translate and not type(v) is lazyT:
            output = current.T(v)
        else:
            output = v

        if prefix and self.hierarchy:
            return self.htemplate % (prefix, output)

        return output

    # -------------------------------------------------------------------------
    def link(self, k, v, row=None):
        """
            Represent a (key, value) as hypertext link.

                - Typically, k is a foreign key value, and v the
                  representation of the referenced record, and the link
                  shall open a read view of the referenced record.

                - In the base class, the linkto-parameter expects a URL (as
                  string) with "[id]" as placeholder for the key.

            @param k: the key
            @param v: the representation of the key
            @param row: the row with this key (unused in the base class)
        """

        if self.linkto:
            k = s3_str(k)
            return A(v, _href=self.linkto.replace("[id]", k) \
                                         .replace("%5Bid%5D", k))
        else:
            return v

    # -------------------------------------------------------------------------
    def __call__(self, value, row=None, show_link=True):
        """
            Represent a single value (standard entry point).

            @param value: the value
            @param row: the referenced row (if value is a foreign key)
            @param show_link: render the representation as link
        """

        self._setup()
        show_link = show_link and self.show_link

        if self.list_type:
            # Is a list-type => use multiple
            return self.multiple(value,
                                 rows=row,
                                 list_type=False,
                                 show_link=show_link)

        # Prefer the row over the value
        if row and self.table:
            value = row[self.key]

        # Lookup the representation
        if value:
            rows = [row] if row is not None else None
            items = self._lookup([value], rows=rows)
            if value in items:
                k, v = value, items[value]
                r = self.link(k, v, row=self.rows.get(k)) \
                    if show_link else items[value]
            else:
                r = self.default
            return r
        return self.none

    # -------------------------------------------------------------------------
    def multiple(self, values, rows=None, list_type=True, show_link=True):
        """
            Represent multiple values as a comma-separated list.

            @param values: list of values
            @param rows: the referenced rows (if values are foreign keys)
            @param show_link: render each representation as link
        """

        self._setup()
        show_link = show_link and self.show_link

        # Get the values
        if rows and self.table:
            key = self.key
            values = [row[key] for row in rows]
        elif self.list_type and list_type:
            try:
                hasnone = None in values
                if hasnone:
                    values = [i for i in values if i != None]
                values = list(set(chain.from_iterable(values)))
                if hasnone:
                    values.append(None)
            except TypeError:
                raise ValueError("List of lists expected, got %s" % values)
        else:
            values = [values] if type(values) is not list else values

        # Lookup the representations
        if values:
            default = self.default
            items = self._lookup(values, rows=rows)
            if show_link:
                link = self.link
                rows = self.rows
                labels = [[link(k, s3_str(items[k]), row=rows.get(k)), ", "]
                          if k in items else [default, ", "]
                          for k in values]
                if labels:
                    return TAG[""](list(chain.from_iterable(labels))[:-1])
                else:
                    return ""
            else:
                labels = [s3_str(items[k])
                          if k in items else default for k in values]
                if labels:
                    return ", ".join(labels)
        return self.none

    # -------------------------------------------------------------------------
    def bulk(self, values, rows=None, list_type=True, show_link=True):
        """
            Represent multiple values as dict {value: representation}

            @param values: list of values
            @param rows: the rows
            @param show_link: render each representation as link

            @return: a dict {value: representation}

            @note: for list-types, the dict keys will be the individual
                   values within all lists - and not the lists (simply
                   because lists can not be dict keys). Thus, the caller
                   would still have to construct the final string/HTML.
        """

        self._setup()
        show_link = show_link and self.show_link

        # Get the values
        if rows and self.table:
            key = self.key
            _rows = self.rows
            values = set()
            add_value = values.add
            for row in rows:
                value = row[key]
                _rows[value] = row
                add_value(value)
            values = list(values)
        elif self.list_type and list_type:
            try:
                hasnone = None in values
                if hasnone:
                    values = [i for i in values if i != None]
                values = list(set(chain.from_iterable(values)))
                if hasnone:
                    values.append(None)
            except TypeError:
                raise ValueError("List of lists expected, got %s" % values)
        else:
            values = [values] if type(values) is not list else values

        # Lookup the representations
        if values:
            labels = self._lookup(values, rows=rows)
            if show_link:
                link = self.link
                rows = self.rows
                labels = {k: link(k, v, rows.get(k)) for k, v in labels.items()}
            for k in values:
                if k not in labels:
                    labels[k] = self.default
        else:
            labels = {}
        labels[None] = self.none
        return labels

    # -------------------------------------------------------------------------
    def render_list(self, value, labels, show_link=True):
        """
            Helper method to render list-type representations from
            bulk()-results.

            @param value: the list
            @param labels: the labels as returned from bulk()
            @param show_link: render references as links, should
                              be the same as used with bulk()
        """

        show_link = show_link and self.show_link
        if show_link:
            labels = [(labels[v], ", ")
                      if v in labels else (self.default, ", ")
                      for v in value]
            if labels:
                return TAG[""](list(chain.from_iterable(labels))[:-1])
            else:
                return ""
        else:
            return ", ".join([s3_str(labels[v])
                              if v in labels else self.default
                              for v in value])

    # -------------------------------------------------------------------------
    def _setup(self):
        """ Lazy initialization of defaults """

        if self.setup:
            return

        self.queries = 0

        # Default representations
        messages = current.messages
        if self.default is None:
            self.default = s3_str(messages.UNKNOWN_OPT)
        if self.none is None:
            self.none = messages["NONE"]

        # Initialize theset
        if self.options is not None:
            if self.translate:
                T = current.T
                self.theset = {opt: T(label) if isinstance(label, basestring) else label
                               for opt, label in self.options.items()}
            else:
                self.theset = self.options
        else:
            self.theset = {}

        # Lookup table parameters and linkto
        if self.table is None:
            tablename = self.tablename
            if tablename:
                table = current.s3db.table(tablename)
                if table is not None:
                    if self.key is None:
                        self.key = table._id.name
                    if not self.fields:
                        if "name" in table:
                            self.fields = ["name"]
                        else:
                            self.fields = [self.key]
                    self.table = table
                if self.linkto is None and self.show_link:
                    c, f = tablename.split("_", 1)
                    self.linkto = URL(c=c, f=f, args=["[id]"], extension="")

        # What type of renderer do we use?
        labels = self.labels
        # String template?
        self.slabels = isinstance(labels, (basestring, lazyT))
        # External renderer?
        self.clabels = callable(labels)

        # Hierarchy template
        if isinstance(self.hierarchy, basestring):
            self.htemplate = self.hierarchy
        else:
            self.htemplate = "%s > %s"

        self.setup = True

    # -------------------------------------------------------------------------
    def _lookup(self, values, rows=None):
        """
            Lazy lookup values.

            @param values: list of values to lookup
            @param rows: rows referenced by values (if values are foreign keys)
                         optional
        """

        theset = self.theset

        keys = {}
        items = {}
        lookup = {}

        # Check whether values are already in theset
        table = self.table
        for _v in values:
            v = _v
            if v is not None and table and isinstance(v, basestring):
                try:
                    v = int(_v)
                except ValueError:
                    pass
            keys[v] = _v
            if v is None:
                items[_v] = self.none
            elif v in theset:
                items[_v] = theset[v]
            else:
                lookup[v] = True

        if table is None or not lookup:
            return items

        if table and self.hierarchy:
            # Does the lookup table have a hierarchy?
            from .s3hierarchy import S3Hierarchy
            h = S3Hierarchy(table._tablename)
            if h.config:
                def lookup_parent(node_id):
                    parent = h.parent(node_id)
                    if parent and \
                       parent not in theset and \
                       parent not in lookup:
                        lookup[parent] = False
                        lookup_parent(parent)
                    return
                for node_id in list(lookup.keys()):
                    lookup_parent(node_id)
            else:
                h = None
        else:
            h = None

        # Get the primary key
        pkey = self.key
        ogetattr = object.__getattribute__
        try:
            key = ogetattr(table, pkey)
        except AttributeError:
            return items

        # Use the given rows to lookup the values
        pop = lookup.pop
        represent_row = self.represent_row
        represent_path = self._represent_path
        if rows and not self.custom_lookup:
            rows_ = dict((row[key], row) for row in rows)
            self.rows.update(rows_)
            for row in rows:
                k = row[key]
                if k not in theset:
                    if h:
                        theset[k] = represent_path(k,
                                                   row,
                                                   rows = rows_,
                                                   hierarchy = h,
                                                   )
                    else:
                        theset[k] = represent_row(row)
                if pop(k, None):
                    items[keys.get(k, k)] = theset[k]

        # Retrieve additional rows as needed
        if lookup:
            if not self.custom_lookup:
                try:
                    # Need for speed: assume all fields are in table
                    fields = [ogetattr(table, f) for f in self.fields]
                except AttributeError:
                    # Ok - they are not: provide debug output and filter fields
                    current.log.error(sys.exc_info()[1])
                    fields = [ogetattr(table, f)
                              for f in self.fields if hasattr(table, f)]
            else:
                fields = []
            rows = self.lookup_rows(key, list(lookup.keys()), fields=fields)
            rows = {row[key]: row for row in rows}
            self.rows.update(rows)
            if h:
                for k, row in rows.items():
                    if lookup.pop(k, None):
                        items[keys.get(k, k)] = represent_path(k,
                                                               row,
                                                               rows = rows,
                                                               hierarchy = h,
                                                               )
            else:
                for k, row in rows.items():
                    lookup.pop(k, None)
                    items[keys.get(k, k)] = theset[k] = represent_row(row)

        # Anything left gets set to default
        if lookup:
            for k in lookup:
                items[keys.get(k, k)] = self.default

        return items

    # -------------------------------------------------------------------------
    def _represent_path(self, value, row, rows=None, hierarchy=None):
        """
            Recursive helper method to represent value as path in
            a hierarchy.

            @param value: the value
            @param row: the row containing the value
            @param rows: all rows from _loopup as dict
            @param hierarchy: the S3Hierarchy instance
        """

        theset = self.theset

        if value in theset:
            return theset[value]

        prefix = None
        parent = hierarchy.parent(value)

        if parent:
            if parent in theset:
                prefix = theset[parent]
            elif parent in rows:
                prefix = self._represent_path(parent,
                                              rows[parent],
                                              rows=rows,
                                              hierarchy=hierarchy)

        result = self.represent_row(row, prefix=prefix)
        theset[value] = result
        return result

# =============================================================================
class S3RepresentLazy(object):
    """
        Lazy Representation of a field value, utilizes the bulk-feature
        of S3Represent-style representation methods
    """

    def __init__(self, value, renderer):
        """
            Constructor

            @param value: the value
            @param renderer: the renderer (S3Represent instance)
        """

        self.value = value
        self.renderer = renderer

        self.multiple = False
        renderer.lazy.append(value)

    # -------------------------------------------------------------------------
    def __repr__(self):

        return s3_str(self.represent())

    # -------------------------------------------------------------------------
    def represent(self):
        """ Represent as string """

        value = self.value
        renderer = self.renderer
        if renderer.lazy:
            labels = renderer.bulk(renderer.lazy, show_link=False)
            renderer.lazy = []
        else:
            labels = renderer.theset
        if renderer.list_type:
            if self.multiple:
                return renderer.multiple(value, show_link=False)
            else:
                return renderer.render_list(value, labels, show_link=False)
        else:
            if self.multiple:
                return renderer.multiple(value, show_link=False)
            else:
                return renderer(value, show_link=False)

    # -------------------------------------------------------------------------
    def render(self):
        """ Render as HTML """

        value = self.value
        renderer = self.renderer
        if renderer.lazy:
            labels = renderer.bulk(renderer.lazy)
            renderer.lazy = []
        else:
            labels = renderer.theset
        if renderer.list_type:
            if not value:
                value = []
            if self.multiple:
                if len(value) and type(value[0]) is not list:
                    value = [value]
                return renderer.multiple(value)
            else:
                return renderer.render_list(value, labels)
        else:
            if self.multiple:
                return renderer.multiple(value)
            else:
                return renderer(value)

    # -------------------------------------------------------------------------
    def render_node(self, element, attributes, name):
        """
            Render as text or attribute of an XML element

            @param element: the element
            @param attributes: the attributes dict of the element
            @param name: the attribute name
        """

        # Render value
        text = s3_unicode(self.represent())

        # Strip markup + XML-escape
        if text and "<" in text:
            try:
                stripper = S3MarkupStripper()
                stripper.feed(text)
                text = stripper.stripped()
            except:
                pass

        # Add to node
        if text is not None:
            if element is not None:
                element.text = text
            else:
                attributes[name] = text
            return

# =============================================================================
# Meta-fields
#
# Use URNs according to http://tools.ietf.org/html/rfc4122
s3uuid = SQLCustomType(type = "string",
                       native = "VARCHAR(128)",
                       encoder = lambda x: \
                                 "%s" % (uuid4().urn if x == "" else s3_str(x)),
                       decoder = lambda x: x,
                       )

# Representation of user roles (auth_group)
auth_group_represent = S3Represent(lookup="auth_group", fields=["role"])

ALL_META_FIELD_NAMES = ("uuid",
                        "mci",
                        "deleted",
                        "deleted_fk",
                        "deleted_rb",
                        "created_on",
                        "created_by",
                        "modified_on",
                        "modified_by",
                        "approved_by",
                        "owned_by_user",
                        "owned_by_group",
                        "realm_entity",
                        )

# -----------------------------------------------------------------------------
class S3MetaFields(object):
    """ Class to standardize meta-fields """

    # -------------------------------------------------------------------------
    @staticmethod
    def uuid():
        """
            Universally unique record identifier according to RFC4122, as URN
            (e.g. "urn:uuid:fd8f97ab-1252-4d62-9982-8e3f3025307f"); uuids are
            mandatory for synchronization (incl. EdenMobile)
        """

        return Field("uuid", type=s3uuid,
                     default = "",
                     length = 128,
                     notnull = True,
                     unique = True,
                     readable = False,
                     writable = False,
                     )

    # -------------------------------------------------------------------------
    @staticmethod
    def mci():
        """
            Master-Copy-Index - whether this record has been created locally
            or imported ("copied") from another source:
                - mci=0 means "created here"
                - mci>0 means "copied n times"
        """

        return Field("mci", "integer",
                     default = 0,
                     readable = False,
                     writable = False,
                     )

    # -------------------------------------------------------------------------
    @staticmethod
    def deleted():
        """
            Deletion status (True=record is deleted)
        """

        return Field("deleted", "boolean",
                     default = False,
                     readable = False,
                     writable = False,
                     )

    # -------------------------------------------------------------------------
    @staticmethod
    def deleted_fk():
        """
            Foreign key values of this record before deletion (foreign keys
            are set to None during deletion to derestrict constraints)
        """

        return Field("deleted_fk", #"text",
                     readable = False,
                     writable = False,
                     )

    # -------------------------------------------------------------------------
    @staticmethod
    def deleted_rb():
        """
            De-duplication: ID of the record that has replaced this record
        """

        return Field("deleted_rb", "integer",
                     readable = False,
                     writable = False,
                     )

    # -------------------------------------------------------------------------
    @staticmethod
    def created_on():
        """
            Date/time when the record was created
        """

        return Field("created_on", "datetime",
                     readable = False,
                     writable = False,
                     default = datetime.datetime.utcnow,
                     )

    # -------------------------------------------------------------------------
    @staticmethod
    def modified_on():
        """
            Date/time when the record was last modified
        """

        return Field("modified_on", "datetime",
                     readable = False,
                     writable = False,
                     default = datetime.datetime.utcnow,
                     update = datetime.datetime.utcnow,
                     )

    # -------------------------------------------------------------------------
    @classmethod
    def created_by(cls):
        """
            Auth_user ID of the user who created the record
        """

        return Field("created_by", current.auth.settings.table_user,
                     readable = False,
                     writable = False,
                     requires = None,
                     default = cls._current_user(),
                     represent = cls._represent_user(),
                     ondelete = "RESTRICT",
                     )

    # -------------------------------------------------------------------------
    @classmethod
    def modified_by(cls):
        """
            Auth_user ID of the last user who modified the record
        """

        current_user = cls._current_user()
        return Field("modified_by", current.auth.settings.table_user,
                     readable = False,
                     writable = False,
                     requires = None,
                     default = current_user,
                     update = current_user,
                     represent = cls._represent_user(),
                     ondelete = "RESTRICT",
                     )

    # -------------------------------------------------------------------------
    @classmethod
    def approved_by(cls):
        """
            Auth_user ID of the user who has approved the record:
                - None means unapproved
                - 0 means auto-approved
        """

        return Field("approved_by", "integer",
                     readable = False,
                     writable = False,
                     requires = None,
                     represent = cls._represent_user(),
                     )

    # -------------------------------------------------------------------------
    @classmethod
    def owned_by_user(cls):
        """
            Auth_user ID of the user owning the record
        """

        return Field("owned_by_user", current.auth.settings.table_user,
                     readable = False,
                     writable = False,
                     requires = None,
                     default = cls._current_user(),
                     represent = cls._represent_user(),
                     ondelete = "RESTRICT",
                     )

    # -------------------------------------------------------------------------
    @staticmethod
    def owned_by_group():
        """
            Auth_group ID of the user role owning the record
        """

        return Field("owned_by_group", "integer",
                     default = None,
                     readable = False,
                     writable = False,
                     requires = None,
                     represent = auth_group_represent,
                     )

    # -------------------------------------------------------------------------
    @staticmethod
    def realm_entity():
        """
            PE ID of the entity managing the record
        """

        return Field("realm_entity", "integer",
                     default = None,
                     readable = False,
                     writable = False,
                     requires = None,
                     # using a lambda here as we don't want the model
                     # to be loaded yet:
                     represent = lambda pe_id: \
                                 current.s3db.pr_pentity_represent(pe_id),
                     )

    # -------------------------------------------------------------------------
    @classmethod
    def all_meta_fields(cls):
        """
            Standard meta fields for all tables

            @return: tuple of Fields
        """

        return (cls.uuid(),
                cls.mci(),
                cls.deleted(),
                cls.deleted_fk(),
                cls.deleted_rb(),
                cls.created_on(),
                cls.created_by(),
                cls.modified_on(),
                cls.modified_by(),
                cls.approved_by(),
                cls.owned_by_user(),
                cls.owned_by_group(),
                cls.realm_entity(),
                )

    # -------------------------------------------------------------------------
    @classmethod
    def sync_meta_fields(cls):
        """
            Meta-fields required for sync

            @return: tuple of Fields
        """

        return (cls.uuid(),
                cls.mci(),
                cls.deleted(),
                cls.deleted_fk(),
                cls.deleted_rb(),
                cls.created_on(),
                cls.modified_on(),
                )

    # -------------------------------------------------------------------------
    @classmethod
    def owner_meta_fields(cls):
        """
            Record ownership meta-fields

            @return: tuple of Fields
        """

        return (cls.owned_by_user(),
                cls.owned_by_group(),
                cls.realm_entity(),
                )

    # -------------------------------------------------------------------------
    @classmethod
    def timestamps(cls):
        """
            Timestamp meta-fields

            @return: tuple of Fields
        """

        return (cls.created_on(),
                cls.modified_on(),
                )

    # -------------------------------------------------------------------------
    @staticmethod
    def _current_user():
        """
            Get the user ID of the currently logged-in user

            @return: auth_user ID
        """

        if current.auth.is_logged_in():
            # Not current.auth.user to support impersonation
            return current.session.auth.user.id
        else:
            return None

    # -------------------------------------------------------------------------
    @staticmethod
    def _represent_user():
        """
            Representation method for auth_user IDs

            @return: representation function
        """

        if current.deployment_settings.get_ui_auth_user_represent() == "name":
            return s3_auth_user_represent_name
        else:
            return s3_auth_user_represent

# -----------------------------------------------------------------------------
def s3_meta_fields():
    """
        Shortcut commonly used in table definitions: *s3_meta_fields()

        @return: tuple of Field instances
    """

    return S3MetaFields.all_meta_fields()

def s3_all_meta_field_names():
    """
        Shortcut commonly used to include/exclude meta fields

        @return: tuple of field names
    """

    return ALL_META_FIELD_NAMES

# =============================================================================
# Reusable roles fields

def s3_role_required():
    """
        Role Required to access a resource
        - used by GIS for map layer permissions management
    """

    T = current.T
    gtable = current.auth.settings.table_group
    represent = S3Represent(lookup="auth_group", fields=["role"])
    return FieldS3("role_required", gtable,
                   sortby="role",
                   requires = IS_EMPTY_OR(
                                IS_ONE_OF(current.db, "auth_group.id",
                                          represent,
                                          zero=T("Public"))),
                   #widget = S3AutocompleteWidget("admin",
                   #                              "group",
                   #                              fieldname="role"),
                   represent = represent,
                   label = T("Role Required"),
                   comment = DIV(_class="tooltip",
                                 _title="%s|%s" % (T("Role Required"),
                                                   T("If this record should be restricted then select which role is required to access the record here."),
                                                   ),
                                 ),
                   ondelete = "RESTRICT",
                   )

# -----------------------------------------------------------------------------
def s3_roles_permitted(name="roles_permitted", **attr):
    """
        List of Roles Permitted to access a resource
        - used by CMS
    """

    T = current.T
    represent = S3Represent(lookup="auth_group", fields=["role"])
    if "label" not in attr:
        attr["label"] = T("Roles Permitted")
    if "sortby" not in attr:
        attr["sortby"] = "role"
    if "represent" not in attr:
        attr["represent"] = represent
    if "requires" not in attr:
        attr["requires"] = IS_EMPTY_OR(IS_ONE_OF(current.db,
                                                 "auth_group.id",
                                                 represent,
                                                 multiple=True))
    if "comment" not in attr:
        attr["comment"] = DIV(_class="tooltip",
                              _title="%s|%s" % (T("Roles Permitted"),
                                                T("If this record should be restricted then select which role(s) are permitted to access the record here.")))
    if "ondelete" not in attr:
        attr["ondelete"] = "RESTRICT"

    return FieldS3(name, "list:reference auth_group", **attr)

# =============================================================================
def s3_comments(name="comments", **attr):
    """
        Return a standard Comments field
    """

    T = current.T
    if "label" not in attr:
        attr["label"] = T("Comments")
    if "represent" not in attr:
        # Support HTML markup
        attr["represent"] = lambda comments: \
            XML(comments) if comments else current.messages["NONE"]
    if "widget" not in attr:
        from .s3widgets import s3_comments_widget
        _placeholder = attr.pop("_placeholder", None)
        if _placeholder:
            attr["widget"] = lambda f, v: \
                s3_comments_widget(f, v, _placeholder=_placeholder)
        else:
            attr["widget"] = s3_comments_widget
    if "comment" not in attr:
        attr["comment"] = DIV(_class="tooltip",
                              _title="%s|%s" % \
            (T("Comments"),
             T("Please use this field to record any additional information, including a history of the record if it is updated.")))

    return Field(name, "text", **attr)

# =============================================================================
def s3_currency(name="currency", **attr):
    """
        Return a standard Currency field

        @ToDo: Move to a Finance module?
    """

    settings = current.deployment_settings

    if "label" not in attr:
        attr["label"] = current.T("Currency")
    if "default" not in attr:
        attr["default"] = settings.get_fin_currency_default()
    if "requires" not in attr:
        currency_opts = settings.get_fin_currencies()
        attr["requires"] = IS_IN_SET(list(currency_opts.keys()),
                                     zero=None)
    if "writable" not in attr:
        attr["writable"] = settings.get_fin_currency_writable()

    return Field(name, length=3, **attr)

# =============================================================================
def s3_language(name="language", **attr):
    """
        Return a standard Language field

        @param name: the Field name
        @param attr: Field parameters, as well as keywords:
            @keyword empty: allow the field to remain empty:
                            None: accept empty, don't show empty-option (default)
                            True: accept empty, show empty-option
                            False: reject empty, don't show empty-option
                            (keyword ignored if a "requires" is passed)
            @keyword translate: translate the language names into
                                current UI language (not recommended for
                                selector to choose that UI language)

            @keyword select: which languages to show in the selector:
                             - a dict of {lang_code: lang_name}
                             - None to expose all languages
                             - False (or omit) to use L10n_languages setting (default)
    """

    if "label" not in attr:
        attr["label"] = current.T("Language")
    if "default" not in attr:
        attr["default"] = current.deployment_settings.get_L10n_default_language()

    empty = attr.pop("empty", None)
    zero = "" if empty else None

    translate = attr.pop("translate", True)

    if "select" in attr:
        # If select is present => pass as-is
        requires = IS_ISO639_2_LANGUAGE_CODE(select = attr.pop("select"),
                                             sort = True,
                                             translate = translate,
                                             zero = zero,
                                             )
    else:
        # Use L10n_languages deployment setting
        requires = IS_ISO639_2_LANGUAGE_CODE(sort = True,
                                             translate = translate,
                                             zero = zero,
                                             )

    if "requires" not in attr:
        # Value required only if empty is explicitly False
        if empty is False:
            attr["requires"] = requires
        else:
            attr["requires"] = IS_EMPTY_OR(requires)

    if "represent" not in attr:
        attr["represent"] = requires.represent

    return Field(name, length=8, **attr)

# =============================================================================
def s3_date(name="date", **attr):
    """
        Return a standard date-field

        @param name: the field name

        @keyword default: the field default, can be specified as "now" for
                          current date, or as Python date
        @keyword past: number of selectable past months
        @keyword future: number of selectable future months
        @keyword widget: the form widget for the field, can be specified
                         as "date" for S3DateWidget, "calendar" for
                         S3CalendarWidget, or as a web2py FormWidget,
                         defaults to "calendar"
        @keyword calendar: the calendar to use for this widget, defaults
                           to current.calendar
        @keyword start_field: CSS selector for the start field for interval
                              selection
        @keyword default_interval: the default interval
        @keyword default_explicit: whether the user must click the field
                                   to set the default, or whether it will
                                   automatically be set when the value for
                                   start_field is set
        @keyword set_min: CSS selector for another date/time widget to
                          dynamically set the minimum selectable date/time to
                          the value selected in this widget
        @keyword set_max: CSS selector for another date/time widget to
                          dynamically set the maximum selectable date/time to
                          the value selected in this widget

        @note: other S3ReusableField keywords are also supported (in addition
               to the above)

        @note: calendar-option requires widget="calendar" (default), otherwise
               Gregorian calendar is enforced for the field

        @note: set_min/set_max only supported for widget="calendar" (default)

        @note: interval options currently not supported by S3CalendarWidget,
               only available with widget="date"
        @note: start_field and default_interval should be given together

        @note: sets a default field label "Date" => use label-keyword to
               override if necessary
        @note: sets a default validator IS_UTC_DATE => use requires-keyword
               to override if necessary
        @note: sets a default representation S3DateTime.date_represent => use
               represent-keyword to override if necessary

        @ToDo: Different default field name in case we need to start supporting
               Oracle, where 'date' is a reserved word
    """

    attributes = dict(attr)

    # Calendar
    calendar = attributes.pop("calendar", None)

    # Past and future options
    past = attributes.pop("past", None)
    future = attributes.pop("future", None)

    # Label
    if "label" not in attributes:
        attributes["label"] = current.T("Date")

    # Widget-specific options (=not intended for S3ReusableField)
    WIDGET_OPTIONS = ("start_field",
                      "default_interval",
                      "default_explicit",
                      "set_min",
                      "set_max",
                      )

    # Widget
    widget = attributes.get("widget", "calendar")
    widget_options = {}
    if widget == "date":
        # Legacy: S3DateWidget
        # @todo: deprecate (once S3CalendarWidget supports all legacy options)

        # Must use Gregorian calendar
        calendar = "Gregorian"

        # Past/future options
        if past is not None:
            widget_options["past"] = past
        if future is not None:
            widget_options["future"] = future

        # Supported additional widget options
        SUPPORTED_OPTIONS = ("start_field",
                             "default_interval",
                             "default_explicit",
                             )
        for option in WIDGET_OPTIONS:
            if option in attributes:
                if option in SUPPORTED_OPTIONS:
                    widget_options[option] = attributes[option]
                del attributes[option]

        widget = S3DateWidget(**widget_options)

    elif widget == "calendar":

        # Default: calendar widget
        widget_options["calendar"] = calendar

        # Past/future options
        if past is not None:
            widget_options["past_months"] = past
        if future is not None:
            widget_options["future_months"] = future

        # Supported additional widget options
        SUPPORTED_OPTIONS = ("set_min",
                             "set_max",
                             )
        for option in WIDGET_OPTIONS:
            if option in attributes:
                if option in SUPPORTED_OPTIONS:
                    widget_options[option] = attributes[option]
                del attributes[option]

        widget = S3CalendarWidget(**widget_options)

    else:
        # Drop all widget options
        for option in WIDGET_OPTIONS:
            attributes.pop(option, None)

    attributes["widget"] = widget

    # Default value
    now = current.request.utcnow.date()
    if attributes.get("default") == "now":
        attributes["default"] = now

    # Representation
    if "represent" not in attributes:
        attributes["represent"] = lambda dt: \
                                  S3DateTime.date_represent(dt,
                                                            utc=True,
                                                            calendar=calendar,
                                                            )

    # Validator
    if "requires" not in attributes:

        if past is None and future is None:
            requires = IS_UTC_DATE(calendar=calendar)
        else:
            from dateutil.relativedelta import relativedelta
            minimum = maximum = None
            if past is not None:
                minimum = now - relativedelta(months = past)
            if future is not None:
                maximum = now + relativedelta(months = future)
            requires = IS_UTC_DATE(calendar=calendar,
                                   minimum=minimum,
                                   maximum=maximum,
                                   )

        empty = attributes.pop("empty", None)
        if empty is False:
            attributes["requires"] = requires
        else:
            # Default
            attributes["requires"] = IS_EMPTY_OR(requires)

    return Field(name, "date", **attributes)

# =============================================================================
def s3_datetime(name="date", **attr):
    """
        Return a standard datetime field

        @param name: the field name

        @keyword default: the field default, can be specified as "now" for
                          current date/time, or as Python date

        @keyword past: number of selectable past hours
        @keyword future: number of selectable future hours

        @keyword widget: form widget option, can be specified as "date"
                         for date-only, or "datetime" for date+time (default),
                         or as a web2py FormWidget
        @keyword calendar: the calendar to use for this field, defaults
                           to current.calendar
        @keyword set_min: CSS selector for another date/time widget to
                          dynamically set the minimum selectable date/time to
                          the value selected in this widget
        @keyword set_max: CSS selector for another date/time widget to
                          dynamically set the maximum selectable date/time to
                          the value selected in this widget

        @note: other S3ReusableField keywords are also supported (in addition
               to the above)

        @note: sets a default field label "Date" => use label-keyword to
               override if necessary
        @note: sets a default validator IS_UTC_DATE/IS_UTC_DATETIME => use
               requires-keyword to override if necessary
        @note: sets a default representation S3DateTime.date_represent or
               S3DateTime.datetime_represent respectively => use the
               represent-keyword to override if necessary

        @ToDo: Different default field name in case we need to start supporting
               Oracle, where 'date' is a reserved word
    """

    attributes = dict(attr)

    # Calendar
    calendar = attributes.pop("calendar", None)

    # Limits
    limits = {}
    for keyword in ("past", "future", "min", "max"):
        if keyword in attributes:
            limits[keyword] = attributes[keyword]
            del attributes[keyword]

    # Compute earliest/latest
    widget = attributes.pop("widget", None)
    now = current.request.utcnow
    if widget == "date":
        # Helper function to convert past/future hours into
        # earliest/latest datetime, retaining day of month and
        # time of day
        def limit(delta):
            current_month = now.month
            years, hours = divmod(-delta, 8760)
            months = divmod(hours, 744)[0]
            if months > current_month:
                years += 1
            month = divmod((current_month - months) + 12, 12)[1]
            year = now.year - years
            return now.replace(month=month, year=year)

        earliest = limits.get("min")
        if not earliest:
            past = limits.get("past")
            if past is not None:
                earliest = limit(-past)
        latest = limits.get("max")
        if not latest:
            future = limits.get("future")
            if future is not None:
                latest = limit(future)
    else:
        # Compute earliest/latest
        earliest = limits.get("min")
        if not earliest:
            past = limits.get("past")
            if past is not None:
                earliest = now - datetime.timedelta(hours=past)
        latest = limits.get("max")
        if not latest:
            future = limits.get("future")
            if future is not None:
                latest = now + datetime.timedelta(hours=future)

    # Label
    if "label" not in attributes:
        attributes["label"] = current.T("Date")

    # Widget
    set_min = attributes.pop("set_min", None)
    set_max = attributes.pop("set_max", None)
    date_only = False
    if widget == "date":
        date_only = True
        widget = S3CalendarWidget(calendar = calendar,
                                  timepicker = False,
                                  minimum = earliest,
                                  maximum = latest,
                                  set_min = set_min,
                                  set_max = set_max,
                                  )
    elif widget is None or widget == "datetime":
        widget = S3CalendarWidget(calendar = calendar,
                                  timepicker = True,
                                  minimum = earliest,
                                  maximum = latest,
                                  set_min = set_min,
                                  set_max = set_max,
                                  )
    attributes["widget"] = widget

    # Default value
    if attributes.get("default") == "now":
        attributes["default"] = now

    # Representation
    represent = attributes.pop("represent", None)
    represent_method = None
    if represent == "date" or represent is None and date_only:
        represent_method = S3DateTime.date_represent
    elif represent is None:
        represent_method = S3DateTime.datetime_represent
    if represent_method:
        represent = lambda dt: represent_method(dt,
                                                utc=True,
                                                calendar=calendar,
                                                )
    attributes["represent"] = represent

    # Validator and empty-option
    if "requires" not in attributes:
        if date_only:
            validator = IS_UTC_DATE
        else:
            validator = IS_UTC_DATETIME
        requires = validator(calendar=calendar,
                             minimum=earliest,
                             maximum=latest,
                             )
        empty = attributes.pop("empty", None)
        if empty is False:
            attributes["requires"] = requires
        else:
            attributes["requires"] = IS_EMPTY_OR(requires)

    return Field(name, "datetime", **attributes)

# =============================================================================
def s3_time(name="time_of_day", **attr):
    """
        Return a standard time field

        @param name: the field name

        @ToDo: Support minTime/maxTime options for fgtimepicker
    """

    attributes = dict(attr)

    if "widget" not in attributes:
        # adds .time class which launches fgtimepicker from s3.datepicker.js
        attributes["widget"] = TimeWidget.widget

    if "requires" not in attributes:
        requires = IS_TIME()
        empty = attributes.pop("empty", None)
        if empty is False:
            attributes["requires"] = requires
        else:
            attributes["requires"] = IS_EMPTY_OR(requires)

    return Field(name, "time", **attributes)

# END =========================================================================
