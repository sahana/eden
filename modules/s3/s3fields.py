# -*- coding: utf-8 -*-

""" S3 Extensions for gluon.dal.Field, reusable fields

    @requires: U{B{I{gluon}} <http://web2py.com>}

    @copyright: 2009-2013 (c) Sahana Software Foundation
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
from uuid import uuid4
from itertools import chain

from gluon import *
# Here are dependencies listed for reference:
#from gluon import current
#from gluon.dal import Field
#from gluon.html import *
#from gluon.validators import *
from gluon.dal import Query, SQLCustomType
from gluon.storage import Storage
from gluon.languages import lazyT

from s3navigation import S3ScriptItem
from s3utils import S3DateTime, s3_auth_user_represent, s3_auth_user_represent_name, s3_auth_group_represent, s3_unicode
from s3validators import IS_ONE_OF, IS_UTC_DATETIME
from s3widgets import S3AutocompleteWidget, S3DateWidget, S3DateTimeWidget

try:
    db = current.db
except:
    # Running from 000_1st_run
    db = None

# =============================================================================
class FieldS3(Field):
    """
        S3 extensions of the gluon.sql.Field clas

        If Server Side Pagination is on, the proper CAST is needed to
        match the lookup table id
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
                       type,
                       length,
                       default,
                       required,
                       requires,
                       ondelete,
                       notnull,
                       unique,
                       uploadfield,
                       widget,
                       label,
                       comment,
                       writable,
                       readable,
                       update,
                       authorize,
                       autodelete,
                       represent,
                       uploadfolder,
                       compute)

    # -------------------------------------------------------------------------
    def join_via(self, value):
        if self.type.find("reference") == 0:
            return Query(self, "=", value)
        else:
            return QueryS3(self, "join_via", value)

# =============================================================================
class QueryS3(Query):
    """
        S3 extensions of the gluon.sql.Query class

        If Server Side Pagination is on, the proper CAST is needed to match
        the string-typed id to lookup table id
    """

    def __init__(self, left, op=None, right=None):

        if op <> "join_via":
            Query.__init__(self, left, op, right)
        else:
            self.sql = "CAST(TRIM(%s,"|") AS INTEGER)=%s" % (left, right)

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

        ia = Storage(self.attr)

        if attr:
            if not attr.get("empty", True):
                requires = ia.requires
                if requires:
                    if not isinstance(requires, (list, tuple)):
                        requires = [requires]
                    if requires:
                        r = requires[0]
                        if isinstance(r, IS_EMPTY_OR):
                            requires = r.other
                            ia.update(requires=requires)
            if "empty" in attr:
                del attr["empty"]
            ia.update(**attr)

        if "script" in ia:
            if ia.script:
                if ia.comment:
                    ia.comment = TAG[""](ia.comment,
                                         S3ScriptItem(script=ia.script))
                else:
                    ia.comment = S3ScriptItem(script=ia.script)
            del ia["script"]

        if ia.sortby is not None:
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
                 lookup=None,
                 key=None,
                 fields=None,
                 labels=None,
                 options=None,
                 translate=False,
                 linkto=None,
                 show_link=False,
                 multiple=False,
                 default=None,
                 none=None):
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
            @param translate: translate all representations (using T)
            @param linkto: a URL (as string) to link representations to,
                           with "[id]" as placeholder for the key
            @param show_link: whether to add a URL to representations
            @param default: default representation for unknown options
            @param none: representation for empty fields (None or empty list)
        """

        self.tablename = lookup
        self.table = None
        self.key = key
        self.fields = fields
        self.labels = labels
        self.options = options
        self.list_type = multiple
        self.translate = translate
        self.linkto = linkto
        self.show_link = show_link
        self.default = default
        self.none = none
        self.setup = False
        self.theset = None
        self.queries = 0
        self.lazy = []
        self.lazy_show_link = False
        
        # Attributes to simulate being a function for sqlhtml's represent()
        # Make sure we indicate only 1 position argument
        self.func_code = Storage(co_argcount = 1)
        self.func_defaults = None

        if hasattr(self, "lookup_rows"):
            self.custom_lookup = True
        else:
            self.lookup_rows = self._lookup_rows
            self.custom_lookup = False

    # -------------------------------------------------------------------------
    def _lookup_rows(self, key, values, fields=[]):
        """
            Lookup all rows referenced by values.
            (in foreign key representations)

            @param key: the key Field
            @param values: the values
            @param fields: the fields to retrieve
        """

        fields.append(key)
        if len(values) == 1:
            query = (key == values[0])
        else:
            query = key.belongs(values)
        rows = current.db(query).select(*fields)
        self.queries += 1
        return rows

    # -------------------------------------------------------------------------
    def represent_row(self, row):
        """
            Represent the referenced row.
            (in foreign key representations)

            @param row: the row

            @return: the representation of the Row, or None if there
                     is an error in the Row
        """

        labels = self.labels

        if self.slabels:
            # String Template
            v = labels % row
        elif self.clabels:
            # External Renderer
            v = labels(row)
        else:
            # Default
            values = [row[f] for f in self.fields if row[f] not in (None, "")]
            if values:
                v = " ".join([s3_unicode(v) for v in values])
            else:
                v = self.none
        if self.translate and not type(v) is lazyT:
            return current.T(v)
        else:
            return v

    # -------------------------------------------------------------------------
    def link(self, k, v):
        """
            Represent a (key, value) as hypertext link.

                - Typically, k is a foreign key value, and v the
                  representation of the referenced record, and the link
                  shall open a read view of the referenced record.

                - In the base class, the linkto-parameter expects a URL (as
                  string) with "[id]" as placeholder for the key.

            @param k: the key
            @param v: the representation of the key
        """

        if self.linkto:
            k = s3_unicode(k)
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
                r = self.link(value, items[value]) \
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
                labels = [[link(v, s3_unicode(items[v])), ", "]
                          if v in items else [default, ", "]
                          for v in values]
                if labels:
                    return TAG[""](list(chain.from_iterable(labels))[:-1])
                else:
                    return ""
            else:
                labels = [s3_unicode(items[v])
                          if v in items else default for v in values]
                if labels:
                    return ", ".join(labels)
        return self.none

    # -------------------------------------------------------------------------
    def bulk(self, values, rows=None, list_type=True, show_link=True):
        """
            Represent multiple values as dict {value: representation}

            @param values: list of values
            @param rows: the referenced rows (if values are foreign keys)
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
            labels = self._lookup(values, rows=rows)
            if show_link:
                link = self.link
                labels = dict([(v, link(v, r)) for v, r in labels.items()])
            for v in values:
                if v not in labels:
                    labels[v] = self.default
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
            return ", ".join([s3_unicode(labels[v])
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
            self.default = s3_unicode(messages.UNKNOWN_OPT)
        if self.none is None:
            self.none = s3_unicode(messages["NONE"])

        # Initialize theset
        if self.options is not None:
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
                    self.linkto = URL(c=c, f=f, args=["[id]"])

        # What type of renderer do we use?
        labels = self.labels
        # String template?
        self.slabels = isinstance(labels, basestring)
        # External renderer?
        self.clabels = callable(labels)

        self.setup = True
        return

    # -------------------------------------------------------------------------
    def _lookup(self, values, rows=None):
        """
            Lazy lookup values.

            @param values: list of values to lookup
            @param rows: rows referenced by values (if values are foreign keys)
                         optional
        """

        theset = self.theset
        
        items = {}
        lookup = {}

        # Check whether values are already in theset
        for v in values:
            if v is None:
                items[v] = self.none
            elif v in theset:
                items[v] = theset[v]
            else:
                lookup[v] = True
        if self.table is None or not lookup:
            return items

        # Get the primary key
        pkey = self.key
        table = self.table
        ogetattr = object.__getattribute__
        try:
            key = ogetattr(table, pkey)
        except AttributeError:
            return items

        # Use the given rows to lookup the values
        pop = lookup.pop
        represent_row = self.represent_row
        if rows and not self.custom_lookup:
            for row in rows:
                k = row[key]
                if k not in theset:
                    theset[k] = represent_row(row)
                if pop(k, None):
                    items[k] = theset[k]

        # Retrieve additional rows as needed
        if lookup:
            if not self.custom_lookup:
                try:
                    # Need for speed: assume all fields are in table
                    fields = [ogetattr(table, f) for f in self.fields]
                except AttributeError:
                    # Ok - they are not: provide debug output and filter fields
                    if current.response.s3.debug:
                        from s3utils import s3_debug
                        s3_debug(sys.exc_info()[1])
                    fields = [ogetattr(table, f)
                              for f in self.fields if hasattr(table, f)]
            else:
                fields = []
            rows = self.lookup_rows(key, lookup.keys(), fields=fields)
            for row in rows:
                k = row[key]
                lookup.pop(k, None)
                items[k] = theset[k] = represent_row(row)

        if lookup:
            for k in lookup:
                items[k] = self.default

        # Done
        return items

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

        return s3_unicode(self.represent())

    # -------------------------------------------------------------------------
    def represent(self):
        """ Represent as string """

        value = self.value
        renderer = self.renderer
        if renderer.lazy:
            labels = renderer.bulk(renderer.lazy)
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
        text = self.represent()
        if hasattr(text, "xml"):
            text = s3_unicode(text)

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
# Record identity meta-fields

# Use URNs according to http://tools.ietf.org/html/rfc4122
s3uuid = SQLCustomType(type = "string",
                       native = "VARCHAR(128)",
                       encoder = lambda x: "%s" % (uuid4().urn
                                    if x == ""
                                    else str(x.encode("utf-8"))),
                       decoder = lambda x: x)

if db and current.db._adapter.represent("X", s3uuid) != "'X'":
    # Old web2py DAL, must add quotes in encoder
    s3uuid = SQLCustomType(type = "string",
                           native = "VARCHAR(128)",
                           encoder = (lambda x: "'%s'" % (uuid4().urn
                                        if x == ""
                                        else str(x.encode("utf-8")).replace("'", "''"))),
                           decoder = (lambda x: x))

# Universally unique identifier for a record
s3_meta_uuid = S3ReusableField("uuid", type=s3uuid,
                               length=128,
                               notnull=True,
                               unique=True,
                               readable=False,
                               writable=False,
                               default="")

# Master-Copy-Index (for Sync)
s3_meta_mci = S3ReusableField("mci", "integer",
                              default=0,
                              readable=False,
                              writable=False)

def s3_uid():
    return (s3_meta_uuid(),
            s3_meta_mci())

# =============================================================================
# Record "soft"-deletion meta-fields

# "Deleted"-flag
s3_meta_deletion_status = S3ReusableField("deleted", "boolean",
                                          readable=False,
                                          writable=False,
                                          default=False)

# Parked foreign keys of a deleted record in JSON format
# => to be restored upon "un"-delete
s3_meta_deletion_fk = S3ReusableField("deleted_fk", #"text",
                                      readable=False,
                                      writable=False)

# ID of the record replacing this record
# => for record merger (de-duplication)
s3_meta_deletion_rb = S3ReusableField("deleted_rb", "integer",
                                      readable=False,
                                      writable=False)

def s3_deletion_status():
    return (s3_meta_deletion_status(),
            s3_meta_deletion_fk(),
            s3_meta_deletion_rb())

# =============================================================================
# Record timestamp meta-fields

s3_meta_created_on = S3ReusableField("created_on", "datetime",
                                     readable=False,
                                     writable=False,
                                     default=lambda: \
                                        datetime.datetime.utcnow())

s3_meta_modified_on = S3ReusableField("modified_on", "datetime",
                                      readable=False,
                                      writable=False,
                                      default=lambda: \
                                        datetime.datetime.utcnow(),
                                      update=lambda: \
                                        datetime.datetime.utcnow())

def s3_timestamp():
    return (s3_meta_created_on(),
            s3_meta_modified_on())

# =============================================================================
# Record authorship meta-fields
def s3_authorstamp():
    """
        Record ownership meta-fields
    """

    auth = current.auth
    utable = auth.settings.table_user

    if auth.is_logged_in():
        current_user = current.session.auth.user.id
    else:
        current_user = None

    if current.deployment_settings.get_ui_auth_user_represent() == "name":
        represent = s3_auth_user_represent_name
    else:
        represent = s3_auth_user_represent

    # Author of a record
    s3_meta_created_by = S3ReusableField("created_by", utable,
                                         readable=False,
                                         writable=False,
                                         requires=None,
                                         default=current_user,
                                         represent=represent,
                                         ondelete="RESTRICT")

    # Last author of a record
    s3_meta_modified_by = S3ReusableField("modified_by", utable,
                                          readable=False,
                                          writable=False,
                                          requires=None,
                                          default=current_user,
                                          update=current_user,
                                          represent=represent,
                                          ondelete="RESTRICT")

    return (s3_meta_created_by(),
            s3_meta_modified_by())

# =============================================================================
def s3_ownerstamp():
    """
        Record ownership meta-fields
    """

    auth = current.auth
    utable = auth.settings.table_user

    # Individual user who owns the record
    s3_meta_owned_by_user = S3ReusableField("owned_by_user", utable,
                                            readable=False,
                                            writable=False,
                                            requires=None,
                                            default=current.session.auth.user.id
                                                        if auth.is_logged_in()
                                                        else None,
                                            represent=lambda id: \
                                                id and s3_auth_user_represent(id) or \
                                                       current.messages.UNKNOWN_OPT,
                                            ondelete="RESTRICT")

    # Role of users who collectively own the record
    s3_meta_owned_by_group = S3ReusableField("owned_by_group", "integer",
                                             readable=False,
                                             writable=False,
                                             requires=None,
                                             default=None,
                                             represent=s3_auth_group_represent)

    # Person Entity controlling access to this record
    s3_meta_realm_entity = S3ReusableField("realm_entity", "integer",
                                              readable=False,
                                              writable=False,
                                              requires=None,
                                              default=None,
                                              # use a lambda here as we don't
                                              # want the model to be loaded yet
                                              represent=lambda val: \
                                                current.s3db.pr_pentity_represent(val))
    return (s3_meta_owned_by_user(),
            s3_meta_owned_by_group(),
            s3_meta_realm_entity())

# =============================================================================
def s3_meta_fields():
    """
        Normal meta-fields added to every table
    """

    utable = current.auth.settings.table_user

    # Approver of a record
    s3_meta_approved_by = S3ReusableField("approved_by", "integer",
                                          readable=False,
                                          writable=False,
                                          requires=None,
                                          represent=s3_auth_user_represent)

    fields = (s3_meta_uuid(),
              s3_meta_mci(),
              s3_meta_deletion_status(),
              s3_meta_deletion_fk(),
              s3_meta_deletion_rb(),
              s3_meta_created_on(),
              s3_meta_modified_on(),
              s3_meta_approved_by(),
              )
    fields = (fields + s3_authorstamp() + s3_ownerstamp())
    return fields

def s3_all_meta_field_names():
    return [field.name for field in s3_meta_fields()]

# =============================================================================
# Reusable roles fields

def s3_role_required():
    """
        Role Required to access a resource
        - used by GIS for map layer permissions management
    """

    T = current.T
    gtable = current.auth.settings.table_group
    f = S3ReusableField("role_required", gtable,
            sortby="role",
            requires = IS_NULL_OR(
                        IS_ONE_OF(db, "auth_group.id",
                                  "%(role)s",
                                  zero=T("Public"))),
            widget = S3AutocompleteWidget("admin",
                                          "group",
                                          fieldname="role"),
            represent = s3_auth_group_represent,
            label = T("Role Required"),
            comment = DIV(_class="tooltip",
                          _title="%s|%s" % (T("Role Required"),
                                            T("If this record should be restricted then select which role is required to access the record here."))),
            ondelete = "RESTRICT")
    return f()


# -----------------------------------------------------------------------------
def s3_roles_permitted(name="roles_permitted", **attr):
    """
        List of Roles Permitted to access a resource
        - used by CMS
    """

    from s3validators import IS_ONE_OF

    T = current.T
    if "label" not in attr:
        label = T("Roles Permitted")
    if "sortby" not in attr:
        sortby = "role"
    if "represent" not in attr:
        represent = s3_auth_group_represent
    if "requires" not in attr:
        requires = IS_NULL_OR(IS_ONE_OF(current.db,
                                        "auth_group.id",
                                        "%(role)s",
                                        multiple=True))
    if "comment" not in attr:
        comment = DIV(_class="tooltip",
                          _title="%s|%s" % (T("Roles Permitted"),
                                            T("If this record should be restricted then select which role(s) are permitted to access the record here.")))
    if "ondelete" not in attr:
        ondelete = "RESTRICT"

    f = S3ReusableField(name, "list:reference auth_group",
                        sortby = sortby,
                        requires = requires,
                        represent = represent,
                        # @ToDo
                        #widget = S3CheckboxesWidget(lookup_table_name = "auth_group",
                        #                            lookup_field_name = "role",
                        #                            multiple = True),
                        label = label,
                        comment = comment,
                        ondelete = ondelete)
    return f()

# =============================================================================
# Comments
#
def s3_comments(name="comments", **attr):
    """
        Return a standard Comments field
    """

    from s3widgets import s3_comments_widget

    T = current.T
    if "label" not in attr:
        attr["label"] = T("Comments")
    if "represent" not in attr:
        attr["represent"] = lambda comments: comments or current.messages["NONE"]
    if "widget" not in attr:
        attr["widget"] = s3_comments_widget
    if "comment" not in attr:
        attr["comment"] = DIV(_class="tooltip",
                              _title="%s|%s" % \
            (T("Comments"),
             T("Please use this field to record any additional information, including a history of the record if it is updated.")))

    f = S3ReusableField(name, "text",
                        **attr)
    return f()

# =============================================================================
# Currency field
#
# @ToDo: Move to a Finance module
#

def s3_currency(name="currency", **attr):
    """
        Return a standard Currency field
    """

    settings = current.deployment_settings

    if "label" not in attr:
        attr["label"] = current.T("Currency")
    if "default" not in attr:
        attr["default"] = settings.get_fin_currency_default()
    if "requires" not in attr:
        currency_opts = settings.get_fin_currencies()
        attr["requires"] = IS_IN_SET(currency_opts.keys(),
                                     zero=None)
    if "writable" not in attr:
         attr["writable"] = settings.get_fin_currency_writable()

    f = S3ReusableField(name, length=3,
                        **attr)
    return f()

# =============================================================================
# Date field
#

def s3_date(name="date", **attr):
    """
        Return a standard Date field

        Additional options to normal S3ReusableField:
            default == "now" (in addition to usual meanings)
            past = x months
            future = x months
    """

    if "past" in attr:
        past = attr["past"]
        del attr["past"]
    else:
        past = None
    if "future" in attr:
        future = attr["future"]
        del attr["future"]
    else:
        future = None

    if "default" in attr and attr["default"] == "now":
        attr["default"] = current.request.utcnow
    if "label" not in attr:
        attr["label"] = current.T("Date")
    if "represent" not in attr:
        attr["represent"] = lambda d: S3DateTime.date_represent(d,
                                                                utc=True)
    if "requires" not in attr:
        if past is None and future is None:
            requires = IS_DATE(
                    format=current.deployment_settings.get_L10n_date_format()
                )
        else:
            now = current.request.utcnow.date()
            current_month = now.month
            if past is None:
                future_month = now.month + future
                if future_month <= 12:
                    max = now.replace(month=future_month)
                else:
                    current_year = now.year
                    years = int(future_month/12)
                    future_year = current_year + years
                    future_month = future_month - (years * 12)
                    if future_month:
                        max = now.replace(year=future_year,
                                          month=future_month)
                    else:
                        max = now.replace(year=future_year)
                requires = IS_DATE_IN_RANGE(
                        format=current.deployment_settings.get_L10n_date_format(),
                        maximum=max,
                        error_message=current.T("Date must be %(max)s or earlier!")
                    )
            elif future is None:
                if past < current_month:
                    min = now.replace(month=current_month - past)
                else:
                    current_year = now.year
                    past_years = int(past/12)
                    past_months = past - (past_years * 12)
                    past_month = current_month - past_months
                    if past_month:
                        min = now.replace(year=current_year - past_years,
                                          month=past_month)
                    else:
                        min = now.replace(year=current_year - past_years)
                requires = IS_DATE_IN_RANGE(
                        format=current.deployment_settings.get_L10n_date_format(),
                        minimum=min,
                        error_message=current.T("Date must be %(min)s or later!")
                    )
            else:
                future_month = now.month + future
                if future_month <= 12:
                    max = now.replace(month=future_month)
                else:
                    current_year = now.year
                    years = int(future_month/12)
                    future_year = now.year + years
                    future_month = future_month - (years * 12)
                    if future_month:
                        max = now.replace(year=future_year,
                                          month=future_month)
                    else:
                        max = now.replace(year=future_year)
                if past < current_month:
                    min = now.replace(month=current_month - past)
                else:
                    current_year = now.year
                    past_years = int(past/12)
                    past_months = past - (past_years * 12)
                    past_month = current_month - past_months
                    if past_month:
                        min = now.replace(year=current_year - past_years,
                                          month=past_month)
                    else:
                        min = now.replace(year=current_year - past_years)
                requires = IS_DATE_IN_RANGE(
                        format=current.deployment_settings.get_L10n_date_format(),
                        maximum=max,
                        minimum=min,
                        error_message=current.T("Date must be between %(min)s and %(max)s!")
                    )
        if "empty" in attr:
            if attr["empty"] is False:
                attr["requires"] = requires
            else:
                attr["requires"] = IS_EMPTY_OR(requires)
            del attr["empty"]
        else:
            # Default
            attr["requires"] = IS_EMPTY_OR(requires)
    if "widget" not in attr:
        if past is None and future is None:
            attr["widget"] = S3DateWidget()
        elif past is None:
            attr["widget"] = S3DateWidget(future=future)
        elif future is None:
            attr["widget"] = S3DateWidget(past=past)
        else:
            attr["widget"] = S3DateWidget(past=past, future=future)

    f = S3ReusableField(name, "date", **attr)
    return f()

# =============================================================================
# Datetime field
#

def s3_datetime(name="date", **attr):
    """
        Return a standard Datetime field

        Additional options to normal S3ReusableField:
            default = "now" (in addition to usual meanings)
            represent = "date" (in addition to usual meanings)
            widget = "date" (in addition to usual meanings)
            past = x hours
            future = x hours
    """

    if "past" in attr:
        past = attr["past"]
        del attr["past"]
    else:
        past = None
    if "future" in attr:
        future = attr["future"]
        del attr["future"]
    else:
        future = None

    if "default" in attr and attr["default"] == "now":
        attr["default"] = current.request.utcnow
    if "label" not in attr:
        attr["label"] = current.T("Date")
    if "represent" not in attr:
        attr["represent"] = lambda dt: S3DateTime.datetime_represent(dt,
                                                                     utc=True)
    elif attr["represent"] == "date":
        attr["represent"] = lambda dt: S3DateTime.date_represent(dt,
                                                                 utc=True)

    if "widget" not in attr:
        if past is None and future is None:
            attr["widget"] = S3DateTimeWidget()
        elif past is None:
            attr["widget"] = S3DateTimeWidget(future=future)
        elif future is None:
            attr["widget"] = S3DateTimeWidget(past=past)
        else:
            attr["widget"] = S3DateTimeWidget(past=past, future=future)
    elif attr["widget"] == "date":
        if past is None and future is None:
            attr["widget"] = S3DateWidget()
            requires = IS_DATE(
                    format=current.deployment_settings.get_L10n_date_format()
                )
        else:
            now = current.request.utcnow.date()
            current_month = now.month
            if past is None:
                future = int(round(future/744.0, 0))
                attr["widget"] = S3DateWidget(future=future)
                future_month = now.month + future
                if future_month <= 12:
                    max = now.replace(month=future_month)
                else:
                    current_year = now.year
                    years = int(future_month/12)
                    future_year = current_year + years
                    future_month = future_month - (years * 12)
                    if future_month:
                        max = now.replace(year=future_year,
                                          month=future_month)
                    else:
                        max = now.replace(year=future_year)
                requires = IS_DATE_IN_RANGE(
                        format=current.deployment_settings.get_L10n_date_format(),
                        maximum=max,
                        error_message=current.T("Date must be %(max)s or earlier!")
                    )
            elif future is None:
                past = int(round(past/744.0, 0))
                attr["widget"] = S3DateWidget(past=past)
                if past < current_month:
                    min = now.replace(month=current_month - past)
                else:
                    current_year = now.year
                    past_years = int(past/12)
                    past_months = past - (past_years * 12)
                    past_month = current_month - past_months
                    if past_month:
                        min = now.replace(year=current_year - past_years,
                                          month=past_month)
                    else:
                        min = now.replace(year=current_year - past_years)
                requires = IS_DATE_IN_RANGE(
                        format=current.deployment_settings.get_L10n_date_format(),
                        minimum=min,
                        error_message=current.T("Date must be %(min)s or later!")
                    )
            else:
                future = int(round(future/744.0, 0))
                past = int(round(past/744.0, 0))
                attr["widget"] = S3DateWidget(past=past, future=future)
                future_month = now.month + future
                if future_month <= 12:
                    max = now.replace(month=future_month)
                else:
                    current_year = now.year
                    years = int(future_month/12)
                    future_year = now.year + years
                    future_month = future_month - (years * 12)
                    if future_month:
                        max = now.replace(year=future_year,
                                          month=future_month)
                    else:
                        max = now.replace(year=future_year)
                if past < current_month:
                    min = now.replace(month=current_month - past)
                else:
                    current_year = now.year
                    past_years = int(past/12)
                    past_months = past - (past_years * 12)
                    past_month = current_month - past_months
                    if past_month:
                        min = now.replace(year=current_year - past_years,
                                          month=past_month)
                    else:
                        min = now.replace(year=current_year - past_years)
                requires = IS_DATE_IN_RANGE(
                        format=current.deployment_settings.get_L10n_date_format(),
                        maximum=max,
                        minimum=min,
                        error_message=current.T("Date must be between %(min)s and %(max)s!")
                    )
        if "empty" in attr:
            if attr["empty"] is False:
                attr["requires"] = requires
            else:
                attr["requires"] = IS_EMPTY_OR(requires)
            del attr["empty"]
        else:
            # Default
            attr["requires"] = IS_EMPTY_OR(requires)

    if "requires" not in attr:
        if past is None and future is None:
            requires = IS_UTC_DATETIME(
                    format=current.deployment_settings.get_L10n_datetime_format()
                )
        else:
            now = current.request.utcnow
            if past is None:
                max = now + datetime.timedelta(hours=future)
                requires = IS_UTC_DATETIME(
                        format=current.deployment_settings.get_L10n_datetime_format(),
                        maximum=max,
                        error_message=current.T("Date must be %(max)s or earlier!")
                    )
            elif future is None:
                min = now - datetime.timedelta(hours=past)
                requires = IS_UTC_DATETIME(
                        format=current.deployment_settings.get_L10n_datetime_format(),
                        minimum=min,
                        error_message=current.T("Date must be %(min)s or later!")
                    )
            else:
                min = now - datetime.timedelta(hours=past)
                max = now + datetime.timedelta(hours=future)
                requires = IS_UTC_DATETIME(
                        format=current.deployment_settings.get_L10n_datetime_format(),
                        maximum=max,
                        minimum=min,
                        error_message=current.T("Date must be between %(min)s and %(max)s!")
                    )
        if "empty" in attr:
            if attr["empty"] is False:
                attr["requires"] = requires
            else:
                attr["requires"] = IS_EMPTY_OR(requires)
            del attr["empty"]
        else:
            # Default
            attr["requires"] = IS_EMPTY_OR(requires)

    f = S3ReusableField(name, "datetime", **attr)
    return f()

# END =========================================================================
