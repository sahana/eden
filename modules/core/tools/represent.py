"""
    Representation Methods and Tools

    Copyright: 2009-2022 (c) Sahana Software Foundation

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

__all__ = ("BooleanRepresent",
           "S3Represent",
           "S3RepresentLazy",
           "S3PriorityRepresent",
           "XMLContentsRepresent",
           "s3_URLise",
           "s3_avatar_represent",
           "s3_comments_represent",
           "s3_datatable_truncate",
           "s3_format_fullname",
           "s3_fullname",
           "s3_fullname_bulk",
           "s3_phone_represent",
           "s3_qrcode_represent",
           "s3_text_represent",
           "s3_truncate",
           "s3_trunk8",
           "s3_url_represent",
           "s3_yes_no_represent",
           "represent_file",
           "represent_image",
           "represent_option",
           "represent_hours",
           "represent_normal",
           "represent_occupancy",
           )

import os
import re
import sys

from itertools import chain

from gluon import current, A, DIV, I, IMG, IS_URL, SPAN, TAG, URL, XML
from gluon.storage import Storage
from gluon.languages import lazyT

from .convert import s3_str
from .utils import MarkupStripper, luminance

URLSCHEMA = re.compile(r"((?:(())(www\.([^/?#\s]*))|((http(s)?|ftp):)"
                       r"(//([^/?#\s]*)))([^?#\s]*)(\?([^#\s]*))?(#([^\s]*))?)")

# =============================================================================
class S3Represent:
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
                 lookup = None, *,
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
                 color = None,
                 field_sep = " "
                 ):
        """
            Args:
                lookup: the name of the lookup table
                key: the field name of the primary key of the lookup table,
                     a field name
                fields: the fields to extract from the lookup table, a list
                        of field names
                labels: string template or callable to represent rows from
                        the lookup table, callables must return a string
                options: dictionary of options to lookup the representation
                         of a value, overrides lookup and key
                multiple: web2py list-type (all values will be lists)
                hierarchy: render a hierarchical representation, either
                           True or a string template like "%s > %s"
                translate: translate all representations (using T)
                linkto: a URL (as string) to link representations to,
                        with "[id]" as placeholder for the key
                show_link: whether to add a URL to representations
                default: default representation for unknown options
                none: representation for empty fields (None or empty list)
                color: field for color-code in lookup table, activates
                       color-coded representation
                field_sep: separator to use to join fields
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
        self.color = color
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
        self.__code__ = Storage(co_argcount = 1)
        self.__defaults__ = None

        # Detect lookup_rows override
        self.custom_lookup = self.lookup_rows.__func__ is not S3Represent.lookup_rows

    # -------------------------------------------------------------------------
    def lookup_rows(self, key, values, fields=None):
        """
            Lookup all rows referenced by values (in foreign key representations)

            Args:
                key: the key Field
                values: the values
                fields: the fields to retrieve
        """

        if fields is None:
            fields = []
        fields.append(key)

        table = self.table
        color = self.color
        if table and color and color in table.fields:
            fields.append(table[color])

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
            Represent the referenced row (in foreign key representations)

            Args:
                row: the row

            Returns:
                the representation of the Row, or None if there is an error
                in the Row
        """

        labels = self.labels

        none = self.none

        translated = False
        T = current.T
        t_ = lambda v: none if v is None else v if type(v) is lazyT else T(v)

        if self.slabels:
            # String Template or lazyT
            try:
                row_dict = row.as_dict()
            except AttributeError:
                # Row just a dict/Storage after all? (e.g. custom lookup)
                row_dict = row

            # Represent None as self.none
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
                    values = [t_(v) for v in values]
                    translated = True
                sep = self.field_sep
                v = sep.join(s3_str(value) for value in values)
            elif values:
                v = s3_str(values[0])
            else:
                v = none

        if not translated and self.translate:
            output = t_(v)
        else:
            output = v

        # Color-coded representation
        color = self.color
        if color and color in row and row[color] is not None:
            bg = row[color]
            # Choose contrasting text color
            fg = "fefefe" if luminance(bg) < 140 else "444"
            style = "background-color:#%s;color:#%s" % (bg, fg)
            output = DIV(output, _class="prio", _style=style)

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

            Args:
                k: the key
                v: the representation of the key
                row: the row with this key (unused in the base class)
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

            Args:
                value: the value
                row: the referenced row (if value is a foreign key)
                show_link: render the representation as link
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

            Args:
                values: list of values
                rows: the referenced rows (if values are foreign keys)
                show_link: render each representation as link
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
            except TypeError as e:
                raise ValueError("List of lists expected, got %s" % values) from e
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

            Args:
                values: list of values
                rows: the rows
                show_link: render each representation as link

            Returns:
                a dict {value: representation}

            Note:
                For list-types, the dict keys will be the individual
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
            except TypeError as e:
                raise ValueError("List of lists expected, got %s" % values) from e
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

            Args:
                value: the list
                labels: the labels as returned from bulk()
                show_link: render references as links, should be the same as
                           used with bulk()
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
                self.theset = {opt: T(label) if isinstance(label, str) else label
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
        self.slabels = isinstance(labels, (str, lazyT))
        # External renderer?
        self.clabels = callable(labels)

        # Hierarchy template
        if isinstance(self.hierarchy, str):
            self.htemplate = self.hierarchy
        else:
            self.htemplate = "%s > %s"

        self.setup = True

    # -------------------------------------------------------------------------
    def _lookup(self, values, rows=None):
        """
            Lazy lookup values.

            Args:
                values: list of values to lookup
                rows: rows referenced by values (if values are foreign keys)
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
            if v is not None and table and isinstance(v, str):
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
            from ..tools import S3Hierarchy
            h = S3Hierarchy(table._tablename)
            if h.config:
                def lookup_parent(node_id):
                    parent = h.parent(node_id)
                    if parent and \
                       parent not in theset and \
                       parent not in lookup:
                        lookup[parent] = False
                        lookup_parent(parent)
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

            Args:
                value: the value
                row: the row containing the value
                rows: all rows from _loopup as dict
                hierarchy: the S3Hierarchy instance
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

        result = self.represent_row(row)
        if prefix:
            result = self.htemplate % (prefix, result)

        theset[value] = result
        return result

# =============================================================================
class S3RepresentLazy:
    """
        Lazy Representation of a field value, utilizes the bulk-feature
        of S3Represent-style representation methods
    """

    def __init__(self, value, renderer):
        """
            Args:
                value: the value
                renderer: the renderer (S3Represent instance)
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

            Args:
                element: the element
                attributes: the attributes dict of the element
                name: the attribute name
        """

        # Render value
        text = s3_str(self.represent())

        # Strip markup + XML-escape
        if text and "<" in text:
            try:
                stripper = MarkupStripper()
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

# =============================================================================
class S3PriorityRepresent:
    """
        Color-coded representation of priorities
    """

    def __init__(self, options, classes=None, none=None):
        """
            Args:
                options: the options (as dict or anything that can be
                         converted into a dict)
                classes: a dict mapping keys to CSS class suffixes
                none: treat None-values as this value
        """

        self.options = dict(options)
        self.classes = classes
        self.none = none

    # -------------------------------------------------------------------------
    def __call__(self, value, row=None):
        """
            Representation function

            Args:
                value: the value to represent
                row: the Row (unused, for API compatibility)
        """

        css_class = base_class = "prio"

        if value is None and self.none:
            value = self.none

        classes = self.classes
        if classes:
            suffix = classes.get(value)
            if suffix:
                css_class = "%s %s-%s" % (css_class, base_class, suffix)

        label = self.options.get(value)

        return DIV(label, _class=css_class)

    # -------------------------------------------------------------------------
    def represent(self, value, row=None):
        """
            Wrapper for self.__call__, for backwards-compatibility
        """

        return self(value, row=row)

# =============================================================================
class BooleanRepresent:
    """
        Visually enhanced representation of boolean values
    """

    RED = "bool-red"
    GREEN = "bool-green"
    BLUE = "bool-blue"
    GREY = "bool-grey"

    POS = "fa fa-check"
    NEG = "fa fa-remove"

    CSS = "bool"

    # -------------------------------------------------------------------------
    def __init__(self, labels=True, icons=False, colors=False, flag=None):
        """
            Args:
                labels: show labels for values
                        - True:                        use default Yes|No labels
                        - tuple (yes_label, no_label): use alternative labels
                        - False:                       hide labels
                icons: show icons for values
                        - True:                        use default icons
                        - tuple (yes_css, no_css)      use alternative CSS classes for icons
                        - False:                       hide icons
                colors: use colors for representation
                        - True:                        use default red|green colors
                        - tuple (yes_css, no_css)      use alternative CSS classes for color
                        - False:                       no colors
                flag: show only positive|negative values
                        - True:                        hide if False (positive flag)
                        - False:                       hide if True (negative flag)
                        - None:                        show both
        """

        self.labels = bool(labels)
        if isinstance(labels, tuple):
            self.yes, self.no = labels
        elif labels:
            T = current.T
            self.yes, self.no = T("Yes"), T("No")
        else:
            self.yes, self.no = "", ""

        if isinstance(icons, tuple):
            self.icons = icons
        elif icons:
            self.icons = (self.POS, self.NEG)
        else:
            self.icons = None

        if isinstance(colors, tuple):
            self.colors = colors
        elif colors:
            self.colors = (self.GREEN, self.RED)
        else:
            self.colors = None

        self.flag = flag

        self._pos = None
        self._neg = None

    # -------------------------------------------------------------------------
    @property
    def pos(self):
        """
            Representation of positive (True) value
        """

        v = self._pos
        if v is None:
            if self.flag is False:
                v = "-"
            else:
                v = self.yes
                icons, colors = self.icons, self.colors
                if icons or colors:
                    v = SPAN(v, _class=self.CSS) if v else SPAN(_class=self.CSS)
                    v.add_class(self.CSS)
                    if icons and icons[0]:
                        v.insert(0, I(_class=icons[0]))
                    if colors and colors[0]:
                        v.add_class(colors[0])
            self._pos = v
        return v

    # -------------------------------------------------------------------------
    @property
    def neg(self):
        """
            Representation of negative (False) values
        """

        v = self._neg
        if v is None:
            if self.flag is True:
                v = "-"
            else:
                v = self.no
                icons, colors = self.icons, self.colors
                if icons or colors:
                    v = SPAN(v, _class=self.CSS) if v else SPAN(_class=self.CSS)
                    if icons and icons[1]:
                        v.insert(0, I(_class=icons[1]))
                    if colors and colors[1]:
                        v.add_class(colors[1])
            self._neg = v
        return v

    # -------------------------------------------------------------------------
    def __call__(self, value, row=None):
        """
            Value representation applying configured options

            Args:
                value: the value
                row: the Row (unused)

            Returns:
                the represented value
        """

        return self.pos if value else self.neg

    # -------------------------------------------------------------------------
    @staticmethod
    def yesno(value, row=None):
        """
            Classic yes|no text representation of boolean values

            Args:
                value: the value
                row: the Row (unused)

            Returns:
                the represented value
        """

        if value is True:
            return current.T("Yes")
        elif value is False:
            return current.T("No")
        else:
            return "-"

# =============================================================================
class XMLContentsRepresent:
    """
        Renderer for db-stored XML contents (e.g. CMS)

        Replaces {{page}} expressions inside the contents with local URLs.

        {{page}}                 - gives the URL of the current page
        {{name:example}}         - gives the URL of the current page with
                                   a query ?name=example (can add any number
                                   of query variables)
        {{c:org,f:organisation}} - c and f tokens override controller and
                                   function of the current page, in this
                                   example like /org/organisation
        {{args:arg,arg}}         - override the current request's URL args
                                   (this should come last in the expression)
        {{noargs}}               - strip all URL args

        NB does not check permissions for the result URLs
    """

    def __init__(self, contents):
        """
            Args:
                contents: the contents (string)
        """

        self.contents = contents

    # -------------------------------------------------------------------------
    @staticmethod
    def link(match):
        """
            Replace {{}} expressions with local URLs, with the ability to
            override controller, function and URL query variables.Called
            from re.sub.

            Args:
                match: the re match object
        """

        # Parse the expression
        tokens = match.group(1).split(",")

        args = True
        parameters = {}
        arguments = []
        collect_args = False
        for token in tokens:
            if not token:
                continue
            if ":" in token:
                collect_args = False
                key, value = token.split(":")
            else:
                key, value = token, None
            key = key.strip()
            if not value:
                if key == "noargs":
                    args = False
                elif collect_args:
                    arguments.append(key)
            elif key == "args":
                arguments.append(value.strip())
                collect_args = True
            else:
                parameters[key] = value.strip()

        # Construct the URL
        request = current.request
        c = parameters.pop("c", request.controller)
        f = parameters.pop("f", request.function)
        if not arguments:
            arguments = request.args
        args = arguments if args else []
        return URL(c=c, f=f, args=args, vars=parameters, host=True)

    # -------------------------------------------------------------------------
    def xml(self):
        """ Render the output """

        return re.sub(r"\{\{(.+?)\}\}", self.link, self.contents)

# =============================================================================
# Uploaded file representation
#
FILE_ICONS = {".pdf": "file-pdf",
              ".xls": "file-xls",
              ".xlsx": "file-xls",
              ".doc": "file-doc",
              ".docx": "file-doc",
              ".odt": "file-text",
              ".txt": "file-text",
              ".png": "file-image",
              ".jpg": "file-image",
              ".jpeg": "file-image",
              ".bmp": "file-image",
              }

def represent_file(tablename="doc_document", fieldname="file"):

    def represent(value, row=None):
        """
            Represent an upload-field (file) as icon+size

            Args:
                value: the uploaded file name
                row: unused, for API compatibility

            Returns:
                representation (DIV-type)
        """

        if not value:
            return current.messages["NONE"]

        try:
            # Check whether file exists and extract the original
            # file name from the stored file name
            name, f = current.s3db[tablename][fieldname].retrieve(value)
        except IOError:
            return current.T("File not found")

        # Get the file extension and generate corresponding icon
        ext = os.path.splitext(name)[1].lower()
        icon_type = FILE_ICONS.get(ext)
        if not icon_type:
            icon_type = "file-generic"

        from ..ui import ICON
        icon = ICON(icon_type)

        output = A(icon,
                   _href = URL(c = "default",
                               f = "download",
                               args = [value],
                               vars = {"otn": tablename},
                               ),
                   _title = name,
                   _class = "file-repr",
                   )

        # Determine the file size
        fsize = f.seek(0, 2) if f else None
        if fsize is not None:
            for u in ("B", "kB", "MB", "GB"):
                unit = u
                if fsize < 1024:
                    break
                fsize /= 1024
            fsize = "%s %s" % (round(fsize), unit)
            output.append(SPAN(fsize, _class="file-size"))

        return output

    return represent

# -----------------------------------------------------------------------------
def represent_image(tablename="doc_image", fieldname="file"):

    def represent(value, row=None):
        """
            Represent an image as a clickable thumbnail

            Args:
                value: name of the image file
                row: unused, for API compatibility

            Returns:
                representation (DIV-type)
        """

        if not value:
            return current.messages["NONE"]

        link = URL(c = "default",
                   f = "download",
                   args = value,
                   vars = {"otn": tablename},
                   )

        return DIV(A(IMG(_src = link,
                         _class = "img-preview",
                         ),
                     _class = "zoom",
                     _href = link,
                     ),
                   )

    return represent

# =============================================================================
def represent_option(options, default="-"):
    """
        Representation function for option dicts

        Args:
            options: the options dict
            default: the default value for unknown options

        Returns:
            function: the representation function
    """

    def represent(value, row=None):
        return options.get(value, default)
    return represent

# =============================================================================
def represent_hours(colon=False):
    """
        Representation function for hours (duration), adding an
        onhover-hint with alternative formatting (0h 0min, or 0:00)

        Args:
            colon: use colon-notation 0:00 for hint

        Returns:
            function: the representation function
    """

    def represent(value, row=None):

        if value is None:
            return ""
        try:
            value = float(value)
        except (ValueError, TypeError):
            value = 0

        hours = int(value)
        minutes = round((value - hours) * 60)

        if colon:
            title = "%d:%02d" % (hours, minutes)
        else:
            formatted = []
            if hours:
                formatted.append("%dh" % hours)
            if minutes:
                formatted.append("%dmin" % minutes)
            title = " ".join(formatted) if formatted else None

        return SPAN("%s" % round(value, 2), _title=title, _class="hours-formatted")

    return represent

# -------------------------------------------------------------------------
def represent_normal(minimum=None, maximum=None):
    """
        Representation of a numerical value with highlighting values
        outside of a given range

        Args:
            minimum: the lower end of the normal range
            maximum: the upper end of the normal range

        Returns:
            SPAN, with CSS class "out-of-range" for abnormal values
    """

    def represent(value, row=None):

        if value is None:
            output = "-"
        elif (minimum is None or minimum <= value) and \
             (maximum is None or value <= maximum):
            output = SPAN(s3_str(value))
        else:
            output = SPAN(s3_str(value), _class="out-of-range")
        return output

    return represent

# -------------------------------------------------------------------------
def represent_occupancy(value, row=None):
    """
        Representation of utilization/occupancy rate as decision aid
        in progress-bar style

        Args:
            value: the utilization/occupancy in % (integer > 0)

        Returns:
            stylable DIV
    """


    if value is None:
        return DIV("?", _class="occupancy-bar")

    elif not value:
        value = 0
        css_class = "occupancy-0"

    else:
        reprval = (value - 1) // 10 * 10 + 10
        if reprval > 100:
            css_class = "occupancy-exc"
        else:
            css_class = "occupancy-%s" % reprval

    return DIV("%s%%" % value,
               DIV(_class="occupancy %s" % css_class),
               _class="occupancy-bar",
               )

# =============================================================================
def s3_comments_represent(text, show_link=True):
    """
        Represent Comments Fields
    """

    # Make sure text is multi-byte-aware before truncating it
    text = s3_str(text)
    if len(text) < 80:
        return text
    elif not show_link:
        return "%s..." % text[:76]
    else:
        import uuid
        unique =  uuid.uuid4()
        represent = DIV(
                DIV(text,
                    _id=unique,
                    _class="hide showall",
                    _onmouseout="$('#%s').hide()" % unique
                   ),
                A("%s..." % text[:76],
                  _onmouseover="$('#%s').removeClass('hide').show()" % unique,
                 ),
                )
        return represent

# =============================================================================
def s3_phone_represent(value):
    """
        Ensure that Phone numbers always show as LTR
        - otherwise + appears at the end which looks wrong even in RTL
    """

    if not value:
        return current.messages["NONE"]
    return s3_str("%s%s" % (chr(8206), s3_str(value)))

# =============================================================================
def s3_url_represent(url):
    """
        Make URLs clickable
    """

    if not url:
        return ""

    url_, error = IS_URL(allowed_schemes = ["http", "https", None],
                         prepend_scheme = "http",
                         )(url)
    if error:
        return url
    return A(url_, _href=url_, _target="_blank")

# =============================================================================
def s3_qrcode_represent(value, row=None, show_value=True):
    """
        Simple QR Code representer, produces a DIV with embedded SVG,
        useful to embed QR Codes that are to be scanned directly from
        the screen, or for previews
            - requires python-qrcode (pip install qrcode), and PIL

        Args:
            value: the value to render (will be converted to str)
            row: the Row (unused, for API-compatibility)
            show_value: include the value (as str) in the representation

        Returns:
            a DIV containing the QR code (SVG)
    """

    try:
        import qrcode
        import qrcode.image.svg
    except ImportError:
        return s3_str(value)

    # Generate the QR Code
    qr = qrcode.QRCode(version = 2,
                       # L-level good enough for displaying on screen, as
                       # it would rarely be damaged or dirty there ;)
                       error_correction = qrcode.constants.ERROR_CORRECT_L,
                       box_size = 10,
                       border = 2,
                       image_factory=qrcode.image.svg.SvgPathImage,
                       )
    qr.add_data(s3_str(value))
    qr.make(fit=True)

    # Generate SVG
    qr_svg = qr.make_image(fill_color="black", back_color="white")

    # # Write the SVG into a buffer
    # from io import BytesIO
    # stream = BytesIO()
    # qr_svg.save(stream)

    # # Generate XML string to embed
    # stream.seek(0)
    # svgxml = XML(stream.read())

    # Convert to byte-string
    svgxml = qr_svg.to_string(encoding="utf-8")

    output = DIV(DIV(XML(svgxml),
                     _class = "s3-qrcode-svg",
                     ),
                 _class = "s3-qrcode-display",
                 )
    if show_value:
        output.append(DIV(s3_str(value), _class="s3-qrcode-val"))

    return output

# =============================================================================
def s3_URLise(text):
    """
        Convert all URLs in a text into an HTML <A> tag.

        Args:
            text: the text
    """

    output = URLSCHEMA.sub(lambda m: '<a href="%s" target="_blank">%s</a>' %
                          (m.group(0), m.group(0)), text)
    return output

# =============================================================================
def s3_avatar_represent(user_id, tablename="auth_user", gravatar=False, **attr):
    """
        Represent a User as their profile picture or Gravatar

        Args:
            tablename: either "auth_user" or "pr_person" depending on which
                       table the 'user_id' refers to
            attr: additional HTML attributes for the IMG(), such as _class
    """

    size = (50, 50)

    if user_id:
        db = current.db
        s3db = current.s3db
        cache = s3db.cache

        table = s3db[tablename]

        email = None
        image = None

        if tablename == "auth_user":
            user = db(table.id == user_id).select(table.email,
                                                  cache = cache,
                                                  limitby = (0, 1),
                                                  ).first()
            if user:
                email = user.email.strip().lower()
            ltable = s3db.pr_person_user
            itable = s3db.pr_image
            query = (ltable.user_id == user_id) & \
                    (ltable.pe_id == itable.pe_id) & \
                    (itable.profile == True)
            image = db(query).select(itable.image,
                                     limitby = (0, 1),
                                     ).first()
            if image:
                image = image.image
        elif tablename == "pr_person":
            user = db(table.id == user_id).select(table.pe_id,
                                                  cache = cache,
                                                  limitby = (0, 1),
                                                  ).first()
            if user:
                ctable = s3db.pr_contact
                query = (ctable.pe_id == user.pe_id) & \
                        (ctable.contact_method == "EMAIL")
                email = db(query).select(ctable.value,
                                         cache = cache,
                                         limitby = (0, 1),
                                         ).first()
                if email:
                    email = email.value
                itable = s3db.pr_image
                query = (itable.pe_id == user.pe_id) & \
                        (itable.profile == True)
                image = db(query).select(itable.image,
                                         limitby = (0, 1),
                                         ).first()
                if image:
                    image = image.image

        if image:
            image = s3db.pr_image_library_represent(image, size=size)
            size = s3db.pr_image_size(image, size)
            url = URL(c="default", f="download",
                      args=image)
        elif gravatar:
            if email:
                # If no Image uploaded, try Gravatar, which also provides a nice fallback identicon
                import hashlib
                email_hash = hashlib.md5(email).hexdigest()
                url = "//www.gravatar.com/avatar/%s?s=50&d=identicon" % email_hash
            else:
                url = "//www.gravatar.com/avatar/00000000000000000000000000000000?d=mm"
        else:
            url = URL(c="static", f="img", args="blank-user.gif")
    else:
        url = URL(c="static", f="img", args="blank-user.gif")

    if "_class" not in attr:
        attr["_class"] = "avatar"
    if "_width" not in attr:
        attr["_width"] = size[0]
    if "_height" not in attr:
        attr["_height"] = size[1]
    return IMG(_src=url, **attr)

# =============================================================================
def s3_yes_no_represent(value):
    " Represent a Boolean field as Yes/No instead of True/False "

    if value is True:
        return current.T("Yes")
    elif value is False:
        return current.T("No")
    else:
        return current.messages["NONE"]

# =============================================================================
def s3_truncate(text, length=48, nice=True):
    """
        Nice truncating of text

        Args:
            text: the text
            length: the maximum length
            nice: do not truncate words
    """


    if len(text) > length:
        if type(text) is str:
            encode = False
        else:
            # Make sure text is multi-byte-aware before truncating it
            text = s3_str(text)
            encode = True
        if nice:
            truncated = "%s..." % text[:length].rsplit(" ", 1)[0][:length-3]
        else:
            truncated = "%s..." % text[:length-3]
        if encode:
            truncated = s3_str(truncated)
        return truncated
    else:
        return text

# =============================================================================
def s3_datatable_truncate(string, maxlength=40):
    """
        Representation method to override the dataTables-internal truncation
        of strings per field, like:

        Example:
            table.field.represent = lambda v, row=None: \
                                    s3_datatable_truncate(v, maxlength=40)

        Args:
            string: the string
            maxlength: the maximum string length

        Note:
            The JS click-event will be attached by s3.ui.datatable.js
    """

    # Make sure text is multi-byte-aware before truncating it
    string = s3_str(string)
    if string and len(string) > maxlength:
        _class = "dt-truncate"
        return TAG[""](
                DIV(SPAN(_class="ui-icon ui-icon-zoomin",
                         _style="float:right",
                         ),
                    string[:maxlength-3] + "...",
                    _class=_class),
                DIV(SPAN(_class="ui-icon ui-icon-zoomout",
                            _style="float:right"),
                    string,
                    _style="display:none",
                    _class=_class),
                )
    else:
        return string if string else ""

# =============================================================================
def s3_trunk8(selector=None, lines=None, less=None, more=None):
    """
        Intelligent client-side text truncation

        Args:
            selector: the jQuery selector (default: .s3-truncate)
            lines: maximum number of lines (default: 1)
    """

    T = current.T

    s3 = current.response.s3

    scripts = s3.scripts
    jquery_ready = s3.jquery_ready

    if s3.debug:
        script = "/%s/static/scripts/trunk8.js" % current.request.application
    else:
        script = "/%s/static/scripts/trunk8.min.js" % current.request.application

    if script not in scripts:

        scripts.append(script)

        # Toggle-script
        # - only required once per page
        script = \
"""$(document).on('click','.s3-truncate-more',function(event){
$(this).parent().trunk8('revert').append(' <a class="s3-truncate-less" href="#">%(less)s</a>')
return false})
$(document).on('click','.s3-truncate-less',function(event){
$(this).parent().trunk8()
return false})""" % {"less": T("less") if less is None else less}
        s3.jquery_ready.append(script)

    # Init-script
    # - required separately for each selector (but do not repeat the
    #   same statement if called multiple times => makes the page very
    #   slow)
    script = """S3.trunk8('%(selector)s',%(lines)s,'%(more)s')""" % \
             {"selector": ".s3-truncate" if selector is None else selector,
              "lines": "null" if lines is None else lines,
              "more": T("more") if more is None else more,
              }

    if script not in jquery_ready:
        jquery_ready.append(script)

# =============================================================================
def s3_text_represent(text, truncate=True, lines=5, _class=None):
    """
        Representation function for text fields with intelligent
        truncation and preserving whitespace.

        Args:
            text: the text
            truncate: whether to truncate or not
            lines: maximum number of lines to show
            _class: CSS class to use for truncation (otherwise using the
                    text-body class itself)
    """

    if not text:
        text = current.messages["NONE"]
    if _class is None:
        selector = ".text-body"
        _class = "text-body"
    else:
        selector = ".%s" % _class
        _class = "text-body %s" % _class

    if truncate and \
       current.auth.permission.format in ("html", "popup", "iframe"):
        s3_trunk8(selector = selector, lines = lines)

    return DIV(text, _class=_class)

# =============================================================================
def s3_format_fullname(fname=None, mname=None, lname=None, truncate=True):
    """
        Formats the full name of a person

        Args:
            fname: the person's pr_person.first_name value
            mname: the person's pr_person.middle_name value
            lname: the person's pr_person.last_name value
            truncate: truncate the name to max 24 characters
    """

    name = ""
    if fname or mname or lname:
        if not fname:
            fname = ""
        if not mname:
            mname = ""
        if not lname:
            lname = ""
        if truncate:
            fname = "%s" % s3_truncate(fname, 24)
            mname = "%s" % s3_truncate(mname, 24)
            lname = "%s" % s3_truncate(lname, 24, nice=False)
        name_format = current.deployment_settings.get_pr_name_format()
        name = name_format % {"first_name": fname,
                              "middle_name": mname,
                              "last_name": lname,
                              }
        name = name.replace("  ", " ").rstrip()
        if truncate:
            name = s3_truncate(name, 24, nice=False)
    return name

# =============================================================================
def s3_fullname(person=None, pe_id=None, truncate=True):
    """
        Returns the full name of a person

        Args:
            person: the pr_person record or record_id
            pe_id: alternatively, the person entity ID
            truncate: truncate the name to max 24 characters
    """

    record = None
    query = None

    if isinstance(person, int) or str(person).isdigit():
        db = current.db
        ptable = db.pr_person
        query = (ptable.id == person)
    elif person is not None:
        record = person
    elif pe_id is not None:
        db = current.db
        ptable = db.pr_person
        query = (ptable.pe_id == pe_id)

    if not record and query is not None:
        record = db(query).select(ptable.first_name,
                                  ptable.middle_name,
                                  ptable.last_name,
                                  limitby = (0, 1)
                                  ).first()
    if record:
        fname, mname, lname = "", "", ""
        if "pr_person" in record:
            # Check if this is a LazySet from db.auth_user
            #test = record["pr_person"]
            #from pydal.objects import LazySet
            #if not isinstance(test, LazySet)
            #    record = test
            record = record["pr_person"]
        if record.first_name:
            fname = record.first_name.strip()
        if "middle_name" in record and record.middle_name:
            mname = record.middle_name.strip()
        if record.last_name:
            lname = record.last_name.strip()
        return s3_format_fullname(fname, mname, lname, truncate)

    else:
        return ""

# =============================================================================
def s3_fullname_bulk(record_ids=None, truncate=True):
    """
        Returns the full name for a set of Persons
            - currently unused

        Args:
            record_ids: a list of record_ids
            truncate: truncate the name to max 24 characters
    """

    represents = {}

    if record_ids:

        db = current.db
        ptable = db.pr_person
        query = (ptable.id.belongs(record_ids))
        rows = db(query).select(ptable.id,
                                ptable.first_name,
                                ptable.middle_name,
                                ptable.last_name,
                                )

        for row in rows:
            fname, mname, lname = "", "", ""
            if row.first_name:
                fname = row.first_name.strip()
            if row.middle_name:
                mname = row.middle_name.strip()
            if row.last_name:
                lname = row.last_name.strip()
            represent = s3_format_fullname(fname, mname, lname, truncate)
            represents[row.id] = represent

    return represents

# END =========================================================================
