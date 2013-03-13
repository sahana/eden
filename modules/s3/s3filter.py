# -*- coding: utf-8 -*-

""" Framework for filtered REST requests

    @copyright: 2013 (c) Sahana Software Foundation
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

#import datetime
import re
#import string

try:
    import json # try stdlib (Python 2.6)
except ImportError:
    try:
        import simplejson as json # try external module
    except:
        import gluon.contrib.simplejson as json # fallback to pure-Python module

from gluon import *
#from gluon.html import BUTTON
#from gluon.serializers import json as jsons
from gluon.sqlhtml import MultipleOptionsWidget
from gluon.storage import Storage

from gluon.contrib.simplejson.ordered_dict import OrderedDict

#from s3crud import S3CRUD
from s3rest import S3Method
#from s3data import S3DataTable
#from s3export import S3Exporter
#from s3navigation import s3_search_tabs
#from s3resource import S3FieldSelector, S3Resource, S3ResourceField, S3URLQuery
from s3resource import S3ResourceField, S3URLQuery
#from s3utils import s3_get_foreign_key, s3_unicode, S3DateTime
from s3utils import s3_unicode
from s3validators import *
from s3widgets import S3DateTimeWidget, S3MultiSelectWidget, S3OrganisationHierarchyWidget, s3_grouped_checkboxes_widget

#MAX_RESULTS = 1000
#MAX_SEARCH_RESULTS = 200

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

            @param selector: the selector(s) for the field(s) to filter by
            @param attr: configuration options for this widget
        """

        self.field = field

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
    def __call__(self, resource, get_vars=None):
        """
            Entry point for the form builder

            @param resource: the S3Resource to render with widget for
            @param get_vars: the GET vars (URL query vars) to prepopulate
                             the widget
        """

        _class = self._class

        # Construct name and id for the widget
        attr = self.attr
        if "_name" not in attr:
            flist = self.field
            if type(flist) is not list:
                flist = [flist]
            colnames = [S3ResourceField(resource, f).colname for f in flist]
            name = "%s-%s-%s" % (resource.alias, "-".join(colnames), _class)
            attr["_name"] = name.replace(".", "_")
        if "_id" not in attr:
            attr["_id"] = attr["_name"]

        # Extract the URL values to populate the widget
        variable = self.variable(resource, get_vars)
        if type(variable) is list:
            values = Storage()
            for k in variable:
                values[k] = self._values(get_vars, k)
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
    @staticmethod
    def _prefix(selector):
        """
            Helper method to prefix an unprefixed field selector

            @param alias: the resource alias to use as prefix
            @param selector: the field selector

            @return: the prefixed selector
        """

        if "." not in selector.split("$", 1)[0]:
            return "~.%s" % selector
        else:
            return selector

    # -------------------------------------------------------------------------
    @classmethod
    def _selector(cls, resource, fields):
        """
            Helper method to generate a filter query selector for the
            given field(s) in the given resource.

            @param resource: the S3Resource
            @param fields: the field selectors (as strings)

            @return: the field label and the filter query selector, or None if none of the
                     field selectors could be resolved
        """

        prefix = cls._prefix
        label = None

        if not fields:
            return label, None
        if not isinstance(fields, (list, tuple)):
            fields = [fields]
        selectors = []
        for field in fields:
            try:
                rfield = S3ResourceField(resource, field)
            except (AttributeError, TypeError):
                continue
            if not label:
                label = rfield.label
            selectors.append(prefix(rfield.selector))
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

        selector = self.selector

        _variable = self._variable

        id = attr["_id"]
        for operator in self.operator:

            input_id = "%s-%s" % (id, operator)

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

            ie_append(current.T(input_labels[operator]) + ":")
            ie_append(input_box)

        return input_elements

# =============================================================================
class S3DateFilter(S3RangeFilter):
    """ Date Range Filter Widget """

    _class = "date-filter"

    # Class for visible input boxes.
    _input_class = "%s-%s" % (_class, "input")

    operator = ["ge", "le"]

    # Untranslated labels for individual input boxes.
    input_labels = {"ge": "Earliest", "le": "Latest"}

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

        rfield = S3ResourceField(resource, self.field)
        field = rfield.field
        if field is None:
            # S3DateTimeWidget doesn't support virtual fields
            dtformat = current.deployment_settings.get_L10n_date_format()
            field = Field(rfield.fname, "datetime",
                          requires = IS_DATE_IN_RANGE(format = dtformat))
            field._tablename = rfield.tname

        input_class = self._input_class
        input_labels = self.input_labels
        input_elements = DIV()

        selector = self.selector

        _variable = self._variable

        id = attr["_id"]
        input_elements = DIV()
        ie_append = input_elements.append
        for operator in self.operator:
            input_id = "%s-%s" % (id, operator)

            # Populate with the value, if given
            # if user has not set any of the limits, we get [] in values.
            variable = _variable(selector, operator)
            value = values.get(variable, None)
            if value not in [None, []]:
                if type(value) is list:
                    value = value[0]
            else:
                value = None

            picker = S3DateTimeWidget()(field,
                                        value,
                                        _name=input_id,
                                        _id=input_id,
                                        _class = self._input_class)

            ie_append(current.T(input_labels[operator]) + ":")
            ie_append(picker)

        return input_elements

# =============================================================================
class S3LocationFilter(S3FilterWidget):
    """ Hierarchical Location Filter Widget """

    _class = "location-filter"

    operator = "belongs"

    # -------------------------------------------------------------------------
    def widget(self, resource, values):
        """
            Render this widget as HTML helper object(s)

            @param resource: the resource
            @param values: the search values from the URL query
        """

        T = current.T

        EMPTY = T("None")

        attr = self.attr
        opts = self.opts

        # Which levels should we display?
        # Lookup the appropriate labels from the GIS configuration
        hierarchy = current.gis.get_location_hierarchy()
        levels = OrderedDict()
        if "levels" in opts:
            for level in opts["levels"]:
                levels[level] = hierarchy.get(level, level)
        else:
            # @ToDo: Do this dynamically from the data?
            for level in hierarchy:
                levels[level] = hierarchy.get(level, level)
        # Pass to data_element
        self.levels = levels

        if "label" not in opts:
            opts["label"] = T("Filter by Location")

        # Resolve the field selector
        field_name = self.field
        rfield = S3ResourceField(resource, field_name)
        field = rfield.field
        colname = rfield.colname
        field_type = "reference gis_location"
        fields = [field_name]
        fappend = fields.append
        for level in levels:
            fappend("%s$%s" % (field_name, level))

        # Find the options
        rows = resource.select(fields=fields,
                               start=None,
                               limit=None,
                               virtual=False)

        # No options?
        if not rows:
            msg = attr.get("_no_opts", T("No options available"))
            return SPAN(msg, _class="no-options-available")

        # Intialise Options Storage & Hierarchy
        hierarchy = {}
        first = True
        for level in levels:
            if first:
                hierarchy[level] = {}
                _level = level
                first = False
            levels[level] = {"label" : levels[level],
                             "options" : [],
                             }

        # Store the options & hierarchy
        for row in rows:
            if "gis_location" in row:
                _row = row.gis_location
                parent = None
                grandparent = None
                greatgrandparent = None
                greatgreatgrandparent = None
                greatgreatgreatgrandparent = None
                i = 0
                for level in levels:
                    v = _row[level]
                    if v:
                        if v not in levels[level]["options"]:
                            levels[level]["options"].append(v)
                        if i == 0:
                            if v not in hierarchy[_level]:
                                hierarchy[_level][v] = {}
                            parent = v
                        elif i == 1:
                            if v not in hierarchy[_level][parent]:
                                hierarchy[_level][parent][v] = {}
                            grandparent = parent
                            parent = v
                        elif i == 2:
                            if v not in hierarchy[_level][grandparent][parent]:
                                hierarchy[_level][grandparent][parent][v] = {}
                            greatgrandparent = grandparent
                            grandparent = parent
                            parent = v
                        elif i == 3:
                            if v not in hierarchy[_level][greatgrandparent][grandparent][parent]:
                                hierarchy[_level][greatgrandparent][grandparent][parent][v] = {}
                            greatgreatgrandparent = greatgrandparent
                            greatgrandparent = grandparent
                            grandparent = parent
                            parent = v
                    i += 1

        # Construct HTML classes for the widget
        if "_class" in attr and attr["_class"]:
            _class = "%s %s %s" % (attr["_class"],
                                   "s3-checkboxes-widget",
                                   self._class)
        else:
            _class = "%s %s" % ("s3-checkboxes-widget", self._class)

        attr["_class"] = _class
        attr["cols"] = opts["cols"]

        widgets = []
        w_append = widgets.append
        base_id = attr["_id"]
        base_name = attr["_name"]
        operator = self.operator
        # @ToDo: Hide dropdowns other than first
        if opts.widget == "multiselect":
            # Multiselect Dropdown with Checkboxes
            _class = attr.get("_class", None)
            if _class:
                if "multiselect-filter-widget" not in _class:
                    attr["_class"] = "%s multiselect-filter-widget" % _class
            else:
                attr["_class"] = "multiselect-filter-widget"
            for level in levels:
                # Dummy field
                name = "%s-%s" % (base_name, level)
                options = levels[level]["options"]
                options.sort()
                dummy_field = Storage(name=name,
                                      type=field_type,
                                      requires=IS_IN_SET(options,
                                                         multiple=True))
                # Unique ID/name
                attr["_id"] = "%s-%s" % (base_id, level)
                attr["_name"] = name
                # Find relevant values
                _values = values["~.%s$%s__%s" % (field_name, level, operator)]
                w = S3MultiSelectWidget(filter = opts.get("filter", False),
                                        header = opts.get("header", False),
                                        selectedList = opts.get("selectedList", 3),
                                        noneSelectedText = "Select %s" % levels[level]["label"])
                widget = w(dummy_field, _values, **attr)
                w_append(widget)
        else:
            # Grouped Checkboxes
            for level in levels:
                # Dummy field
                name = "%s-%s" % (base_name, level)
                options = levels[level]["options"]
                options.sort()
                dummy_field = Storage(name=name,
                                      type=field_type,
                                      requires=IS_IN_SET(options,
                                                         multiple=True))
                # Unique ID/name
                attr["_id"] = "%s-%s" % (base_id, level)
                attr["_name"] = name
                # Find relevant values
                _values = values["~.%s$%s__%s" % (field_name, level, operator)]
                w_append(s3_grouped_checkboxes_widget(dummy_field,
                                                      _values,
                                                      **attr))

        # Reset for data_element
        attr["_id"] = base_id

        # Inject the Location Hierarchy
        hierarchy = "S3.location_filter_hierarchy=%s" % json.dumps(hierarchy)
        current.response.s3.js_global.append(hierarchy)

        # Render the filter widget
        return TAG[""](*widgets)

    # -------------------------------------------------------------------------
    def data_element(self, variable):
        """
            Prototype method to construct the hidden element that holds the
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
        label = None

        if "levels" in self.opts:
            levels = self.opts.levels
        else:
            levels = current.gis.hierarchy_level_keys
        fields = ["%s$%s" % (fields, level) for level in levels]
        selectors = []
        for field in fields:
            try:
                rfield = S3ResourceField(resource, field)
            except (AttributeError, TypeError):
                continue
            if not label:
                label = rfield.label
            selectors.append(prefix(rfield.selector))
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
class S3MapFilter(S3FilterWidget):
    """ Map Location Filter Widget """

    _class = "map-filter"

# =============================================================================
class S3OptionsFilter(S3FilterWidget):

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

        T = current.T

        EMPTY = T("None")

        attr = self.attr
        opts = self.opts

        # Resolve the field selector
        field_name = self.field
        if (isinstance(field_name, (list, tuple))):
            field_name = field_name[0]
        rfield = S3ResourceField(resource, field_name)
        field = rfield.field
        colname = rfield.colname
        field_type = rfield.ftype

        # Find the options ----------------------------------------------------

        if opts.options is not None:
            # Custom dict of options {value: label} or a callable
            # returning such a dict:
            options = opts.options
            if callable(options):
                options = options()
            opt_values = options.keys()

        else:
            # Determine the options from the field type
            options = None
            if field_type == "boolean":
                opt_values = (True, False)
            else:
                multiple = field_type[:5] == "list:"
                groupby = field if field and not multiple else None
                virtual = field is None
                rows = resource.select(fields=[field_name],
                                       start=None,
                                       limit=None,
                                       orderby=field,
                                       groupby=groupby,
                                       virtual=virtual)
                opt_values = []
                if rows:
                    opt_extend = opt_values.extend
                    opt_append = opt_values.append
                    if multiple:
                        for row in rows:
                            vals = row[colname]
                            if vals:
                                opt_extend([v for v in vals
                                            if v not in opt_values])
                    else:
                        for row in rows:
                            v = row[colname]
                            if v not in opt_values:
                                opt_append(v)

        # No options?
        if len(opt_values) < 1 or \
           len(opt_values) == 1 and not opt_values[0]:
            msg = attr.get("_no_opts", T("No options available"))
            return SPAN(msg, _class="no-options-available")

        # Represent the options -----------------------------------------------

        opt_list = []

        # Custom represent? (otherwise fall back to field represent)
        represent = opts.represent
        if not represent or field_type[:9] != "reference":
            represent = field.represent

        if options is not None:
            # Custom dict of {value:label} => use this label
            opt_list = options.items()

        elif callable(represent):
            # Callable representation function:

            if hasattr(represent, "bulk"):
                # S3Represent => use bulk option
                opt_dict = represent.bulk(opt_values,
                                          list_type=False,
                                          show_link=False)
                if None in opt_values:
                    opt_dict[None] = EMPTY
                elif None in opt_dict:
                    del opt_dict[None]
                if "" in opt_values:
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
                opt_list = map(repr_opt, opt_values)

        elif isinstance(represent, str) and field_type[:9] == "reference":
            # Represent is a string template to be fed from the
            # referenced record

            # Get the referenced table
            db = current.db
            ktable = db[field_type[10:]]

            k_id = ktable._id.name

            # Get the fields referenced by the string template
            fieldnames = [k_id]
            fieldnames += re.findall("%\(([a-zA-Z0-9_]*)\)s", represent)
            represent_fields = [ktable[fieldname] for fieldname in fieldnames]

            # Get the referenced records
            query = (ktable.id.belongs([k for k in opt_values
                                              if str(k).isdigit()])) & \
                    (ktable.deleted == False)
            rows = db(query).select(*represent_fields).as_dict(key=k_id)

            # Run all referenced records against the format string
            opt_list = []
            ol_append = opt_list.append
            for opt_value in opt_values:
                if opt_value in rows:
                    opt_represent = represent % rows[opt_value]
                    if opt_represent:
                        ol_append((opt_value, opt_represent))

        else:
            # Straight string representations of the values (fallback)
            opt_list = [(opt_value, s3_unicode(opt_value))
                        for opt_value in opt_values if opt_value]

        # Sort the options
        options = OrderedDict([("NONE" if o is None else o, v)
                               for o, v in opt_list])

        # Construct HTML classes for the widget
        if "_class" in attr and attr["_class"]:
            _class = "%s %s %s" % (attr["_class"],
                                   "s3-checkboxes-widget",
                                   self._class)
        else:
            _class = "%s %s" % ("s3-checkboxes-widget", self._class)

        attr["_class"] = _class
        attr["cols"] = opts["cols"]

        # Dummy field
        name = attr["_name"]
        dummy_field = Storage(name=name,
                              type=field_type,
                              requires=IS_IN_SET(options, multiple=True))

        # Any-All-Option : for many-to-many fields the user can search for
        # records containing all the options or any of the options:
        if len(options) > 1 and field_type[:4] == "list":
            if self.operator == "anyof":
                filter_type = "any"
            else:
                filter_type = "all"
                if self.operator == "belongs":
                    self.operator = "contains"

            any_all = DIV(
                T("Filter type "),
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
                _class="s3-checkboxes-widget-filter"
            )
        else:
            any_all = ""

        if opts.widget in ("multiselect", "multiselect-bootstrap"):
            # Multiselect Dropdown with Checkboxes
            if opts.widget == "multiselect-bootstrap":
                script = "/%s/static/scripts/bootstrap-multiselect.js" % \
                    current.request.application
                scripts = current.response.s3.scripts
                if script not in scripts:
                    scripts.append(script)
                widget = MultipleOptionsWidget.widget(dummy_field,
                                                      values,
                                                      **attr)
                widget.add_class("multiselect-filter-bootstrap")
            else:
                _class = attr.get("_class", None)
                if _class:
                    if "multiselect-filter-widget" not in _class:
                        attr["_class"] = "%s multiselect-filter-widget" % _class
                else:
                    attr["_class"] = "multiselect-filter-widget"
                w = S3MultiSelectWidget(filter = opts.get("filter", False),
                                        header = opts.get("header", False),
                                        selectedList = opts.get("selectedList", 3),
                                        )
                widget = w(dummy_field, values, **attr)
        else:
            # Grouped Checkboxes
            widget = s3_grouped_checkboxes_widget(dummy_field,
                                                  values,
                                                  **attr)

        # Render the filter widget
        return TAG[""](any_all, widget)

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
    def html(self, resource, get_vars=None, target=None):
        """
            Render this filter form as HTML

            @param resource: the S3Resource
            @param get_vars: the request GET vars (URL query dict)
        """

        formstyle = self.opts.get("formstyle", None)
        if not formstyle:
            formstyle = self._formstyle

        rows = []
        rappend = rows.append
        for f in self.widgets:
            widget = f(resource, get_vars)
            label = f.opts["label"]
            comment = f.opts["comment"]
            widget_id = f.attr["_id"]
            if widget_id:
                row_id = "%s__row" % widget_id
                label_id = "%s__label" % widget_id
            else:
                row_id = None
                label_id = None
            if label:
                label = LABEL("%s :" % label, _id=label_id, _for=widget_id)
            else:
                label = ""
            if not comment:
                comment = ""
            rappend(formstyle(row_id, label, widget, comment))

        submit = self.opts.get("submit", False)
        if submit:
            _class = "filter-submit"
            ajax = self.opts.get("ajax", False)
            if ajax:
                _class = "%s filter-ajax" % _class
            if submit is True:
                label = current.T("Search")
            elif isinstance(submit, (list, tuple)):
                label = submit[0]
                _class = "%s %s" % (submit[1], _class)
            else:
                label = submit
            url = self.opts.get("url", URL(vars={}))
            submit = TAG[""](
                        INPUT(_type="button",
                              _value=label,
                              _class=_class),
                        INPUT(_type="hidden",
                              _class="filter-submit-url",
                              _value=url))

            if ajax and target:
                submit.append(INPUT(_type="hidden",
                                    _class="filter-submit-target",
                                    _value=target))

            rappend(formstyle(None, "", submit, ""))

        form = FORM(TABLE(TBODY(rows)), **self.attr)
        return form

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
    def _formstyle(row_id, label, widget, comment):
        """
            Default formstyle for search forms

            @param row_id: HTML id for the row
            @param label: the label
            @param widget: the form widget
            @param comment: the comment
        """

        row = TR(TD(label, _class="w2p_fl"), TD(widget), _id=row_id)

        if comment:
            row.append(TD(DIV(_class="tooltip",
                              _title="%s|%s" % (label, comment)),
                          _class="w2p_fc"))
        return row

# =============================================================================
class S3Filter(S3Method):
    """ Back-end for filter form updates """

    def apply_method(self, r, **attr):
        """
            Entry point for REST interface

            @param r: the S3Request
            @param attr: additional controller parameters
        """

        representation = r.representation
        if representation == "html":
            return self._form(r, **attr)

        elif representation == "json":
            # Return the filter options as JSON
            return self._options(r, **attr)

        else:
            r.error(501, current.manager.ERROR.BAD_FORMAT)

    # -------------------------------------------------------------------------
    def _form(self, r, **attr):
        """
            Get the filter form for the target resource as HTML snippet

            @param r: the S3Request
            @param attr: additional controller parameters
        """
        
        r.error(501, current.manager.ERROR.NOT_IMPLEMENTED)

    # -------------------------------------------------------------------------
    def _options(self, r, **attr):
        """
            Get the updated options for the filter form for the target
            resource as JSON

            @param r: the S3Request
            @param attr: additional controller parameters
        """


        resource = self.resource
        get_config = resource.get_config
    
        options = {}

        # Filter-form
        filter_widgets = get_config("filter_widgets", None)
        if filter_widgets:
            fresource = current.s3db.resource(resource.tablename)
            
            for widget in filter_widgets:
                if hasattr(widget, "ajax_options"):
                    opts = widget.ajax_options(fresource,
                                               r.get_vars)
                    if opts and isinstance(opts, dict):
                        options.update(opts)

            target = "datalist"
            output["list_filter_form"] = filter_form.html(fresource,
                                                            r.get_vars,
                                                            target=target)

        options = json.dumps(options)
        current.response.headers["Content-Type"] = "application/json"
        return options
        
# END =========================================================================
