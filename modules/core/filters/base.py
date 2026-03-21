"""
    Interactive filters

    Copyright: 2013-2022 (c) Sahana Software Foundation

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

__all__ = ("FilterForm",
           "FilterWidget",
           "get_filter_options",
           "set_default_filter",
           )

import json

from collections import OrderedDict

from gluon import current, URL, A, DIV, FORM, INPUT, LABEL, OPTION, SELECT, \
                  SPAN, TABLE, TAG, TBODY

from gluon.storage import Storage

from ..resource import S3ResourceField, S3URLQuery
from ..tools import JSONSEPARATORS, s3_str
from ..ui import ICON

DEFAULT = lambda: None

# =============================================================================
class FilterWidget:
    """ Filter widget for interactive search forms (base class) """

    css_base = "generic-filter"

    operator = None

    alternatives = None

    def __init__(self, field=None, **attr):
        """
            Args:
                field: the selector(s) for the field(s) to filter by
                attr: configuration options for this widget

            Keyword Args:
                label: label for the widget
                comment: comment for the widget
                hidden: render widget initially hidden (="advanced" option)

            - additional keywords see subclasses
        """

        self.field = field
        self.alias = None

        attributes = Storage()
        options = Storage()
        for k, v in attr.items():
            if k[0] == "_":
                attributes[k] = v
            else:
                options[k] = v
        self.attr = attributes
        self.opts = options

        self.selector = None
        self.values = Storage()

    # -------------------------------------------------------------------------
    def widget(self, resource, values):
        """
            Prototype method to render this widget as an instance of
            a web2py HTML helper class, to be implemented by subclasses.

            Args:
                resource: the CRUDResource to render with widget for
                values: the values for this widget from the URL query
        """

        raise NotImplementedError

    # -------------------------------------------------------------------------
    def variable(self, resource, get_vars=None):
        """
            Prototype method to generate the name for the URL query variable
            for this widget, can be overwritten in subclasses.

            Args:
                resource: the resource

            Returns:
                the URL query variable name (or list of variable names if
                there are multiple operators)
        """

        opts = self.opts

        if "selector" in opts:
            # Override selector
            label, selector = None, opts["selector"]
        else:
            label, selector = self._selector(resource, self.field)
        self.selector = selector

        if not selector:
            return None

        if self.alternatives and get_vars is not None:
            # Get the actual operator from get_vars
            operator = self._operator(get_vars, selector)
            if operator:
                self.operator = operator

        if "label" not in self.opts:
            self.opts["label"] = label

        return self._variable(selector, self.operator)

    # -------------------------------------------------------------------------
    def data_element(self, variable):
        """
            Prototype method to construct the hidden element that holds the
            URL query term corresponding to an input element in the widget.

            Args:
                variable: the URL query variable
        """

        if isinstance(variable, list):
            variable = "&".join(variable)

        return INPUT(_type = "hidden",
                     _id = "%s-data" % self.attr["_id"],
                     _class = "filter-widget-data %s-data" % self.css_base,
                     _value = variable,
                     )

    # -------------------------------------------------------------------------
    def __call__(self, resource, get_vars=None, alias=None):
        """
            Entry point for the form builder

            Args:
                resource: the CRUDResource to render the widget for
                get_vars: the GET vars (URL query vars) to prepopulate
                          the widget
                alias: the resource alias to use
        """

        self.alias = alias

        # Initialize the widget attributes
        self._attr(resource)

        # Extract the URL values to populate the widget
        variable = self.variable(resource, get_vars)

        defaults = {}
        for k, v in self.values.items():
            selector = self._prefix(k)
            defaults[selector] = v

        if isinstance(variable, list):
            values = Storage()
            for k in variable:
                if k in defaults:
                    values[k] = defaults[k]
                else:
                    values[k] = self._values(get_vars, k)
        else:
            if variable in defaults:
                values = defaults[variable]
            else:
                values = self._values(get_vars, variable)

        # Construct and populate the widget
        widget = self.widget(resource, values)

        # Recompute variable in case operator got changed in widget()
        if self.alternatives:
            variable = self._variable(self.selector, self.operator)

        # Construct the hidden data element
        data = self.data_element(variable)

        if isinstance(data, list):
            data.append(widget)
        else:
            data = [data, widget]
        return TAG[""](*data)

    # -------------------------------------------------------------------------
    # Helper methods
    #
    def _attr(self, resource):
        """
            Initialize and return the HTML attributes for this widget

            Args:
                resource: the CRUDResource to be filtered
        """

        attr = self.attr

        if "_name" not in attr:
            if not resource:
                raise SyntaxError("%s: _name parameter required when rendered without resource." % \
                                  self.__class__.__name__)
            flist = self.field
            if not isinstance(flist, (list, tuple)):
                flist = [flist]
            colnames = []
            for f in flist:
                rfield = S3ResourceField(resource, f)
                colname = rfield.colname
                if colname:
                    colnames.append(colname)
                else:
                    colnames.append(rfield.fname)
            name = "%s-%s-%s" % (resource.alias, "-".join(colnames), self.css_base)
            attr["_name"] = name.replace(".", "_")

        if "_id" not in attr:
            attr["_id"] = attr["_name"]

        return attr

    # -------------------------------------------------------------------------
    @classmethod
    def _operator(cls, get_vars, selector):
        """
            Helper method to get the operators from the URL query

            Args:
                get_vars: the GET vars (a dict)
                selector: field selector

            Returns:
                query operator - None, str or list
        """

        variables = ["%s__%s" % (selector, op) for op in cls.alternatives]
        slen = len(selector) + 2

        operators = [k[slen:] for k in get_vars if k in variables]
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

            Args:
                alias: the resource alias to use as prefix
                selector: the field selector

            Returns:
                the prefixed selector
        """

        alias = self.alias
        items = selector.split("$", 0)
        head = items[0]
        if "." in head:
            if alias not in (None, "~"):
                prefix, key = head.split(".", 1)
                if prefix == "~":
                    prefix = alias
                elif prefix != alias:
                    prefix = "%s.%s" % (alias, prefix)
                items[0] = "%s.%s" % (prefix, key)
                selector = "$".join(items)
        else:
            if alias is None:
                alias = "~"
            selector = "%s.%s" % (alias, selector)
        return selector

    # -------------------------------------------------------------------------
    def _selector(self, resource, fields):
        """
            Helper method to generate a filter query selector for the
            given field(s) in the given resource.

            Args:
                resource: the CRUDResource
                fields: the field selectors (as strings)

            Returns:
                the field label and the filter query selector, or None
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

            Args:
                get_vars: the GET vars (a dict)
                variable: the name of the query variable

            Returns:
                a list of values
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

            Args:
                selector: the selector
                operator: the operator (or tuple/list of operators)

            Returns:
                the URL query variable name (or list of variable names)
        """

        if isinstance(operator, (tuple, list)):
            return [cls._variable(selector, o) for o in operator]
        elif operator:
            return "%s__%s" % (selector, operator)
        else:
            return selector

# =============================================================================
class FilterForm:
    """ Filter form builder """

    def __init__(self, widgets, **attr):
        """
            Args:
                widgets: the widgets (as list)
                attr: HTML attributes for this form
        """

        self.widgets = widgets

        attributes = Storage()
        options = Storage()
        for k, v in attr.items():
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

            Args:
                resource: the CRUDResource
                get_vars: the request GET vars (URL query dict)
                target: the HTML element ID of the target object for
                        this filter form (e.g. a datatable)
                alias: the resource alias to use in widgets

            Returns:
                a FORM
        """

        attr = self.attr
        form_id = attr.get("_id")
        if not form_id:
            form_id = "filter-form"
        attr["_id"] = form_id

        # Prevent issues with Webkit-based browsers & Back buttons
        attr["_autocomplete"] = "off"

        opts_get = self.opts.get
        settings = current.deployment_settings

        # Form style
        formstyle = opts_get("formstyle", None)
        if not formstyle:
            formstyle = settings.get_ui_filter_formstyle()

        # Filter widgets
        rows = self._render_widgets(resource,
                                    get_vars = get_vars or {},
                                    alias = alias,
                                    formstyle = formstyle,
                                    )

        # Filter Manager (load/apply/save filters)
        fm = settings.get_search_filter_manager()
        if fm and opts_get("filter_manager", resource is not None):
            filter_manager = self._render_filters(resource, form_id)
        else:
            filter_manager = None

        # Other filter form controls
        controls = self._render_controls(resource, filter_manager)
        if controls:
            rows.append(formstyle(None, "", controls, ""))

        # Submit elements
        ajax = opts_get("ajax", False)
        submit = opts_get("submit", False)
        if submit:
            # Auto-submit?
            auto_submit = settings.get_ui_filter_auto_submit()
            if auto_submit and opts_get("auto_submit", True):
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
            submit_button = INPUT(_type = "button",
                                  _value = label,
                                  _class = "filter-submit",
                                  )
            if _class:
                submit_button.add_class(_class)

            # Where to request filtered data from:
            submit_url = opts_get("url", URL(vars={}))

            # Where to request updated options from:
            ajax_url = opts_get("ajaxurl", URL(args=["filter.options"], vars={}))

            # Submit row elements
            submit = TAG[""](submit_button,
                             INPUT(_type = "hidden",
                                   _class = "filter-ajax-url",
                                   _value = ajax_url,
                                   ),
                             INPUT(_type = "hidden",
                                   _class = "filter-submit-url",
                                   _value = submit_url,
                                   ))
            if ajax and target:
                submit.append(INPUT(_type = "hidden",
                                    _class = "filter-submit-target",
                                    _value = target,
                                    ))

            # Append submit row
            submit_row = formstyle(None, "", submit, "")
            if auto_submit and hasattr(submit_row, "add_class"):
                submit_row.add_class("hide")
            rows.append(submit_row)

        # Filter Manager (load/apply/save filters)
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

            Args:
                resource: the CRUDResource
                get_vars: the request GET vars (URL query dict)
                alias: the resource alias to use in widgets
        """

        attr = self.attr
        form_id = attr.get("_id")
        if not form_id:
            form_id = "filter-form"

        opts_get = self.opts.get
        settings = current.deployment_settings

        formstyle = self.opts.get("formstyle", None)
        if not formstyle:
            formstyle = current.deployment_settings.get_ui_filter_formstyle()

        rows = self._render_widgets(resource,
                                    get_vars = get_vars,
                                    alias = alias,
                                    formstyle = formstyle,
                                    )

        # Filter Manager
        fm = settings.get_search_filter_manager()
        if fm and opts_get("filter_manager", resource is not None):
            filter_manager = self._render_filters(resource, form_id)
        else:
            filter_manager = None

        controls = self._render_controls(resource, filter_manager)
        if controls:
            rows.append(formstyle(None, "", controls, ""))

        # Filter Manager (load/apply/save filters)
        if filter_manager:
            fmrow = formstyle(None, "", filter_manager, "")
            if hasattr(fmrow, "add_class"):
                fmrow.add_class("hide filter-manager-row")
            rows.append(fmrow)

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
        else:
            fields = ""

        return fields

    # -------------------------------------------------------------------------
    def _render_controls(self, resource, filter_manager=None):
        """
            Render optional additional filter form controls: advanced
            options toggle, clear filters.

            Args:
                resource: the resource
                filter_manager: the filter manager widget
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
                              _class = "filter-advanced-label",
                              ),
                         ICON("down"),
                         ICON("up", _style = "display:none"),
                         _class = _class,
                         )
            controls.append(advanced)

        clear = opts.get("clear", True)
        if clear:
            _class = "filter-clear"
            if clear is True:
                label = T("Clear Filter")
            elif isinstance(clear, (list, tuple)):
                label = clear[0]
                _class = "%s %s" % (clear[1], _class)
            else:
                label = clear
            clear = A(label, _class=_class)
            clear.add_class("action-lnk")
            controls.append(clear)

        if filter_manager:
            show_fm = A(T("Saved Filters"),
                        _class = "show-filter-manager action-lnk",
                        )
            controls.append(show_fm)

        return DIV(controls, _class="filter-controls") if controls else None

    # -------------------------------------------------------------------------
    def _render_widgets(self,
                        resource,
                        get_vars=None,
                        alias=None,
                        formstyle=None):
        """
            Render the filter widgets

            Args:
                resource: the CRUDResource
                get_vars: the request GET vars (URL query dict)
                alias: the resource alias to use in widgets
                formstyle: the formstyle to use

            Returns:
                a list of form rows
        """

        rows = []
        rappend = rows.append
        advanced = False
        for f in self.widgets:
            if not f:
                continue
            widget = f(resource, get_vars, alias=alias)
            widget_opts = f.opts
            label = widget_opts["label"]
            comment = widget_opts["comment"]
            hidden = widget_opts["hidden"]
            widget_formstyle = widget_opts.get("formstyle", formstyle)
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
            elif label is not False:
                label = ""
            if not comment:
                comment = ""
            formrow = widget_formstyle(row_id, label, widget, comment, hidden=hidden)
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
                self.opts["advanced"] = \
                    resource.get_config("filter_advanced", True)
            else:
                self.opts["advanced"] = True
        return rows

    # -------------------------------------------------------------------------
    def _render_filters(self, resource, form_id):
        """
            Render a filter manager widget

            Args:
                resource: the resource

            Returns:
                the widget
        """

        SELECT_FILTER = current.T("Saved Filters")

        ajaxurl = self.opts.get("saveurl")
        if not ajaxurl:
            ajaxurl = URL(args = ["filter.json"],
                          vars = current.request.get_vars,
                          )

        # Current user
        auth = current.auth
        user = auth.user
        pe_id = user.pe_id if user and auth.s3_logged_in() else None
        if not pe_id:
            return None

        table = current.s3db.usr_filter
        query = (table.deleted == False) & \
                (table.pe_id == pe_id)

        if resource:
            query &= (table.resource == resource.tablename)
        else:
            query &= (table.resource == None)

        rows = current.db(query).select(table._id,
                                        table.title,
                                        table.query,
                                        orderby = table.title
                                        )

        options = [OPTION(SELECT_FILTER,
                          _value = "",
                          _class = "filter-manager-prompt",
                          _disabled = "disabled",
                          )]
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
                            _id = widget_id,
                            _class = "filter-manager-widget",
                            ),
                     _class = "filter-manager-container",
                     )

        # JSON-serializable translator
        T = current.T
        t_ = lambda s: s3_str(T(s))

        # Configure the widget
        settings = current.deployment_settings
        config = {# Filters and Ajax URL
                  "filters": filters,
                  "ajaxURL": ajaxurl,

                  # Workflow Options
                  "allowDelete": settings.get_search_filter_manager_allow_delete(),

                  # Tooltips for action icons/buttons
                  "createTooltip": t_("Save current options as new filter"),
                  "loadTooltip": t_("Load filter"),
                  "saveTooltip": t_("Update saved filter"),
                  "deleteTooltip": t_("Delete saved filter"),

                  # Hints
                  "titleHint": t_("Enter a title..."),
                  "selectHint": s3_str(SELECT_FILTER),
                  "emptyHint": t_("No saved filters"),

                  # Confirm update + confirmation text
                  "confirmUpdate": t_("Update this filter?"),
                  "confirmDelete": t_("Delete this filter?"),
                  }

        # Render actions as buttons with text if configured, otherwise
        # they will appear as empty DIVs with classes for CSS icons
        create_text = settings.get_search_filter_manager_save()
        if create_text:
            config["createText"] = t_(create_text)
        update_text = settings.get_search_filter_manager_update()
        if update_text:
            config["saveText"] = t_(update_text)
        delete_text = settings.get_search_filter_manager_delete()
        if delete_text:
            config["deleteText"] = t_(delete_text)
        load_text = settings.get_search_filter_manager_load()
        if load_text:
            config["loadText"] = t_(load_text)

        script = '''$("#%s").filtermanager(%s)''' % \
                    (widget_id,
                     json.dumps(config, separators=JSONSEPARATORS))

        current.response.s3.jquery_ready.append(script)

        return widget

    # -------------------------------------------------------------------------
    @staticmethod
    def apply_filter_defaults(request, resource):
        """
            Add default filters to resource, to be called on a multi-record
            view when a filter form is rendered the first time and before
            the view elements get processed; can be overridden in request
            URL with ?search=xxx (e.g. $search=query)

            Args:
                request: the request
                resource: the resource

            Returns:
                dict with default filters (URL vars)
        """

        default_filters = {}

        if request.suppress_default_filters:
            # Skip default filters (e.g. session filter, or links in reports)
            return default_filters

        get_vars = request.get_vars

        # Do we have filter defaults for this table?
        tablename = resource.tablename
        filter_defaults = current.response.s3.get("filter_defaults")
        if filter_defaults:
            table_defaults = filter_defaults.get(tablename)
        else:
            table_defaults = None

        filter_widgets = resource.get_config("filter_widgets")
        for filter_widget in filter_widgets:

            if not filter_widget:
                continue

            # Do not apply defaults of hidden widgets because they are
            # not visible to the user
            widget_opts = filter_widget.opts
            #if widget_opts.get("hidden"):
                #continue

            # Skip widget if there are no defaults
            if table_defaults is None and "default" not in widget_opts:
                continue

            # Use alias in selectors if looking at a component
            filter_widget.alias = resource.alias if resource.parent else None

            # Get all widget variables
            variables = filter_widget.variable(resource, get_vars)
            if not isinstance(variables, list):
                variables = [variables]

            for variable in variables:

                # Actual filter in get_vars?
                values = filter_widget._values(get_vars, variable)
                if values:
                    filter_widget.values[variable] = values
                    continue

                # Parse the variable
                selector, operator, invert = S3URLQuery.parse_key(variable)
                if invert:
                    operator = "%s!" % operator

                applicable_defaults = None

                # Table default?
                if table_defaults and selector in table_defaults:
                    # {selector: {op: value}}, {selector: value}, or {selector: callback}
                    applicable_defaults = table_defaults[selector]

                else:
                    # Widget default?
                    widget_default = widget_opts.get("default", DEFAULT)
                    if isinstance(widget_default, dict) and variable in widget_default:
                        # {variable: value}, or {variable: callback}
                        applicable_defaults = {operator: widget_default[variable]}
                    elif widget_default is not DEFAULT:
                        # {op: value}, value, or callback
                        applicable_defaults = widget_default

                if callable(applicable_defaults):
                    applicable_defaults = applicable_defaults(selector, tablename=tablename)

                if isinstance(applicable_defaults, dict):
                    default = applicable_defaults.get(operator)
                elif operator in (None, "belongs", "eq", "ne", "like"):
                    default = applicable_defaults
                else:
                    default = None

                if default is None:
                    # Ignore (configure [None] to filter for None)
                    continue

                if not isinstance(default, list):
                    default = [default]

                filter_widget.values[variable] = [str(v) if v is None else v for v in default]
                default_filters[variable] = ",".join(s3_str(v) for v in default)

            # Apply to resource
            queries = S3URLQuery.parse(resource, default_filters)
            add_filter = resource.add_filter
            for alias in queries:
                for q in queries[alias]:
                    add_filter(q)

        return default_filters

# =============================================================================
def set_default_filter(selector, value, tablename=None):
    """
        Set a default filter for selector.

        Args:
            selector: the field selector
            value: the value, can be a dict {operator: value},
                   a list of values, or a single value, or a
                   callable that returns any of these
            tablename: the tablename
    """

    s3 = current.response.s3

    filter_defaults = s3.get("filter_defaults")
    if filter_defaults is None:
        filter_defaults = s3["filter_defaults"] = {}

    table_defaults = filter_defaults.get("tablename")
    if table_defaults is None:
        table_defaults = filter_defaults[tablename] = {}

    table_defaults[selector] = value

# =============================================================================
def get_filter_options(tablename, *,
                       fieldname = "name",
                       location_filter = False,
                       org_filter = False,
                       key = "id",
                       none = False,
                       orderby = None,
                       translate = False,
                       ):
    """
        Lazy options getter - this is useful when the expected number
        of options is significantly smaller than the number of records
        to iterate through

        NB unlike the built-in reverse lookup in OptionsFilter, this
           function does *not* check whether the options are actually
           in use - so it can be used to enforce filter options to be
           shown even if there are no records matching them.

        Args:
            tablename: the name of the lookup table
            fieldname: the name of the field to represent options with
            location_filter: whether to filter the values by location
            org_filter: whether to filter the values by root_org
            key: the option key field (if not "id", e.g. a super key)
            none: whether to include an option for None
            orderby: orderby-expression as alternative to alpha-sorting
                     of options in widget (=> set widget sort=False)
            translate: whether to translate the values
    """

    auth = current.auth
    table = current.s3db.table(tablename)

    if auth.s3_has_permission("read", table):
        query = auth.s3_accessible_query("read", table)
        if "deleted" in table.fields:
            query &= (table.deleted == False)
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
        if orderby is None:
            # Options are alpha-sorted later in widget
            odict = dict
        else:
            # Options-dict to retain order
            odict = OrderedDict
        rows = current.db(query).select(table[key],
                                        table[fieldname],
                                        orderby = orderby,
                                        )

        if translate:
            T = current.T
            t_ = lambda v: T(v) if isinstance(v, str) else "-"
            opts = odict((row[key], t_(row[fieldname])) for row in rows)
        else:
            opts = odict((row[key], row[fieldname]) for row in rows)
        if none:
            opts[None] = current.messages["NONE"]
    else:
        opts = {}
    return opts

# END =========================================================================
