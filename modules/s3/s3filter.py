# -*- coding: utf-8 -*-

""" Framework for filtered REST requests

    @copyright: 2013-14 (c) Sahana Software Foundation
    @license: MIT

    @requires: U{B{I{gluon}} <http://web2py.com>}

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

__all__ = ("S3DateFilter",
           "S3Filter",
           "S3FilterForm",
           "S3FilterString",
           "S3FilterWidget",
           "S3HierarchyFilter",
           "S3LocationFilter",
           "S3OptionsFilter",
           "S3RangeFilter",
           "S3SliderFilter",
           "S3TextFilter",
           "get_s3_filter_opts",
           )

import datetime
import re

try:
    import json # try stdlib (Python 2.6)
except ImportError:
    try:
        import simplejson as json # try external module
    except:
        import gluon.contrib.simplejson as json # fallback to pure-Python module

try:
    # Python 2.7
    from collections import OrderedDict
except:
    # Python 2.6
    from gluon.contrib.simplejson.ordered_dict import OrderedDict

from gluon import *
from gluon.storage import Storage
from gluon.tools import callback

from s3rest import S3Method
from s3query import S3ResourceField, S3ResourceQuery, S3URLQuery
from s3utils import s3_get_foreign_key, s3_unicode, S3TypeConverter
from s3validators import *
from s3widgets import ICON, S3DateWidget, S3DateTimeWidget, S3GroupedOptionsWidget, S3MultiSelectWidget, S3HierarchyWidget

# Compact JSON encoding
SEPARATORS = (",", ":")

# =============================================================================
def get_s3_filter_opts(tablename,
                       fieldname = "name",
                       location_filter = False,
                       org_filter = False,
                       none = False,
                       translate = False,
                       ):
    """
        Lazy options getter
        - this is useful when the expected number of options is significantly smaller than the number of records to iterate through
            NB This reason is no longer required with S3Filter, but is a legacy from S3Search: S3Filter already does an efficient Reverse-Query
            @ToDo: Deprecate
        - note this doesn't check if options are actually in-use

        @param tablename: the name of the lookup table
        @param fieldname: the name of the field to represent options with
        @param location_filter: whether to filter the values by location
        @param org_filter: whether to filter the values by root_org
        @param none: whether to include an option for None
        @param translate: whether to translate the values
    """

    auth = current.auth
    table = current.s3db.table(tablename)
    if auth.s3_has_permission("read", table):
        query = auth.s3_accessible_query("read", table)
        if location_filter:
            location = current.session.s3.location_filter
            if location:
                query &= (table.location_id == location)
        if org_filter:
            root_org = auth.root_org()
            if root_org:
                query &= ((table.organisation_id == root_org) | \
                          (table.organisation_id == None))
            #else:
            #    query &= (table.organisation_id == None)
        rows = current.db(query).select(table.id,
                                        table[fieldname],
                                        # Options are sorted later
                                        #orderby = table[fieldname]
                                        )
        if translate:
            T = current.T
            opts = dict((row.id, T(row[fieldname])) for row in rows)
        else:
            opts = dict((row.id, row[fieldname]) for row in rows)
        if none:
            opts[None] = current.messages["NONE"]
    else:
        opts = {}
    return opts

# =============================================================================
class S3FilterWidget(object):
    """ Filter widget for interactive search forms (base class) """

    #: the HTML class for the widget type
    _class = "generic-filter"

    #: the default query operator(s) for the widget type
    operator = None

    #: alternatives for client-side changeable operators
    alternatives = None

    # -------------------------------------------------------------------------
    def widget(self, resource, values):
        """
            Prototype method to render this widget as an instance of
            a web2py HTML helper class, to be implemented by subclasses.

            @param resource: the S3Resource to render with widget for
            @param values: the values for this widget from the URL query
        """

        raise NotImplementedError

    # -------------------------------------------------------------------------
    def variable(self, resource, get_vars=None):
        """
            Prototype method to generate the name for the URL query variable
            for this widget, can be overwritten in subclasses.

            @param resource: the resource
            @return: the URL query variable name (or list of
                     variable names if there are multiple operators)
        """

        label, self.selector = self._selector(resource, self.field)

        if not self.selector:
            return None

        if self.alternatives and get_vars is not None:
            # Get the actual operator from get_vars
            operator = self._operator(get_vars, self.selector)
            if operator:
                self.operator = operator

        if "label" not in self.opts:
            self.opts["label"] = label

        return self._variable(self.selector, self.operator)

    # -------------------------------------------------------------------------
    def data_element(self, variable):
        """
            Prototype method to construct the hidden element that holds the
            URL query term corresponding to an input element in the widget.

            @param variable: the URL query variable
        """

        if type(variable) is list:
            variable = "&".join(variable)
        return INPUT(_type="hidden",
                     _id="%s-data" % self.attr["_id"],
                     _class="filter-widget-data %s-data" % self._class,
                     _value=variable)

    # -------------------------------------------------------------------------
    # Helper methods
    #
    def __init__(self, field=None, **attr):
        """
            Constructor to configure the widget

            @param field: the selector(s) for the field(s) to filter by
            @param attr: configuration options for this widget

            Configuration options:
            @keyword label: label for the widget
            @keyword comment: comment for the widget
            @keyword hidden: render widget initially hidden (="advanced"
                             option)
            @keyword levels: list of location hierarchy levels
                             (L{S3LocationFilter})
            @keyword widget: widget to use (L{S3OptionsFilter}),
                             "select", "multiselect" (default),
                             or "groupedopts"
            @keyword cols: number of columns of checkboxes (L{S3OptionsFilter}
                           and L{S3LocationFilter} with "groupedopts" widget)
            @keyword filter: show filter for options (L{S3OptionsFilter},
                             L{S3LocationFilter} with "multiselect" widget)
            @keyword header: show header in widget (L{S3OptionsFilter},
                             L{S3LocationFilter} with "multiselect" widget)
            @keyword selectedList: number of selected items to show before
                                   collapsing into number of items
                                   (L{S3OptionsFilter}, L{S3LocationFilter}
                                   with "multiselect" widget)
            @keyword no_opts: text to show if no options available
                              (L{S3OptionsFilter}, L{S3LocationFilter})
            @keyword resource: alternative resource to look up options
                               (L{S3LocationFilter}, L{S3OptionsFilter})
            @keyword lookup: field in the alternative resource to look up
                             options (L{S3LocationFilter})
            @keyword options: fixed set of options (L{S3OptionsFilter}: dict
                              of {value: label} or a callable that returns one,
                              L{S3LocationFilter}: list of gis_location IDs)
            @keyword size: maximum size of multi-letter options groups
                           (L{S3OptionsFilter} with "groupedopts" widget)
            @keyword help_field: field in the referenced table to display on
                                 hovering over a foreign key option
                                 (L{S3OptionsFilter} with "groupedopts" widget)
            @keyword none: label for explicit None-option in many-to-many
                           fields (L{S3OptionsFilter})
            @keyword fieldtype: explicit field type "date" or "datetime" to
                                use for context or virtual fields
                                (L{S3DateFilter})
            @keyword hide_time: don't show time selector (L{S3DateFilter})
        """

        self.field = field
        self.alias = None

        attributes = Storage()
        options = Storage()
        for k, v in attr.iteritems():
            if k[0] == "_":
                attributes[k] = v
            else:
                options[k] = v
        self.attr = attributes
        self.opts = options

        self.selector = None
        self.values = Storage()

    # -------------------------------------------------------------------------
    def __call__(self, resource, get_vars=None, alias=None):
        """
            Entry point for the form builder

            @param resource: the S3Resource to render the widget for
            @param get_vars: the GET vars (URL query vars) to prepopulate
                             the widget
            @param alias: the resource alias to use
        """

        self.alias = alias

        # Initialize the widget attributes
        self._attr(resource)

        # Extract the URL values to populate the widget
        variable = self.variable(resource, get_vars)
        if type(variable) is list:
            values = Storage()
            for k in variable:
                if k in self.values:
                    values[k] = self.values[k]
                else:
                    values[k] = self._values(get_vars, k)
        else:
            if variable in self.values:
                values = self.values[variable]
            else:
                values = self._values(get_vars, variable)

        # Construct and populate the widget
        widget = self.widget(resource, values)

        # Recompute variable in case operator got changed in widget()
        if self.alternatives:
            variable = self._variable(self.selector, self.operator)

        # Construct the hidden data element
        data = self.data_element(variable)

        if type(data) is list:
            data.append(widget)
        else:
            data = [data, widget]
        return TAG[""](*data)

    # -------------------------------------------------------------------------
    def _attr(self, resource):
        """ Initialize and return the HTML attributes for this widget """

        _class = self._class

        # Construct name and id for the widget
        attr = self.attr
        if "_name" not in attr:
            if not resource:
                raise SyntaxError("%s: _name parameter required " \
                                  "when rendered without resource." % \
                                  self.__class__.__name__)
            flist = self.field
            if type(flist) is not list:
                flist = [flist]
            colnames = []
            for f in flist:
                rfield = S3ResourceField(resource, f)
                colname = rfield.colname
                if colname:
                    colnames.append(colname)
                else:
                    colnames.append(rfield.fname)
            name = "%s-%s-%s" % (resource.alias, "-".join(colnames), _class)
            attr["_name"] = name.replace(".", "_")
        if "_id" not in attr:
            attr["_id"] = attr["_name"]

        return attr

    # -------------------------------------------------------------------------
    @classmethod
    def _operator(cls, get_vars, selector):
        """
            Helper method to get the operators from the URL query

            @param get_vars: the GET vars (a dict)
            @param selector: field selector

            @return: query operator - None, str or list
        """

        variables = ["%s__%s" % (selector, op) for op in cls.alternatives]
        slen = len(selector) + 2

        operators = [k[slen:] for k, v in get_vars.iteritems()
                                  if k in variables]
        if not operators:
            return None
        elif len(operators) == 1:
            return operators[0]
        else:
            return operators

    # -------------------------------------------------------------------------
    def _prefix(self, selector):
        """
            Helper method to prefix an unprefixed field selector

            @param alias: the resource alias to use as prefix
            @param selector: the field selector

            @return: the prefixed selector
        """

        alias = self.alias
        if alias is None:
            alias = "~"
        if "." not in selector.split("$", 1)[0]:
            return "%s.%s" % (alias, selector)
        else:
            return selector

    # -------------------------------------------------------------------------
    def _selector(self, resource, fields):
        """
            Helper method to generate a filter query selector for the
            given field(s) in the given resource.

            @param resource: the S3Resource
            @param fields: the field selectors (as strings)

            @return: the field label and the filter query selector, or None
                     if none of the field selectors could be resolved
        """

        prefix = self._prefix
        label = None

        if not fields:
            return label, None
        if not isinstance(fields, (list, tuple)):
            fields = [fields]
        selectors = []
        for field in fields:
            if resource:
                try:
                    rfield = S3ResourceField(resource, field)
                except (AttributeError, TypeError):
                    continue
                if not rfield.field and not rfield.virtual:
                    # Unresolvable selector
                    continue
                if not label:
                    label = rfield.label
                selectors.append(prefix(rfield.selector))
            else:
                selectors.append(field)
        if selectors:
            return label, "|".join(selectors)
        else:
            return label, None

    # -------------------------------------------------------------------------
    @staticmethod
    def _values(get_vars, variable):
        """
            Helper method to get all values of a URL query variable

            @param get_vars: the GET vars (a dict)
            @param variable: the name of the query variable

            @return: a list of values
        """

        if not variable:
            return []
        elif variable in get_vars:
            values = S3URLQuery.parse_value(get_vars[variable])
            if not isinstance(values, (list, tuple)):
                values = [values]
            return values
        else:
            return []

    # -------------------------------------------------------------------------
    @classmethod
    def _variable(cls, selector, operator):
        """
            Construct URL query variable(s) name from a filter query
            selector and the given operator(s)

            @param selector: the selector
            @param operator: the operator (or tuple/list of operators)

            @return: the URL query variable name (or list of variable names)
        """

        if isinstance(operator, (tuple, list)):
            return [cls._variable(selector, o) for o in operator]
        elif operator:
            return "%s__%s" % (selector, operator)
        else:
            return selector

# =============================================================================
class S3TextFilter(S3FilterWidget):
    """ Text filter widget """

    _class = "text-filter"

    operator = "like"

    # -------------------------------------------------------------------------
    def widget(self, resource, values):
        """
            Render this widget as HTML helper object(s)

            @param resource: the resource
            @param values: the search values from the URL query
        """

        attr = self.attr

        if "_size" not in attr:
            attr.update(_size="40")
        if "_class" in attr and attr["_class"]:
            _class = "%s %s" % (attr["_class"], self._class)
        else:
            _class = self._class
        attr["_class"] = _class
        attr["_type"] = "text"

        values = [v.strip("*") for v in values if v is not None]
        if values:
            attr["_value"] = " ".join(values)

        return INPUT(**attr)

# =============================================================================
class S3RangeFilter(S3FilterWidget):
    """ Numerical Range Filter Widget """

    # Overall class
    _class = "range-filter"
    # Class for visible input boxes.
    _input_class = "%s-%s" % (_class, "input")

    operator = ["ge", "le"]

    # Untranslated labels for individual input boxes.
    input_labels = {"ge": "Minimum", "le": "Maximum"}

    # -------------------------------------------------------------------------
    def data_element(self, variables):
        """
            Overrides S3FilterWidget.data_element(), constructs multiple
            hidden INPUTs (one per variable) with element IDs of the form
            <id>-<operator>-data (where no operator is translated as "eq").

            @param variables: the variables
        """

        if variables is None:
            operators = self.operator
            if type(operators) is not list:
                operators = [operators]
            variables = self._variable(self.selector, operators)
        else:

            # Split the operators off the ends of the variables.
            if type(variables) is not list:
                variables = [variables]
            operators = [v.split("__")[1]
                         if "__" in v else "eq"
                         for v in variables]

        elements = []
        id = self.attr["_id"]

        for o, v in zip(operators, variables):
            elements.append(
                INPUT(_type="hidden",
                      _id="%s-%s-data" % (id, o),
                      _class="filter-widget-data %s-data" % self._class,
                      _value=v))

        return elements

    # -------------------------------------------------------------------------
    def widget(self, resource, values):
        """
            Render this widget as HTML helper object(s)

            @param resource: the resource
            @param values: the search values from the URL query
        """

        attr = self.attr
        _class = self._class
        if "_class" in attr and attr["_class"]:
            _class = "%s %s" % (attr["_class"], _class)
        else:
            _class = _class
        attr["_class"] = _class

        input_class = self._input_class
        input_labels = self.input_labels
        input_elements = DIV()
        ie_append = input_elements.append

        _id = attr["_id"]
        _variable = self._variable
        selector = self.selector

        for operator in self.operator:

            input_id = "%s-%s" % (_id, operator)

            input_box = INPUT(_name=input_id,
                              _id=input_id,
                              _type="text",
                              _class=input_class)

            variable = _variable(selector, operator)

            # Populate with the value, if given
            # if user has not set any of the limits, we get [] in values.
            value = values.get(variable, None)
            if value not in [None, []]:
                if type(value) is list:
                    value = value[0]
                input_box["_value"] = value
                input_box["value"] = value

            ie_append(DIV(
                        DIV(LABEL(current.T(input_labels[operator] + ":"),
                                  _for=input_id),
                            _class="range-filter-label"),
                        DIV(input_box,
                            _class="range-filter-widget"),
                        _class="range-filter-field"))

        return input_elements

# =============================================================================
class S3DateFilter(S3RangeFilter):
    """
        Date Range Filter Widget
        @see: L{Configuration Options<S3FilterWidget.__init__>}
    """

    _class = "date-filter"

    # Class for visible input boxes.
    _input_class = "%s-%s" % (_class, "input")

    operator = ["ge", "le"]

    # Untranslated labels for individual input boxes.
    input_labels = {"ge": "From", "le": "To"}

    # -------------------------------------------------------------------------
    def widget(self, resource, values):
        """
            Render this widget as HTML helper object(s)

            @param resource: the resource
            @param values: the search values from the URL query
        """

        attr = self.attr

        # CSS class and element ID
        _class = self._class
        if "_class" in attr and attr["_class"]:
            _class = "%s %s" % (attr["_class"], _class)
        else:
            _class = _class
        _id = attr["_id"]

        # Determine the field type
        if resource:
            rfield = S3ResourceField(resource, self.field)
            field = rfield.field
        else:
            rfield = field = None
        if not field:
            if not rfield or rfield.virtual:
                ftype = self.opts.get("fieldtype", "datetime")
            else:
                # Unresolvable selector
                return ""
        else:
            ftype = rfield.ftype
        if not field:
            # S3DateTimeWidget requires a Field
            if rfield:
                tname, fname = rfield.tname, rfield.fname
            else:
                tname, fname = "notable", "datetime"
                if not _id:
                    raise SyntaxError("%s: _id parameter required " \
                                      "when rendered without resource." % \
                                      self.__class__.__name__)
            dtformat = current.deployment_settings.get_L10n_date_format()
            field = Field(fname, ftype,
                          requires = IS_DATE_IN_RANGE(format = dtformat))
            field.tablename = field._tablename = tname

        # Options
        hide_time = self.opts.get("hide_time", False)

        # Generate the input elements
        T = current.T
        selector = self.selector
        _variable = self._variable
        input_class = self._input_class
        input_labels = self.input_labels
        input_elements = DIV(_id=_id, _class=_class)
        append = input_elements.append
        for operator in self.operator:

            input_id = "%s-%s" % (_id, operator)

            # Determine the widget class
            if ftype == "date":
                widget = S3DateWidget()
            else:
                opts = {}
                if operator == "ge":
                    opts["set_min"] = "%s-%s" % (_id, "le")
                elif operator == "le":
                    opts["set_max"] = "%s-%s" % (_id, "ge")
                widget = S3DateTimeWidget(hide_time=hide_time, **opts)

            # Populate with the value, if given
            # if user has not set any of the limits, we get [] in values.
            variable = _variable(selector, operator)
            value = values.get(variable, None)
            if value not in [None, []]:
                if type(value) is list:
                    value = value[0]
            else:
                value = None

            # Render the widget
            picker = widget(field, value,
                            _name=input_id,
                            _id=input_id,
                            _class=input_class)

            # Append label and widget
            append(DIV(
                    DIV(LABEL("%s:" % T(input_labels[operator]),
                            _for=input_id),
                        _class="range-filter-label"),
                    DIV(picker,
                        _class="range-filter-widget"),
                    _class="range-filter-field"))

        return input_elements

# =============================================================================
class S3SliderFilter(S3RangeFilter):
    """
        Filter widget for Ranges which is controlled by a Slider instead of
        INPUTs
    """

    _class = "slider-filter"

    operator = ["ge", "le"]

    # -------------------------------------------------------------------------
    def widget(self, resource, values):
        """
            Render this widget as HTML helper object(s)

            @param resource: the resource
            @param values: the search values from the URL query
        """

        attr = self.attr

        # CSS class and element ID
        _class = self._class
        if "_class" in attr and attr["_class"]:
            _class = "%s %s" % (attr["_class"], _class)
        else:
            _class = _class
        attr["_class"] = _class
        _id = attr["_id"]

        # Determine the field type
        if resource:
            rfield = S3ResourceField(resource, self.field)
            field = rfield.field
        else:
            field = None
        if not field:
            # Unresolvable selector
            return ""

        # Options
        step = self.opts.get("step", 1)
        type = self.opts.get("type", "int")

        # Generate the input elements
        field = str(field)
        fieldname = field.replace(".", "_")
        selector = self.selector
        _variable = self._variable
        for operator in self.operator:
            input_id = "%s-%s" % (_id, operator)
            input = INPUT(_name = input_id,
                          _disabled = True,
                          _id = input_id,
                          _style = "border:0",
                          )
            # Populate with the value, if given
            # if user has not set any of the limits, we get [] in values.
            variable = _variable(selector, operator)
            value = values.get(variable, None)
            if value not in [None, []]:
                if type(value) is list:
                    value = value[0]
                input["_value"] = value
                input["value"] = value

        slider = DIV(_id="%s_slider" % fieldname, **attributes)

        s3 = current.response.s3

        validator = field.requires
        if isinstance(validator, IS_EMPTY_OR):
            validator = validator.other
        _min = validator.minimum
        # Max Value depends upon validator type
        if isinstance(validator, IS_INT_IN_RANGE):
            _max = validator.maximum - 1
        elif isinstance(validator, IS_FLOAT_IN_RANGE):
            _max = validator.maximum

        if values is None:
            # JSONify
            value = "null"
            script = '''i18n.slider_help="%s"''' % \
                current.T("Click on the slider to choose a value")
            s3.js_global.append(script)

        if _type == "int":
            script = '''S3.range_slider('%s',%i,%i,%i,%s)''' % (fieldname,
                                                                _min,
                                                                _max,
                                                                step,
                                                                values)
        else:
            # Float
            script = '''S3.range_slider('%s',%f,%f,%f,%s)''' % (fieldname,
                                                                _min,
                                                                _max,
                                                                step,
                                                                values)
        s3.jquery_ready.append(script)

        return TAG[""](input1, input2, slider)

# =============================================================================
class S3LocationFilter(S3FilterWidget):
    """
        Hierarchical Location Filter Widget
        @see: L{Configuration Options<S3FilterWidget.__init__>}

        NB This will show records linked to all child locations of the Lx
    """

    _class = "location-filter"

    operator = "belongs"

    # -------------------------------------------------------------------------
    def __init__(self, field=None, **attr):
        """
            Constructor to configure the widget

            @param field: the selector(s) for the field(s) to filter by
            @param attr: configuration options for this widget
        """

        if not field:
            field = "location_id"

        # Translate options using gis_location_name?
        settings = current.deployment_settings
        translate = settings.get_L10n_translate_gis_location()
        if translate:
            language = current.session.s3.language
            if language == settings.get_L10n_default_language():
                translate = False
        self.translate = translate

        super(S3LocationFilter, self).__init__(field=field, **attr)

    # -------------------------------------------------------------------------
    def widget(self, resource, values):
        """
            Render this widget as HTML helper object(s)

            @param resource: the resource
            @param values: the search values from the URL query
        """

        attr = self._attr(resource)
        opts = self.opts
        name = attr["_name"]

        ftype, levels, noopt = self._options(resource, values=values)
        if noopt:
            return SPAN(noopt, _class="no-options-available")

        # Filter class (default+custom)
        _class = self._class
        if "_class" in attr and attr["_class"]:
            _class = "%s %s" % (_class, attr["_class"])
        attr["_class"] = _class

        # Store id and name for the data element
        base_id = attr["_id"]
        base_name = attr["_name"]

        widgets = []
        w_append = widgets.append
        operator = self.operator
        field_name = self.field

        fname = self._prefix(field_name) if resource else field_name

        #widget_type = opts["widget"]
        # Use groupedopts widget if we specify cols, otherwise assume multiselect
        cols = opts.get("cols", None)
        if cols:
            # Grouped Checkboxes
            # @ToDo: somehow working, but ugly, not usable (deprecated?)
            if "groupedopts-filter-widget" not in _class:
                attr["_class"] = "%s groupedopts-filter-widget" % _class
            attr["cols"] = cols

            # Add one widget per level
            for level in levels:
                options = levels[level]["options"]
                groupedopts = S3GroupedOptionsWidget(cols = cols,
                                                     size = opts["size"] or 12,
                                                     )
                # Dummy field
                name = "%s-%s" % (base_name, level)
                dummy_field = Storage(name=name,
                                      type=ftype,
                                      requires=IS_IN_SET(options,
                                                         multiple=True))
                # Unique ID/name
                attr["_id"] = "%s-%s" % (base_id, level)
                attr["_name"] = name

                # Find relevant values to pre-populate
                _values = values.get("%s$%s__%s" % (fname, level, operator))
                w_append(groupedopts(dummy_field, _values, **attr))

        else:
            # Multiselect is default
            T = current.T

            # Multiselect Dropdown with Checkboxes
            if "multiselect-filter-widget" not in _class:
                _class = "%s multiselect-filter-widget" % _class

            # Add one widget per level
            first = True
            hide = True
            for level in levels:
                # Dummy field
                name = "%s-%s" % (base_name, level)
                options = levels[level]["options"]
                dummy_field = Storage(name=name,
                                      type=ftype,
                                      requires=IS_IN_SET(options,
                                                         multiple=True))
                # Unique ID/name
                attr["_id"] = "%s-%s" % (base_id, level)
                attr["_name"] = name
                # Find relevant values to pre-populate the widget
                _values = values.get("%s$%s__%s" % (fname, level, operator))
                w = S3MultiSelectWidget(filter = opts.get("filter", "auto"),
                                        header = opts.get("header", False),
                                        selectedList = opts.get("selectedList", 3),
                                        noneSelectedText = T("Select %(location)s") % \
                                                             dict(location=levels[level]["label"]))
                if first:
                    attr["_class"] = _class
                elif hide:
                    # Hide dropdowns other than first
                    _class = "%s hide" % _class
                    attr["_class"] = _class
                    hide = False
                widget = w(dummy_field, _values, **attr)
                w_append(widget)
                first = False

        # Restore id and name for the data_element
        attr["_id"] = base_id
        attr["_name"] = base_name

        # Render the filter widget
        return TAG[""](*widgets)

    # -------------------------------------------------------------------------
    def data_element(self, variable):
        """
            Construct the hidden element that holds the
            URL query term corresponding to an input element in the widget.

            @param variable: the URL query variable
        """

        output = []
        oappend = output.append
        i = 0
        for level in self.levels:
            widget = INPUT(_type="hidden",
                           _id="%s-%s-data" % (self.attr["_id"], level),
                           _class="filter-widget-data %s-data" % self._class,
                           _value=variable[i])
            oappend(widget)
            i += 1

        return output

    # -------------------------------------------------------------------------
    def ajax_options(self, resource):

        attr = self._attr(resource)
        ftype, levels, noopt = self._options(resource, inject_hierarchy=False)

        opts = {}
        base_id = attr["_id"]
        for level in levels:
            if noopt:
                opts["%s-%s" % (base_id, level)] = str(noopt)
            else:
                options = levels[level]["options"]
                opts["%s-%s" % (base_id, level)] = options
        return opts

    # -------------------------------------------------------------------------
    @staticmethod
    def __options(row, levels, inject_hierarchy, hierarchy, _level, translate, name_l10n):

        if inject_hierarchy:
            parent = None
            grandparent = None
            greatgrandparent = None
            greatgreatgrandparent = None
            greatgreatgreatgrandparent = None
            i = 0
        for level in levels:
            v = row[level]
            if v:
                o = levels[level]["options"]
                if v not in o:
                    if translate:
                        o[v] = name_l10n.get(v, v)
                    else:
                        o.append(v)
            if inject_hierarchy:
                if i == 0:
                    h = hierarchy[_level]
                    if v not in h:
                        h[v] = {}
                    parent = v
                elif i == 1:
                    h = hierarchy[_level][parent]
                    if v not in h:
                        h[v] = {}
                    grandparent = parent
                    parent = v
                elif i == 2:
                    h = hierarchy[_level][grandparent][parent]
                    if v not in h:
                        h[v] = {}
                    greatgrandparent = grandparent
                    grandparent = parent
                    parent = v
                elif i == 3:
                    h = hierarchy[_level][greatgrandparent][grandparent][parent]
                    if v not in h:
                        h[v] = {}
                    greatgreatgrandparent = greatgrandparent
                    greatgrandparent = grandparent
                    grandparent = parent
                    parent = v
                elif i == 4:
                    h = hierarchy[_level][greatgreatgrandparent][greatgrandparent][grandparent][parent]
                    if v not in h:
                        h[v] = {}
                    greatgreatgreatgrandparent = greatgreatgrandparent
                    greatgreatgrandparent = greatgrandparent
                    greatgrandparent = grandparent
                    grandparent = parent
                    parent = v
                elif i == 5:
                    h = hierarchy[_level][greatgreatgreatgrandparent][greatgreatgrandparent][greatgrandparent][grandparent][parent]
                    if v not in h:
                        h[v] = {}
                i += 1

    # -------------------------------------------------------------------------
    def _options(self, resource, inject_hierarchy=True, values=None):

        T = current.T
        s3db = current.s3db
        gtable = s3db.gis_location

        NOOPT = T("No options available")

        #attr = self.attr
        opts = self.opts
        translate = self.translate

        # Which levels should we display?
        # Lookup the appropriate labels from the GIS configuration
        if "levels" in opts:
            hierarchy = current.gis.get_location_hierarchy()
            levels = OrderedDict()
            for level in opts["levels"]:
                levels[level] = hierarchy.get(level, level)
        else:
            levels = current.gis.get_relevant_hierarchy_levels(as_dict=True)

        # Pass to data_element
        self.levels = levels

        if "label" not in opts:
            opts["label"] = T("Filter by Location")

        ftype = "reference gis_location"
        default = (ftype, levels.keys(), opts.get("no_opts", NOOPT))

        # Resolve the field selector
        selector = None
        if resource is None:
            rname = opts.get("resource")
            if rname:
                resource = s3db.resource(rname)
                selector = opts.get("lookup", "location_id")
        else:
            selector = self.field

        options = opts.get("options")
        if options:
            # Fixed options (=list of location IDs)
            resource = s3db.resource("gis_location", id=options)
            fields = ["id"] + [l for l in levels]
            if translate:
                fields.append("path")
            joined = False

        elif selector:
            # Lookup options from resource
            rfield = S3ResourceField(resource, selector)
            if not rfield.field or rfield.ftype != ftype:
                # Must be a real reference to gis_location
                return default
            fields = [selector] + ["%s$%s" % (selector, l) for l in levels]
            if translate:
                fields.append("%s$path" % selector)
            joined = True
            # Filter out old Locations
            # @ToDo: Allow override
            resource.add_filter(gtable.end_date == None)

        else:
            # Neither fixed options nor resource to look them up
            return default

        # Find the options
        rows = resource.select(fields=fields,
                               limit=None,
                               virtual=False,
                               as_rows=True)
        rows2 = []
        if not rows:
            if values:
                # Make sure the selected options are in the available options
                resource = s3db.resource("gis_location")
                fields = ["id"] + [l for l in levels]
                if translate:
                    fields.append("path")
                joined = False
                rows = []
                for f in values:
                    v = values[f]
                    if not v:
                        continue
                    level = "L%s" % f.split("L", 1)[1][0]
                    resource.clear_query()
                    query = (gtable.level == level) & \
                            (gtable.name.belongs(v))
                    resource.add_filter(query)
                    # Filter out old Locations
                    # @ToDo: Allow override
                    resource.add_filter(gtable.end_date == None)
                    _rows = resource.select(fields=fields,
                                            limit=None,
                                            virtual=False,
                                            as_rows=True)
                    if rows:
                        rows &= _rows
                    else:
                        rows = _rows

            if not rows:
                # No options
                return default

        elif values:
            # Make sure the selected options are in the available options
            resource2 = s3db.resource("gis_location")
            fields = ["id"] + [l for l in levels]
            if translate:
                fields.append("path")
            for f in values:
                v = values[f]
                if not v:
                    continue
                level = "L%s" % f.split("L", 1)[1][0]
                resource2.clear_query()
                query = (gtable.level == level) & \
                        (gtable.name.belongs(v))
                resource2.add_filter(query)
                # Filter out old Locations
                # @ToDo: Allow override
                resource2.add_filter(gtable.end_date == None)
                _rows = resource2.select(fields=fields,
                                         limit=None,
                                         virtual=False,
                                         as_rows=True)
                if rows2:
                    rows2 &= _rows
                else:
                    rows2 = _rows

        # Initialise Options Storage & Hierarchy
        hierarchy = {}
        first = True
        for level in levels:
            if first:
                hierarchy[level] = {}
                _level = level
                first = False
            levels[level] = {"label": levels[level],
                             "options": {} if translate else [],
                             }

        # Generate a name localization lookup dict
        name_l10n = {}
        if translate:
            # Get IDs via Path to lookup name_l10n
            ids = set()
            if joined:
                if "$" in selector:
                    selector = "%s.%s" % (rfield.field.tablename, selector.split("$", 1)[1])
                elif "." in selector:
                    selector = "%s.%s" % (rfield.field.tablename, selector.split(".", 1)[1])
                else:
                    selector = "%s.%s" % (resource.tablename, selector)
            for row in rows:
                _row = getattr(row, "gis_location") if joined else row
                path = _row.path
                if path:
                    path = path.split("/")
                else:
                    # Build it
                    if joined:
                        location_id = row[selector]
                        if location_id:
                            _row.id = location_id
                    if "id" in _row:
                        path = current.gis.update_location_tree(_row)
                        path = path.split("/")
                if path:
                    ids |= set(path)
            for row in rows2:
                path = row.path
                if path:
                    path = path.split("/")
                else:
                    # Build it
                    if "id" in row:
                        path = current.gis.update_location_tree(row)
                        path = path.split("/")
                if path:
                    ids |= set(path)
            # Build lookup table for name_l10n
            ntable = s3db.gis_location_name
            query = (gtable.id.belongs(ids)) & \
                    (ntable.deleted == False) & \
                    (ntable.location_id == gtable.id) & \
                    (ntable.language == current.session.s3.language)
            nrows = current.db(query).select(gtable.name,
                                             ntable.name_l10n,
                                             limitby=(0, len(ids)),
                                             )
            for row in nrows:
                name_l10n[row["gis_location.name"]] = row["gis_location_name.name_l10n"]

        # Populate the Options and the Hierarchy
        for row in rows:
            _row = getattr(row, "gis_location") if joined else row
            self.__options(_row, levels, inject_hierarchy, hierarchy, _level, translate, name_l10n)
        for row in rows2:
            self.__options(row, levels, inject_hierarchy, hierarchy, _level, translate, name_l10n)

        if translate:
            # Sort the options dicts
            for level in levels:
                options = levels[level]["options"]
                options = OrderedDict(sorted(options.iteritems()))
        else:
            # Sort the options lists
            for level in levels:
                levels[level]["options"].sort()

        if inject_hierarchy:
            # Inject the Location Hierarchy
            hierarchy = "S3.location_filter_hierarchy=%s" % \
                json.dumps(hierarchy, separators=SEPARATORS)
            js_global = current.response.s3.js_global
            js_global.append(hierarchy)
            if translate:
                # Inject lookup list
                name_l10n = "S3.location_name_l10n=%s" % \
                    json.dumps(name_l10n, separators=SEPARATORS)
                js_global.append(name_l10n)

        return (ftype, levels, None)

    # -------------------------------------------------------------------------
    def _selector(self, resource, fields):
        """
            Helper method to generate a filter query selector for the
            given field(s) in the given resource.

            @param resource: the S3Resource
            @param fields: the field selectors (as strings)

            @return: the field label and the filter query selector, or None if none of the
                     field selectors could be resolved
        """

        prefix = self._prefix

        if resource:
            rfield = S3ResourceField(resource, fields)
            label = rfield.label
        else:
            label = None

        if "levels" in self.opts:
            levels = self.opts.levels
        else:
            levels = current.gis.get_relevant_hierarchy_levels()

        fields = ["%s$%s" % (fields, level) for level in levels]
        if resource:
            selectors = []
            for field in fields:
                try:
                    rfield = S3ResourceField(resource, field)
                except (AttributeError, TypeError):
                    continue
                selectors.append(prefix(rfield.selector))
        else:
            selectors = fields
        if selectors:
            return label, "|".join(selectors)
        else:
            return label, None

    # -------------------------------------------------------------------------
    @classmethod
    def _variable(cls, selector, operator):
        """
            Construct URL query variable(s) name from a filter query
            selector and the given operator(s)

            @param selector: the selector
            @param operator: the operator (or tuple/list of operators)

            @return: the URL query variable name (or list of variable names)
        """

        selectors = selector.split("|")
        return ["%s__%s" % (selector, operator) for selector in selectors]

# =============================================================================
class S3OptionsFilter(S3FilterWidget):
    """
        Options filter widget
        @see: L{Configuration Options<S3FilterWidget.__init__>}
    """

    _class = "options-filter"

    operator = "belongs"

    alternatives = ["anyof", "contains"]

    # -------------------------------------------------------------------------
    def widget(self, resource, values):
        """
            Render this widget as HTML helper object(s)

            @param resource: the resource
            @param values: the search values from the URL query
        """

        attr = self._attr(resource)
        opts = self.opts
        name = attr["_name"]

        # Get the options
        ftype, options, noopt = self._options(resource, values=values)
        if noopt:
            return SPAN(noopt, _class="no-options-available")
        else:
            options = OrderedDict(options)

        # Any-All-Option : for many-to-many fields the user can
        # search for records containing all the options or any
        # of the options:
        if len(options) > 1 and ftype[:4] == "list":
            operator = opts.get("operator", None)
            if operator:
                self.operator = operator
                any_all = ""
            else:
                operator = self.operator
                any_all = True

            if operator == "anyof":
                filter_type = "any"
            else:
                filter_type = "all"
                if operator == "belongs":
                    operator = "contains"

            if any_all:
                # Provide a form to prompt the user to choose
                T = current.T
                any_all = DIV(T("Filter type"),
                              INPUT(_name="%s_filter" % name,
                                    _id="%s_filter_any" % name,
                                    _type="radio",
                                    _value="any",
                                    value=filter_type),
                              LABEL(T("Any"),
                                    _for="%s_filter_any" % name),
                              INPUT(_name="%s_filter" % name,
                                    _id="%s_filter_all" % name,
                                    _type="radio",
                                    _value="all",
                                    value=filter_type),
                              LABEL(T("All"),
                                    _for="%s_filter_all" % name),
                              _class="s3-options-filter-anyall",
                              )

        else:
            any_all = ""

        # Initialize widget
        #widget_type = opts["widget"]
        # Use groupedopts widget if we specify cols, otherwise assume multiselect
        cols = opts.get("cols", None)
        if cols:
            widget_class = "groupedopts-filter-widget"
            w = S3GroupedOptionsWidget(options = options,
                                       multiple = opts.get("multiple", True),
                                       cols = cols,
                                       size = opts["size"] or 12,
                                       help_field = opts["help_field"],
                                       )
        else:
            # Default widget_type = "multiselect"
            widget_class = "multiselect-filter-widget"
            w = S3MultiSelectWidget(filter = opts.get("filter", "auto"),
                                    header = opts.get("header", False),
                                    selectedList = opts.get("selectedList", 3),
                                    multiple = opts.get("multiple", True),
                                    )


        # Add widget class and default class
        classes = set(attr.get("_class", "").split()) | \
                  set((widget_class, self._class))
        attr["_class"] = " ".join(classes) if classes else None

        # Render the widget
        dummy_field = Storage(name=name,
                              type=ftype,
                              requires=IS_IN_SET(options, multiple=True))
        widget = w(dummy_field, values, **attr)

        return TAG[""](any_all, widget)

    # -------------------------------------------------------------------------
    def ajax_options(self, resource):
        """
            Method to Ajax-retrieve the current options of this widget

            @param resource: the S3Resource
        """

        opts = self.opts
        attr = self._attr(resource)
        ftype, options, noopt = self._options(resource)

        if noopt:
            options = {attr["_id"]: str(noopt)}
        else:
            #widget_type = opts["widget"]
            # Use groupedopts widget if we specify cols, otherwise assume multiselect
            cols = opts.get("cols", None)
            if cols:
                # Use the widget method to group and sort the options
                widget = S3GroupedOptionsWidget(
                                options = options,
                                multiple = True,
                                cols = cols,
                                size = opts["size"] or 12,
                                help_field = opts["help_field"]
                                )
                options = {attr["_id"]:
                           widget._options({"type": ftype}, [])}
            else:
                # Multiselect
                # Produce a simple list of tuples
                options = {attr["_id"]: [(k, s3_unicode(v))
                                         for k, v in options]}

        return options

    # -------------------------------------------------------------------------
    def _options(self, resource, values=None):
        """
            Helper function to retrieve the current options for this
            filter widget

            @param resource: the S3Resource
        """

        T = current.T
        NOOPT = T("No options available")
        EMPTY = T("None")

        #attr = self.attr
        opts = self.opts

        # Resolve the field selector
        selector = self.field
        if isinstance(selector, (tuple, list)):
            selector = selector[0]

        if resource is None:
            rname = opts.get("resource")
            if rname:
                resource = current.s3db.resource(rname)

        if resource:
            rfield = S3ResourceField(resource, selector)
            field = rfield.field
            colname = rfield.colname
            ftype = rfield.ftype
        else:
            rfield = field = colname = None
            ftype = "string"

        # Find the options
        opt_keys = []

        multiple = ftype[:5] == "list:"
        if opts.options is not None:
            # Custom dict of options {value: label} or a callable
            # returning such a dict:
            options = opts.options
            if callable(options):
                options = options()
            opt_keys = options.keys()

        elif resource:
            # Determine the options from the field type
            options = None
            if ftype == "boolean":
                opt_keys = (True, False)

            elif field or rfield.virtual:

                groupby = field if field and not multiple else None
                virtual = field is None

                # If the search field is a foreign key, then try to perform
                # a reverse lookup of primary IDs in the lookup table which
                # are linked to at least one record in the resource => better
                # scalability.
                rows = None
                if field:
                    ktablename, key, m = s3_get_foreign_key(field, m2m=False)
                    if ktablename:

                        multiple = m

                        ktable = current.s3db.table(ktablename)
                        key_field = ktable[key]
                        colname = str(key_field)
                        left = None

                        accessible_query = current.auth.s3_accessible_query

                        # Respect the validator of the foreign key field.

                        # Commented because questionable: We want a filter
                        # option for every current field value, even if it
                        # doesn't match the validator (don't we?)

                        #requires = field.requires
                        #if requires:
                            #if not isinstance(requires, list):
                                #requires = [requires]
                            #requires = requires[0]
                            #if isinstance(requires, IS_EMPTY_OR):
                                #requires = requires.other
                            #if isinstance(requires, IS_ONE_OF_EMPTY):
                                #query, left = requires.query(ktable)
                        #else:
                            #query = accessible_query("read", ktable)
                        #query &= (key_field == field)

                        query = (key_field == field)
                        joins = rfield.join
                        for tname in joins:
                            query &= joins[tname]

                        # We do not allow the user to see values only used
                        # in records he's not permitted to see:
                        query &= accessible_query("read", resource.table)

                        # Filter options by location?
                        location_filter = opts.get("location_filter")
                        if location_filter and "location_id" in ktable:
                            location = current.session.s3.location_filter
                            if location:
                                query &= (ktable.location_id == location)

                        # Filter options by organisation?
                        org_filter = opts.get("org_filter")
                        if org_filter and "organisation_id" in ktable:
                            root_org = current.auth.root_org()
                            if root_org:
                                query &= ((ktable.organisation_id == root_org) | \
                                          (ktable.organisation_id == None))
                            #else:
                            #    query &= (ktable.organisation_id == None)

                        rows = current.db(query).select(key_field,
                                                        resource._id.min(),
                                                        groupby=key_field,
                                                        left=left)

                # If we can not perform a reverse lookup, then we need
                # to do a forward lookup of all unique values of the
                # search field from all records in the table :/ still ok,
                # but not endlessly scalable:
                if rows is None:
                    rows = resource.select([selector],
                                           limit=None,
                                           orderby=field,
                                           groupby=groupby,
                                           virtual=virtual,
                                           as_rows=True)

                opt_keys = [] # Can't use set => would make orderby pointless
                if rows:
                    kappend = opt_keys.append
                    kextend = opt_keys.extend
                    for row in rows:
                        val = row[colname]
                        if virtual and callable(val):
                            val = val()
                        if multiple or \
                           virtual and isinstance(val, (list, tuple, set)):
                            kextend([v for v in val
                                       if v not in opt_keys])
                        elif val not in opt_keys:
                            kappend(val)

        # Make sure the selected options are in the available options
        # (not possible if we have a fixed options dict)
        if options is None and values:
            numeric = rfield.ftype in ("integer", "id") or \
                      rfield.ftype[:9] == "reference"
            for _val in values:
                if numeric:
                    try:
                        val = int(_val)
                    except ValueError:
                        # not valid for this field type => skip
                        continue
                else:
                    val = _val
                if val not in opt_keys and \
                   (not isinstance(val, (int, long)) or not str(val) in opt_keys):
                    opt_keys.append(val)

        # No options?
        if len(opt_keys) < 1 or len(opt_keys) == 1 and not opt_keys[0]:
            return (ftype, None, opts.get("no_opts", NOOPT))

        # Represent the options
        opt_list = [] # list of tuples (key, value)

        # Custom represent? (otherwise fall back to field.represent)
        represent = opts.represent
        if not represent: # or ftype[:9] != "reference":
            represent = field.represent if field else None

        if options is not None:
            # Custom dict of {value:label} => use this label
            opt_list = options.items()

        elif callable(represent):
            # Callable representation function:

            if hasattr(represent, "bulk"):
                # S3Represent => use bulk option
                opt_dict = represent.bulk(opt_keys,
                                          list_type=False,
                                          show_link=False)
                if None in opt_keys:
                    opt_dict[None] = EMPTY
                elif None in opt_dict:
                    del opt_dict[None]
                if "" in opt_keys:
                    opt_dict[""] = EMPTY
                opt_list = opt_dict.items()

            else:
                # Simple represent function
                args = {"show_link": False} \
                       if "show_link" in represent.func_code.co_varnames else {}
                if multiple:
                    repr_opt = lambda opt: opt in (None, "") and (opt, EMPTY) or \
                                           (opt, represent([opt], **args))
                else:
                    repr_opt = lambda opt: opt in (None, "") and (opt, EMPTY) or \
                                           (opt, represent(opt, **args))
                opt_list = map(repr_opt, opt_keys)

        elif isinstance(represent, str) and ftype[:9] == "reference":
            # Represent is a string template to be fed from the
            # referenced record

            # Get the referenced table
            db = current.db
            ktable = db[ftype[10:]]

            k_id = ktable._id.name

            # Get the fields referenced by the string template
            fieldnames = [k_id]
            fieldnames += re.findall("%\(([a-zA-Z0-9_]*)\)s", represent)
            represent_fields = [ktable[fieldname] for fieldname in fieldnames]

            # Get the referenced records
            query = (ktable.id.belongs([k for k in opt_keys
                                              if str(k).isdigit()])) & \
                    (ktable.deleted == False)
            rows = db(query).select(*represent_fields).as_dict(key=k_id)

            # Run all referenced records against the format string
            opt_list = []
            ol_append = opt_list.append
            for opt_value in opt_keys:
                if opt_value in rows:
                    opt_represent = represent % rows[opt_value]
                    if opt_represent:
                        ol_append((opt_value, opt_represent))

        else:
            # Straight string representations of the values (fallback)
            opt_list = [(opt_value, s3_unicode(opt_value))
                        for opt_value in opt_keys if opt_value]

        if opts.get("sort", True):
            try:
                opt_list.sort(key=lambda item: item[1])
            except:
                opt_list.sort(key=lambda item: s3_unicode(item[1]))
        options = []
        empty = False
        none = opts["none"]
        for k, v in opt_list:
            if k is None:
                if none:
                    empty = True
                    if none is True:
                        # Use the represent
                        options.append((k, v))
                    else:
                        # Must be a string to use as the represent:
                        options.append((k, none))
            else:
                options.append((k, v))
        if none and not empty:
            # Add the value anyway (e.g. not found via the reverse lookup)
            if none is True:
                none = current.messages["NONE"]
            options.append((None, none))

        if not opts.get("multiple") and not self.values:
            # Browsers automatically select the first option in single-selects,
            # but that doesn't filter the data, so the first option must be
            # empty if we don't have a default:
            options.insert(0, ("", ""))

        # Sort the options
        return (ftype, options, None)

    # -------------------------------------------------------------------------
    @staticmethod
    def _values(get_vars, variable):
        """
            Helper method to get all values of a URL query variable

            @param get_vars: the GET vars (a dict)
            @param variable: the name of the query variable

            @return: a list of values
        """

        if not variable:
            return []

        # Match __eq before checking any other operator
        selector = variable.split("__", 1)[0]
        for key in ("%s__eq" % selector, selector, variable):
            if key in get_vars:
                values = S3URLQuery.parse_value(get_vars[key])
                if not isinstance(values, (list, tuple)):
                    values = [values]
                return values

        return []

# =============================================================================
class S3HierarchyFilter(S3FilterWidget):
    """
        Filter widget for hierarchical types

        Specific options:

            lookup              name of the lookup table
            represent           representation method for the key
            multiple            allow selection of multiple options
            leafonly            only lead nodes can be selected
    """

    _class = "hierarchy-filter"

    operator = "belongs"

    # -------------------------------------------------------------------------
    def widget(self, resource, values):
        """
            Render this widget as HTML helper object(s)

            @param resource: the resource
            @param values: the search values from the URL query
        """

        # Currently selected values
        selected = []
        append = selected.append
        if not isinstance(values, (list, tuple, set)):
            values = [values]
        for v in values:
            if isinstance(v, (int, long)) or str(v).isdigit():
                append(v)

        # Resolve the field selector
        rfield = S3ResourceField(resource, self.field)

        # Instantiate the widget
        opts = self.opts
        w = S3HierarchyWidget(lookup = opts.get("lookup"),
                              represent = opts.get("represent"),
                              multiple = opts.get("multiple", True),
                              leafonly = opts.get("leafonly", True),
                              filter = opts.get("filter"),
                              )

        # Render the widget
        widget = w(rfield.field, selected, **self._attr(resource))
        widget.add_class(self._class)

        return widget

    # -------------------------------------------------------------------------
    def variable(self, resource, get_vars=None):
        """
            Generate the name for the URL query variable for this
            widget, detect alternative __typeof queries.

            @param resource: the resource
            @return: the URL query variable name (or list of
                     variable names if there are multiple operators)
        """

        label, self.selector = self._selector(resource, self.field)

        if not self.selector:
            return None

        if "label" not in self.opts:
            self.opts["label"] = label

        selector = self.selector

        if self.alternatives and get_vars is not None:
            # Get the actual operator from get_vars
            operator = self._operator(get_vars, self.selector)
            if operator:
                self.operator = operator

        variable = self._variable(selector, self.operator)

        if not get_vars or not resource or variable in get_vars:
            return variable

        # Detect and resolve __typeof queries
        #BELONGS = current.db._adapter.BELONGS
        resolve = S3ResourceQuery._resolve_hierarchy
        selector = resource.prefix_selector(selector)
        for key, value in get_vars.items():

            if key.startswith(selector):
                selectors, op, invert = S3URLQuery.parse_expression(key)
            else:
                continue
            if op != "typeof" or len(selectors) != 1:
                continue

            rfield = resource.resolve_selector(selectors[0])
            if rfield.field:
                values = S3URLQuery.parse_value(value)
                hierarchy, field, nodeset, none = resolve(rfield.field, values)
                if field and (nodeset or none):
                    if nodeset is None:
                        nodeset = set()
                    if none:
                        nodeset.add(None)
                    get_vars.pop(key, None)
                    get_vars[variable] = [str(v) for v in nodeset]
            break

        return variable

# =============================================================================
class S3FilterForm(object):
    """ Helper class to construct and render a filter form for a resource """

    def __init__(self, widgets, **attr):
        """
            Constructor

            @param widgets: the widgets (as list)
            @param attr: HTML attributes for this form
        """

        self.widgets = widgets

        attributes = Storage()
        options = Storage()
        for k, v in attr.iteritems():
            if k[0] == "_":
                attributes[k] = v
            else:
                options[k] = v
        self.attr = attributes
        self.opts = options

    # -------------------------------------------------------------------------
    def html(self, resource, get_vars=None, target=None, alias=None):
        """
            Render this filter form as HTML form.

            @param resource: the S3Resource
            @param get_vars: the request GET vars (URL query dict)
            @param target: the HTML element ID of the target object for
                           this filter form (e.g. a datatable)
            @param alias: the resource alias to use in widgets
        """

        attr = self.attr
        form_id = attr.get("_id")
        if not form_id:
            form_id = "filter-form"
        attr["_id"] = form_id

        # Prevent issues with Webkit-based browsers & Back buttons
        attr["_autocomplete"] = "off"

        opts = self.opts
        settings = current.deployment_settings

        # Form style
        formstyle = opts.get("formstyle", None)
        if not formstyle:
            formstyle = settings.get_ui_filter_formstyle()

        # Filter widgets
        rows = self._render_widgets(resource,
                                    get_vars=get_vars or {},
                                    alias=alias,
                                    formstyle=formstyle)

        # Other filter form controls
        controls = self._render_controls(resource)
        if controls:
            rows.append(formstyle(None, "", controls, ""))

        # Submit elements
        ajax = opts.get("ajax", False)
        submit = opts.get("submit", False)
        if submit:
            # Auto-submit?
            auto_submit = settings.get_ui_filter_auto_submit()
            if auto_submit and opts.get("auto_submit", True):
                script = '''S3.search.filterFormAutoSubmit('%s',%s)''' % \
                         (form_id, auto_submit)
                current.response.s3.jquery_ready.append(script)

            # Custom label and class
            _class = None
            if submit is True:
                label = current.T("Search")
            elif isinstance(submit, (list, tuple)):
                label, _class = submit
            else:
                label = submit

            # Submit button
            submit_button = INPUT(_type="button",
                                  _value=label,
                                  _class="filter-submit")
            #if auto_submit:
                #submit_button.add_class("hide")
            if _class:
                submit_button.add_class(_class)

            # Where to request filtered data from:
            submit_url = opts.get("url", URL(vars={}))

            # Where to request updated options from:
            ajax_url = opts.get("ajaxurl", URL(args=["filter.options"], vars={}))

            # Submit row elements
            submit = TAG[""](submit_button,
                             INPUT(_type="hidden",
                                   _class="filter-ajax-url",
                                   _value=ajax_url),
                             INPUT(_type="hidden",
                                   _class="filter-submit-url",
                                   _value=submit_url))
            if ajax and target:
                submit.append(INPUT(_type="hidden",
                                    _class="filter-submit-target",
                                    _value=target))

            # Append submit row
            submit_row = formstyle(None, "", submit, "")
            if auto_submit and hasattr(submit_row, "add_class"):
                submit_row.add_class("hide")
            rows.append(submit_row)

        # Filter Manager (load/apply/save filters)
        fm = settings.get_search_filter_manager()
        if fm and opts.get("filter_manager", resource is not None):
            filter_manager = self._render_filters(resource, form_id)
            if filter_manager:
                fmrow = formstyle(None, "", filter_manager, "")
                if hasattr(fmrow, "add_class"):
                    fmrow.add_class("hide filter-manager-row")
                rows.append(fmrow)

        # Adapt to formstyle: render a TABLE only if formstyle returns TRs
        if rows:
            elements = rows[0]
            if not isinstance(elements, (list, tuple)):
                elements = elements.elements()
            n = len(elements)
            if n > 0 and elements[0].tag == "tr" or \
               n > 1 and elements[0].tag == "" and elements[1].tag == "tr":
                form = FORM(TABLE(TBODY(rows)), **attr)
            else:
                form = FORM(DIV(rows), **attr)
                if settings.ui.formstyle == "bootstrap":
                    # We need to amend the HTML markup to support this CSS framework
                    form.add_class("form-horizontal")
            form.add_class("filter-form")
            if ajax:
                form.add_class("filter-ajax")
        else:
            return ""

        # Put a copy of formstyle into the form for access by the view
        form.formstyle = formstyle
        return form

    # -------------------------------------------------------------------------
    def fields(self, resource, get_vars=None, alias=None):
        """
            Render the filter widgets without FORM wrapper, e.g. to
            embed them as fieldset in another form.

            @param resource: the S3Resource
            @param get_vars: the request GET vars (URL query dict)
            @param alias: the resource alias to use in widgets
        """

        formstyle = self.opts.get("formstyle", None)
        if not formstyle:
            formstyle = current.deployment_settings.get_ui_filter_formstyle()

        rows = self._render_widgets(resource,
                                    get_vars=get_vars,
                                    alias=alias,
                                    formstyle=formstyle)

        controls = self._render_controls(resource)
        if controls:
            rows.append(formstyle(None, "", controls, ""))

        # Adapt to formstyle: only render a TABLE if formstyle returns TRs
        if rows:
            elements = rows[0]
            if not isinstance(elements, (list, tuple)):
                elements = elements.elements()
            n = len(elements)
            if n > 0 and elements[0].tag == "tr" or \
               n > 1 and elements[0].tag == "" and elements[1].tag == "tr":
                fields = TABLE(TBODY(rows))
            else:
                fields = DIV(rows)

        return fields

    # -------------------------------------------------------------------------
    def _render_controls(self, resource):
        """
            Render optional additional filter form controls: advanced
            options toggle, clear filters.
        """

        T = current.T
        controls = []
        opts = self.opts

        advanced = opts.get("advanced", False)
        if advanced:
            _class = "filter-advanced"
            if advanced is True:
                label = T("More Options")
            elif isinstance(advanced, (list, tuple)):
                label = advanced[0]
                label = advanced[1]
                if len(advanced > 2):
                    _class = "%s %s" % (advanced[2], _class)
            else:
                label = advanced
            label_off = T("Less Options")
            advanced = A(SPAN(label,
                              data = {"on": label,
                                      "off": label_off,
                                      },
                              _class="filter-advanced-label",
                              ),
                         ICON("down"),
                         ICON("up", _style="display:none"),
                         _class=_class
                         )
            controls.append(advanced)

        clear = opts.get("clear", True)
        if clear:
            _class = "filter-clear"
            if clear is True:
                label = T("Clear filter")
            elif isinstance(clear, (list, tuple)):
                label = clear[0]
                _class = "%s %s" % (clear[1], _class)
            else:
                label = clear
            clear = A(label, _class=_class)
            clear.add_class("action-lnk")
            controls.append(clear)

        fm = current.deployment_settings.get_search_filter_manager()
        if fm and opts.get("filter_manager", resource is not None):
            show_fm = A(T("Saved filters"),
                        _class="show-filter-manager action-lnk")
            controls.append(show_fm)

        if controls:
            return DIV(controls, _class="filter-controls")
        else:
            return None

    # -------------------------------------------------------------------------
    def _render_widgets(self,
                        resource,
                        get_vars=None,
                        alias=None,
                        formstyle=None):
        """
            Render the filter widgets

            @param resource: the S3Resource
            @param get_vars: the request GET vars (URL query dict)
            @param alias: the resource alias to use in widgets
            @param formstyle: the formstyle to use

            @return: a list of form rows
        """

        rows = []
        rappend = rows.append
        advanced = False
        for f in self.widgets:
            widget = f(resource, get_vars, alias=alias)
            label = f.opts["label"]
            comment = f.opts["comment"]
            hidden = f.opts["hidden"]
            if hidden:
                advanced = True
            widget_id = f.attr["_id"]
            if widget_id:
                row_id = "%s__row" % widget_id
                label_id = "%s__label" % widget_id
            else:
                row_id = None
                label_id = None
            if label:
                label = LABEL("%s:" % label, _id=label_id, _for=widget_id)
            else:
                label = ""
            if not comment:
                comment = ""
            formrow = formstyle(row_id, label, widget, comment, hidden=hidden)
            if hidden:
                if isinstance(formrow, DIV):
                    formrow.add_class("advanced")
                elif isinstance(formrow, tuple):
                    for item in formrow:
                        if hasattr(item, "add_class"):
                            item.add_class("advanced")
            rappend(formrow)
        if advanced:
            if resource:
                self.opts["advanced"] = resource.get_config(
                                            "filter_advanced", True)
            else:
                self.opts["advanced"] = True
        return rows

    # -------------------------------------------------------------------------
    def _render_filters(self, resource, form_id):
        """
            Render a filter manager widget

            @param resource: the resource
            @return: the widget
        """

        SELECT_FILTER = current.T("Saved Filters...")

        ajaxurl = self.opts.get("saveurl", URL(args=["filter.json"], vars={}))

        # Current user
        auth = current.auth
        pe_id = auth.user.pe_id if auth.s3_logged_in() else None
        if not pe_id:
            return None

        table = current.s3db.pr_filter
        query = (table.deleted != True) & \
                (table.pe_id == pe_id)

        if resource:
            query &= (table.resource == resource.tablename)
        else:
            query &= (table.resource == None)

        rows = current.db(query).select(table._id,
                                        table.title,
                                        table.query,
                                        orderby=table.title)

        options = [OPTION(SELECT_FILTER,
                          _value="",
                          _class="filter-manager-prompt",
                          _disabled="disabled")]
        add_option = options.append
        filters = {}
        for row in rows:
            filter_id = row[table._id]
            add_option(OPTION(row.title, _value=filter_id))
            query = row.query
            if query:
                query = json.loads(query)
            filters[filter_id] = query
        widget_id = "%s-fm" % form_id
        widget = DIV(SELECT(options,
                            _id=widget_id,
                            _class="filter-manager-widget"),
                     _class="filter-manager-container")

        # JSON-serializable translator
        T = current.T
        _t = lambda s: str(T(s))

        # Configure the widget
        settings = current.deployment_settings
        config = dict(

            # Filters and Ajax URL
            filters = filters,
            ajaxURL = ajaxurl,

            # Workflow Options
            allowDelete = settings.get_search_filter_manager_allow_delete(),

            # Tooltips for action icons/buttons
            createTooltip = _t("Save current options as new filter"),
            loadTooltip = _t("Load filter"),
            saveTooltip = _t("Update saved filter"),
            deleteTooltip = _t("Delete saved filter"),

            # Hints
            titleHint = _t("Enter a title..."),
            selectHint = str(SELECT_FILTER),
            emptyHint = _t("No saved filters"),

            # Confirm update + confirmation text
            confirmUpdate = _t("Update this filter?"),
            confirmDelete = _t("Delete this filter?"),
        )

        # Render actions as buttons with text if configured, otherwise
        # they will appear as empty DIVs with classes for CSS icons
        create_text = settings.get_search_filter_manager_save()
        if create_text:
            config["createText"] = _t(create_text)
        update_text = settings.get_search_filter_manager_update()
        if update_text:
            config["saveText"] = _t(update_text)
        delete_text = settings.get_search_filter_manager_delete()
        if delete_text:
            config["deleteText"] = _t(delete_text)
        load_text = settings.get_search_filter_manager_load()
        if load_text:
            config["loadText"] = _t(load_text)

        script = '''$("#%s").filtermanager(%s)''' % \
                    (widget_id,
                     json.dumps(config, separators=SEPARATORS))

        current.response.s3.jquery_ready.append(script)

        return widget

    # -------------------------------------------------------------------------
    def json(self, resource, get_vars=None):
        """
            Render this filter form as JSON (for Ajax requests)

            @param resource: the S3Resource
            @param get_vars: the request GET vars (URL query dict)
        """

        raise NotImplementedError

    # -------------------------------------------------------------------------
    @staticmethod
    def apply_filter_defaults(request, resource):
        """
            Add default filters to resource, to be called a multi-record
            view with a filter form is rendered the first time and before
            the view elements get processed

            @param request: the request
            @param resource: the resource
        """

        s3 = current.response.s3

        get_vars = request.get_vars
        tablename = resource.tablename

        # Do we have filter defaults for this resource?
        filter_defaults = s3
        for level in ("filter_defaults", tablename):
            if level not in filter_defaults:
                filter_defaults = None
                break
            filter_defaults = filter_defaults[level]

        # Which filter widgets do we need to apply defaults for?
        filter_widgets = resource.get_config("filter_widgets")
        for filter_widget in filter_widgets:

            # Do not apply defaults of hidden widgets because they are
            # not visible to the user:
            if filter_widget.opts.hidden:
                continue

            has_default = False
            if "default" in filter_widget.opts:
                has_default = True
            elif filter_defaults is None:
                continue

            defaults = set()
            variable = filter_widget.variable(resource, get_vars)
            multiple = type(variable) is list

            # Do we have a corresponding value in get_vars?
            if multiple:
                for k in variable:
                    values = filter_widget._values(get_vars, k)
                    if values:
                        filter_widget.values[k] = values
                    else:
                        defaults.add(k)
            else:
                values = filter_widget._values(get_vars, variable)
                if values:
                    filter_widget.values[variable] = values
                else:
                    defaults.add(variable)

            # Extract widget default
            if has_default:
                widget_default = filter_widget.opts["default"]
                if not isinstance(widget_default, dict):
                    if multiple:
                        widget_default = dict((k, widget_default)
                                              for k in variable)
                    else:
                        widget_default = {variable: widget_default}
                for k in widget_default:
                    if k not in filter_widget.values:
                        defaults.add(k)
            else:
                widget_default = {}

            default_filters = {}
            for variable in defaults:
                if "__" in variable:
                    selector, operator = variable.split("__", 1)
                else:
                    selector, operator = variable, None

                if filter_defaults and selector in filter_defaults:
                    applicable_defaults = filter_defaults[selector]
                elif variable in widget_default:
                    applicable_defaults = widget_default[variable]
                else:
                    continue

                if callable(applicable_defaults):
                    applicable_defaults = applicable_defaults(selector,
                                                              tablename=tablename)
                if isinstance(applicable_defaults, dict):
                    if operator in applicable_defaults:
                        default = applicable_defaults[operator]
                    else:
                        continue
                elif operator in (None, "belongs", "eq"):
                    default = applicable_defaults
                else:
                    continue
                if default is None:
                    # Ignore (return [None] to filter for None)
                    continue
                elif not isinstance(default, list):
                    default = [default]
                filter_widget.values[variable] = [str(v) if v is None else v
                                                  for v in default]
                default_filters[variable] = ",".join(s3_unicode(v)
                                                     for v in default)

            # Apply to resource
            queries = S3URLQuery.parse(resource, default_filters)
            add_filter = resource.add_filter
            for alias in queries:
                for q in queries[alias]:
                    add_filter(q)

        return

# =============================================================================
class S3Filter(S3Method):
    """ Back-end for filter forms """

    def apply_method(self, r, **attr):
        """
            Entry point for REST interface

            @param r: the S3Request
            @param attr: additional controller parameters
        """

        representation = r.representation
        if representation == "options":
            # Return the filter options as JSON
            return self._options(r, **attr)

        elif representation == "json":
            if r.http == "GET":
                # Load list of saved filters
                return self._load(r, **attr)
            elif r.http == "POST":
                if "delete" in r.get_vars:
                    # Delete a filter
                    return self._delete(r, **attr)
                else:
                    # Save a filter
                    return self._save(r, **attr)
            else:
                r.error(405, current.ERROR.BAD_METHOD)

        elif representation == "html":
            return self._form(r, **attr)

        else:
            r.error(501, current.ERROR.BAD_FORMAT)

    # -------------------------------------------------------------------------
    def _form(self, r, **attr):
        """
            Get the filter form for the target resource as HTML snippet

            GET filter.html

            @param r: the S3Request
            @param attr: additional controller parameters
        """

        r.error(501, current.ERROR.NOT_IMPLEMENTED)

    # -------------------------------------------------------------------------
    def _options(self, r, **attr):
        """
            Get the updated options for the filter form for the target
            resource as JSON

            GET filter.options

            @param r: the S3Request
            @param attr: additional controller parameters
        """

        resource = self.resource
        get_config = resource.get_config

        options = {}

        filter_widgets = get_config("filter_widgets", None)
        if filter_widgets:
            fresource = current.s3db.resource(resource.tablename)

            for widget in filter_widgets:
                if hasattr(widget, "ajax_options"):
                    opts = widget.ajax_options(fresource)
                    if opts and isinstance(opts, dict):
                        options.update(opts)

        options = json.dumps(options, separators=SEPARATORS)
        current.response.headers["Content-Type"] = "application/json"
        return options

    # -------------------------------------------------------------------------
    def _delete(self, r, **attr):
        """
            Delete a filter, responds to POST filter.json?delete=

            @param r: the S3Request
            @param attr: additional controller parameters
        """

        # Authorization, get pe_id
        auth = current.auth
        if auth.s3_logged_in():
            pe_id = current.auth.user.pe_id
        else:
            pe_id = None
        if not pe_id:
            r.unauthorised()

        # Read the source
        source = r.body
        source.seek(0)

        try:
            data = json.load(source)
        except ValueError:
            # Syntax error: no JSON data
            r.error(501, current.ERROR.BAD_SOURCE)

        # Try to find the record
        db = current.db
        s3db = current.s3db

        table = s3db.pr_filter
        record = None
        record_id = data.get("id")
        if record_id:
            query = (table.id == record_id) & (table.pe_id == pe_id)
            record = db(query).select(table.id, limitby=(0, 1)).first()
        if not record:
            r.error(501, current.ERROR.BAD_RECORD)

        resource = s3db.resource("pr_filter", id=record_id)
        success = resource.delete(format=r.representation)

        if not success:
            raise(400, resource.error)
        else:
            current.response.headers["Content-Type"] = "application/json"
            return current.xml.json_message(deleted=record_id)

    # -------------------------------------------------------------------------
    def _save(self, r, **attr):
        """
            Save a filter, responds to POST filter.json

            @param r: the S3Request
            @param attr: additional controller parameters
        """

        # Authorization, get pe_id
        auth = current.auth
        if auth.s3_logged_in():
            pe_id = current.auth.user.pe_id
        else:
            pe_id = None
        if not pe_id:
            r.unauthorised()

        # Read the source
        source = r.body
        source.seek(0)

        try:
            data = json.load(source)
        except ValueError:
            r.error(501, current.ERROR.BAD_SOURCE)

        # Try to find the record
        db = current.db
        s3db = current.s3db

        table = s3db.pr_filter
        record_id = data.get("id")
        record = None
        if record_id:
            query = (table.id == record_id) & (table.pe_id == pe_id)
            record = db(query).select(table.id, limitby=(0, 1)).first()
            if not record:
                r.error(404, current.ERROR.BAD_RECORD)

        # Build new record
        filter_data = {
            "pe_id": pe_id,
            "controller": r.controller,
            "function": r.function,
            "resource": self.resource.tablename,
            "deleted": False,
        }

        title = data.get("title")
        if title is not None:
            filter_data["title"] = title

        description = data.get("description")
        if description is not None:
            filter_data["description"] = description

        query = data.get("query")
        if query is not None:
            filter_data["query"] = json.dumps(query)

        url = data.get("url")
        if url is not None:
            filter_data["url"] = url

        # Store record
        onaccept = None
        form = Storage(vars=filter_data)
        if record:
            success = db(table.id == record_id).update(**filter_data)
            if success:
                current.audit("update", "pr", "filter", form, record_id, "json")
                info = {"updated": record_id}
                onaccept = s3db.get_config(table, "update_onaccept",
                           s3db.get_config(table, "onaccept"))
        else:
            success = table.insert(**filter_data)
            if success:
                record_id = success
                current.audit("create", "pr", "filter", form, record_id, "json")
                info = {"created": record_id}
                onaccept = s3db.get_config(table, "update_onaccept",
                           s3db.get_config(table, "onaccept"))

        if onaccept is not None:
            form.vars["id"] = record_id
            callback(onaccept, form)

        # Success/Error response
        xml = current.xml
        if success:
            msg = xml.json_message(**info)
        else:
            msg = xml.json_message(False, 400)
        current.response.headers["Content-Type"] = "application/json"
        return msg

    # -------------------------------------------------------------------------
    def _load(self, r, **attr):
        """
            Load filters

            GET filter.json or GET filter.json?load=<id>

            @param r: the S3Request
            @param attr: additional controller parameters
        """

        db = current.db
        table = current.s3db.pr_filter

        # Authorization, get pe_id
        auth = current.auth
        if auth.s3_logged_in():
            pe_id = current.auth.user.pe_id
        else:
            pe_id = None
        if not pe_id:
            r.unauthorized()

        # Build query
        query = (table.deleted != True) & \
                (table.resource == self.resource.tablename) & \
                (table.pe_id == pe_id)

        # Any particular filters?
        load = r.get_vars.get("load")
        if load:
            record_ids = [i for i in load.split(",") if i.isdigit()]
            if record_ids:
                if len(record_ids) > 1:
                    query &= table.id.belongs(record_ids)
                else:
                    query &= table.id == record_ids[0]
        else:
            record_ids = None

        # Retrieve filters
        rows = db(query).select(table.id,
                                table.title,
                                table.description,
                                table.query)

        # Pack filters
        filters = []
        for row in rows:
            filters.append({
                "id": row.id,
                "title": row.title,
                "description": row.description,
                "query": json.loads(row.query) if row.query else [],
            })

        # JSON response
        current.response.headers["Content-Type"] = "application/json"
        return json.dumps(filters, separators=SEPARATORS)

# =============================================================================
class S3FilterString(object):
    """
        Helper class to render a human-readable representation of a
        filter query, as representation method of JSON-serialized
        queries in saved filters.
    """

    def __init__(self, resource, query):
        """
            Constructor

            @param query: the URL query (list of key-value pairs or a
                          string with such a list in JSON)
        """

        if type(query) is not list:
            try:
                self.query = json.loads(query)
            except ValueError:
                self.query = []
        else:
            self.query = query

        get_vars = {}
        for k, v in self.query:
            if v is not None:
                key = resource.prefix_selector(k)
                if key in get_vars:
                    value = get_vars[key]
                    if type(value) is list:
                        value.append(v)
                    else:
                        get_vars[key] = [value, v]
                else:
                    get_vars[key] = v

        self.resource = resource
        self.get_vars = get_vars

    # -------------------------------------------------------------------------
    def represent(self):
        """ Render the query representation for the given resource """

        default = ""

        get_vars = self.get_vars
        resource = self.resource
        if not get_vars:
            return default
        else:
            queries = S3URLQuery.parse(resource, get_vars)

        # Get alternative field labels
        labels = {}
        get_config = resource.get_config
        prefix = resource.prefix_selector
        for config in ("list_fields", "notify_fields"):
            fields = get_config(config, set())
            for f in fields:
                if type(f) is tuple:
                    labels[prefix(f[1])] = f[0]

        # Iterate over the sub-queries
        render = self._render
        substrings = []
        append = substrings.append
        for alias, subqueries in queries.iteritems():

            for subquery in subqueries:
                s = render(resource, alias, subquery, labels=labels)
                if s:
                    append(s)

        if substrings:
            result = substrings[0]
            T = current.T
            for s in substrings[1:]:
                result = T("%s AND %s") % (result, s)
            return result
        else:
            return default

    # -------------------------------------------------------------------------
    @classmethod
    def _render(cls, resource, alias, query, invert=False, labels=None):
        """
            Recursively render a human-readable representation of a
            S3ResourceQuery.

            @param resource: the S3Resource
            @param query: the S3ResourceQuery
            @param invert: invert the query
        """

        T = current.T

        if not query:
            return None

        op = query.op

        l = query.left
        r = query.right
        render = lambda q, r=resource, a=alias, invert=False, labels=labels: \
                        cls._render(r, a, q, invert=invert, labels=labels)

        if op == query.AND:
            # Recurse AND
            l = render(l)
            r = render(r)
            if l is not None and r is not None:
                if invert:
                    result = T("NOT %s OR NOT %s") % (l, r)
                else:
                    result = T("%s AND %s") % (l, r)
            else:
                result = l if l is not None else r
        elif op == query.OR:
            # Recurse OR
            l = render(l)
            r = render(r)
            if l is not None and r is not None:
                if invert:
                    result = T("NOT %s AND NOT %s") % (l, r)
                else:
                    result = T("%s OR %s") % (l, r)
            else:
                result = l if l is not None else r
        elif op == query.NOT:
            # Recurse NOT
            result = render(l, invert=not invert)
        else:
            # Resolve the field selector against the resource
            try:
                rfield = l.resolve(resource)
            except (AttributeError, SyntaxError):
                return None

            # Convert the filter values into the field type
            try:
                values = cls._convert(rfield, r)
            except (TypeError, ValueError):
                values = r

            # Alias
            selector = l.name
            if labels and selector in labels:
                rfield.label = labels[selector]
            # @todo: for duplicate labels, show the table name
            #else:
                #tlabel = " ".join(s.capitalize() for s in rfield.tname.split("_")[1:])
                #rfield.label = "(%s) %s" % (tlabel, rfield.label)

            # Represent the values
            if values is None:
                values = T("None")
            else:
                list_type = rfield.ftype[:5] == "list:"
                renderer = rfield.represent
                if not callable(renderer):
                    renderer = lambda v: s3_unicode(v)
                if hasattr(renderer, "linkto"):
                    #linkto = renderer.linkto
                    renderer.linkto = None
                #else:
                #    #linkto = None

                is_list = type(values) is list

                try:
                    if is_list and hasattr(renderer, "bulk") and not list_type:
                        fvalues = renderer.bulk(values, list_type=False)
                        values = [fvalues[v] for v in values if v in fvalues]
                    elif list_type:
                        if is_list:
                            values = renderer(values)
                        else:
                            values = renderer([values])
                    else:
                        if is_list:
                            values = [renderer(v) for v in values]
                        else:
                            values = renderer(values)
                except:
                    values = s3_unicode(values)

            # Translate the query
            result = cls._translate_query(query, rfield, values, invert=invert)

        return result

    # -------------------------------------------------------------------------
    @classmethod
    def _convert(cls, rfield, value):
        """
            Convert a filter value according to the field type
            before representation

            @param rfield: the S3ResourceField
            @param value: the value
        """

        if value is None:
            return value

        ftype = rfield.ftype
        if ftype[:5] == "list:":
            if ftype[5:8] in ("int", "ref"):
                ftype = long
            else:
                ftype = unicode
        elif ftype == "id" or ftype [:9] == "reference":
            ftype = long
        elif ftype == "integer":
            ftype = int
        elif ftype == "date":
            ftype = datetime.date
        elif ftype == "time":
            ftype = datetime.time
        elif ftype == "datetime":
            ftype = datetime.datetime
        elif ftype == "double":
            ftype = float
        elif ftype == "boolean":
            ftype = bool
        else:
            ftype = unicode

        convert = S3TypeConverter.convert
        if type(value) is list:
            output = []
            append = output.append
            for v in value:
                try:
                    append(convert(ftype, v))
                except (TypeError, ValueError):
                    continue
        else:
            try:
                output = convert(ftype, value)
            except (TypeError, ValueError):
                output = None
        return output

    # -------------------------------------------------------------------------
    @classmethod
    def _translate_query(cls, query, rfield, values, invert=False):
        """
            Translate the filter query into human-readable language

            @param query: the S3ResourceQuery
            @param rfield: the S3ResourceField the query refers to
            @param values: the filter values
            @param invert: invert the operation
        """

        T = current.T

        # Value list templates
        vor = T("%s or %s")
        vand = T("%s and %s")

        # Operator templates
        otemplates = {
            query.LT: (query.GE, vand, "%(label)s < %(values)s"),
            query.LE: (query.GT, vand, "%(label)s <= %(values)s"),
            query.EQ: (query.NE, vor, T("%(label)s is %(values)s")),
            query.GE: (query.LT, vand, "%(label)s >= %(values)s"),
            query.GT: (query.LE, vand, "%(label)s > %(values)s"),
            query.NE: (query.EQ, vor, T("%(label)s != %(values)s")),
            query.LIKE: ("notlike", vor, T("%(label)s like %(values)s")),
            query.BELONGS: (query.NE, vor, T("%(label)s = %(values)s")),
            query.CONTAINS: ("notall", vand, T("%(label)s contains %(values)s")),
            query.ANYOF: ("notany", vor, T("%(label)s contains any of %(values)s")),
            "notall": (query.CONTAINS, vand, T("%(label)s does not contain %(values)s")),
            "notany": (query.ANYOF, vor, T("%(label)s does not contain %(values)s")),
            "notlike": (query.LIKE, vor, T("%(label)s not like %(values)s"))
        }

        # Quote values as necessary
        ftype = rfield.ftype
        if ftype in ("string", "text") or \
           ftype[:9] == "reference" or \
           ftype[:5] == "list:" and ftype[5:8] in ("str", "ref"):
            if type(values) is list:
                values = ['"%s"' % v for v in values]
            elif values is not None:
                values = '"%s"' % values
            else:
                values = current.messages["NONE"]

        # Render value list template
        def render_values(template=None, values=None):
            if not template or type(values) is not list:
                return str(values)
            elif not values:
                return "()"
            elif len(values) == 1:
                return values[0]
            else:
                return template % (", ".join(values[:-1]), values[-1])

        # Render the operator template
        op = query.op
        if op in otemplates:
            inversion, vtemplate, otemplate = otemplates[op]
            if invert:
                inversion, vtemplate, otemplate = otemplates[inversion]
            return otemplate % dict(label=rfield.label,
                                    values=render_values(vtemplate, values))
        else:
            # Fallback to simple representation
            # FIXME: resource not defined here!
            return query.represent(resource)

# END =========================================================================
