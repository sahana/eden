"""
    Inline components and links

    Copyright: 2012-2023 (c) Sahana Software Foundation

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

__all__ = ("SubFormLayout",
           "SubFormLayoutVertical",
           "InlineComponent",
           "InlineValueSet",
           "InlineLink",
           )

import json

from itertools import chain

from gluon import current, \
                  A, DIV, INPUT, LABEL, LI, TABLE, TAG, TBODY, TD, TFOOT, THEAD, TR, UL, XML, \
                  IS_EMPTY_OR, IS_IN_SET

from gluon.storage import Storage
from gluon.sqlhtml import StringWidget, SQLFORM

from s3dal import Field, original_tablename

from ..resource import FS
from ..tools import s3_str, s3_validate, JSONERRORS, JSONSEPARATORS, S3Represent, SKIP_VALIDATION

from .widgets import S3UploadWidget
from .selectors import LocationSelector
from .forms import DEFAULT, CRUDFormElement


# =============================================================================
class SubForm(CRUDFormElement):
    """
        Base class for subforms

        A subform is a form element to be processed after the main
        form. Subforms render a single (usually hidden) input field
        and a client-side controlled widget to manipulate its contents.
    """

    # -------------------------------------------------------------------------
    def __init__(self, selector, **options):
        """
            Args:
                selector: the data object selector
                options: options for the form element
        """

        super().__init__(selector, **options)

        self.alias = None

    # -------------------------------------------------------------------------
    def extract(self, resource, record_id):
        """
            Initialize this form element for a particular record. This
            method will be called by the form renderer to populate the
            form for an existing record. To be implemented in subclass.

            Args:
                resource: the resource the record belongs to
                record_id: the record ID

            Returns:
                the value for the input field that corresponds
                to the specified record.
        """

        return None

    # -------------------------------------------------------------------------
    def parse(self, value, record_id=None):
        """
            Validator method for the input field, used to extract the
            data from the input field and prepare them for further
            processing by the accept()-method. To be implemented in
            subclass and set as requires=self.parse for the input field
            in the resolve()-method of this form element.

            Args:
                value: the value returned from the input field
                record_id: usused (for API compatibility with validators)

            Returns:
                tuple of (value, error) where value is the pre-processed
                field value and error an error message in case of invalid
                data, or None.
        """

        return (value, None)

    # -------------------------------------------------------------------------
    def __call__(self, field, value, **attributes):
        """
            Widget renderer for the input field. To be implemented in
            subclass (if required) and to be set as widget=self for the
            field returned by the resolve()-method of this form element.

            Args:
                field: the input field
                value: the value to populate the widget
                attributes: attributes for the widget

            Returns:
                the widget for this form element as HTML helper
        """

        raise NotImplementedError

    # -------------------------------------------------------------------------
    def represent(self, value):
        """
            Read-only representation of this form element. This will be
            used instead of the __call__() method when the form element
            is to be rendered read-only.

            Args:
                value: the value as returned from extract()

            Returns:
                the read-only representation of this element as
                string or HTML helper
        """

        return ""

    # -------------------------------------------------------------------------
    def accept(self, form, master_id=None, format=None):
        """
            Post-process this form element and perform the related
            transactions. This method will be called after the main
            form has been accepted, where the master record ID will
            be provided.

            Args:
                form: the form
                master_id: the master record ID
                format: the data format extension

            Returns:
                True on success, False on error
        """

        return True

# =============================================================================
class SubFormLayout:
    """ Layout for InlineComponent (Base Class) """

    # Layout-specific CSS class for the inline component
    layout_class = "subform-default"

    def __init__(self):

        self.inject_script()
        self.columns = None
        self.row_actions = True

    # -------------------------------------------------------------------------
    def set_columns(self, columns, row_actions=True):
        """
            Set column widths for inline-widgets, can be used by subclasses
            to render CSS classes for grid-width

            Args:
                columns: iterable of column widths
                actions: whether the subform contains an action column
        """

        self.columns = columns
        self.row_actions = row_actions

    # -------------------------------------------------------------------------
    def subform(self,
                data,
                item_rows,
                action_rows,
                empty = False,
                readonly = False):
        """
            Outer container for the subform

            Args:
                data: the data dict (as returned from extract())
                item_rows: the item rows
                action_rows: the (hidden) action rows
                empty: no data in this component
                readonly: render read-only
        """

        if empty:
            subform = current.T("No entries currently available")
        else:
            headers = self.headers(data, readonly=readonly)
            subform = TABLE(headers,
                            TBODY(item_rows),
                            TFOOT(action_rows),
                            _class= " ".join(("embeddedComponent", self.layout_class)),
                            )
        return subform

    # -------------------------------------------------------------------------
    def readonly(self, resource, data):
        """
            Render this component read-only (table-style)

            Args:
                resource: the CRUDResource
                data: the data dict (as returned from extract())
        """

        audit = current.audit
        prefix, name = resource.prefix, resource.name

        xml_decode = current.xml.xml_decode

        items = data["data"]
        fields = data["fields"]

        trs = []
        for item in items:
            if "_id" in item:
                record_id = item["_id"]
            else:
                continue
            audit("read", prefix, name,
                  record=record_id,  representation="html")
            trow = TR(_class="read-row")
            for f in fields:
                text = xml_decode(item[f["name"]]["text"])
                trow.append(XML(xml_decode(text)))
            trs.append(trow)

        return self.subform(data, trs, [], empty=False, readonly=True)

    # -------------------------------------------------------------------------
    @staticmethod
    def render_list(resource, data):
        """
            Render this component read-only (list-style)

            Args:
                resource: the CRUDResource
                data: the data dict (as returned from extract())
        """

        audit = current.audit
        prefix, name = resource.prefix, resource.name

        xml_decode = current.xml.xml_decode

        items = data["data"]
        fields = data["fields"]

        # Render as comma-separated list of values (no header)
        elements = []
        for item in items:
            if "_id" in item:
                record_id = item["_id"]
            else:
                continue
            audit("read", prefix, name,
                  record=record_id, representation="html")
            t = []
            for f in fields:
                t.append([XML(xml_decode(item[f["name"]]["text"])), " "])
            elements.append([TAG[""](list(chain.from_iterable(t))[:-1]), ", "])

        return DIV(list(chain.from_iterable(elements))[:-1],
                   _class = "embeddedComponent",
                   )

    # -------------------------------------------------------------------------
    def headers(self, data, readonly=False):
        """
            Render the header row with field labels

            Args:
                data: the input field data as Python object
                readonly: whether the form is read-only
        """

        fields = data["fields"]

        # Don't render a header row if there are no labels
        render_header = False
        header_row = TR(_class = "label-row static")
        happend = header_row.append
        for f in fields:
            label = f["label"]
            if label:
                render_header = True
            label = TD(LABEL(label))
            happend(label)

        if render_header:
            if not readonly:
                # Add columns for the Controls
                happend(TD())
                happend(TD())
            return THEAD(header_row)
        else:
            return THEAD(_class = "hide")

    # -------------------------------------------------------------------------
    @staticmethod
    def actions(subform,
                formname,
                index,
                item = None,
                readonly = True,
                editable = True,
                deletable = True
                ):
        """
            Render subform row actions into the row

            Args:
                subform: the subform row
                formname: the form name
                index: the row index
                item: the row data
                readonly: this is a read-row
                editable: this row is editable
                deletable: this row is deletable
        """

        T = current.T
        action_id = "%s-%s" % (formname, index)

        # Action button helper
        def action(title, name, throbber=False):
            btn = DIV(_id = "%s-%s" % (name, action_id),
                      _class = "inline-%s" % name,
                      )
            if throbber:
                return DIV(btn,
                           DIV(_class = "inline-throbber hide",
                               _id = "throbber-%s" % action_id,
                               ),
                           )
            else:
                return DIV(btn)


        # CSS class for action-columns
        _class = "subform-action"

        # Render the action icons for this row
        append = subform.append
        if readonly:
            if editable:
                append(TD(action(T("Edit this entry"), "edt"),
                          _class = _class,
                          ))
            else:
                append(TD(_class=_class))

            if deletable:
                append(TD(action(T("Remove this entry"), "rmv"),
                          _class = _class,
                          ))
            else:
                append(TD(_class=_class))
        else:
            if index != "none" or item:
                append(TD(action(T("Update this entry"), "rdy", throbber=True),
                          _class = _class,
                          ))
                append(TD(action(T("Cancel editing"), "cnc"),
                          _class = _class,
                          ))
            else:
                append(TD(action(T("Discard this entry"), "dsc"),
                          _class=_class,
                          ))
                append(TD(action(T("Add this entry"), "add", throbber=True),
                          _class = _class,
                          ))

    # -------------------------------------------------------------------------
    def rowstyle_read(self, form, fields, *args, **kwargs):
        """
            Formstyle for subform read-rows, normally identical
            to rowstyle, but can be different in certain layouts
        """

        return self.rowstyle(form, fields, *args, **kwargs)

    # -------------------------------------------------------------------------
    def rowstyle(self, form, fields, *args, **kwargs):
        """
            Formstyle for subform action-rows
        """

        def render_col(col_id, label, widget, comment, hidden=False):

            if col_id == "submit_record__row":
                if hasattr(widget, "add_class"):
                    widget.add_class("inline-row-actions")
                col = TD(widget)
            elif comment:
                col = TD(DIV(widget, comment), _id=col_id)
            else:
                col = TD(widget, _id=col_id)
            return col

        if args:
            col_id = form
            label = fields
            widget, comment = args
            hidden = kwargs.get("hidden", False)
            return render_col(col_id, label, widget, comment, hidden)
        else:
            parent = TR()
            for col_id, label, widget, comment in fields:
                parent.append(render_col(col_id, label, widget, comment))
            return parent

    # -------------------------------------------------------------------------
    @staticmethod
    def inject_script():
        """ Inject custom JS to render new read-rows """

        # Example:

        #appname = current.request.application
        #scripts = current.response.s3.scripts

        #script = "/%s/static/themes/CRMT/js/inlinecomponent.layout.js" % appname
        #if script not in scripts:
            #scripts.append(script)

        # No custom JS in the default layout
        return

# =============================================================================
class SubFormLayoutVertical(SubFormLayout):
    """
        Vertical layout for inline-components

        - renders an vertical layout for edit-rows
        - standard horizontal layout for read-rows
        - hiding header row if there are no visible read-rows
    """

    # Layout-specific CSS class for the inline component
    layout_class = "subform-vertical"

    # -------------------------------------------------------------------------
    def headers(self, data, readonly=False):
        """
            Header-row layout: same as default, but non-static (i.e. hiding
            if there are no visible read-rows, because edit-rows have their
            own labels)
        """

        headers = super().headers

        header_row = headers(data, readonly = readonly)
        element = header_row.element("tr")
        if hasattr(element, "remove_class"):
            element.remove_class("static")
        return header_row

    # -------------------------------------------------------------------------
    def rowstyle_read(self, form, fields, *args, **kwargs):
        """
            Formstyle for subform read-rows, same as standard
            horizontal layout.
        """

        rowstyle = super().rowstyle
        return rowstyle(form, fields, *args, **kwargs)

    # -------------------------------------------------------------------------
    def rowstyle(self, form, fields, *args, **kwargs):
        """
            Formstyle for subform edit-rows, using a vertical
            formstyle because multiple fields combined with
            location-selector are too complex for horizontal
            layout.
        """

        # Use standard foundation formstyle
        from s3theme import formstyle_foundation as formstyle
        if args:
            col_id = form
            label = fields
            widget, comment = args
            hidden = kwargs.get("hidden", False)
            return formstyle(col_id, label, widget, comment, hidden)
        else:
            parent = TD(_colspan = len(fields))
            for col_id, label, widget, comment in fields:
                parent.append(formstyle(col_id, label, widget, comment))
            return TR(parent)

# =============================================================================
class INLINEFORM(DIV):
    """
        Custom DIV for inline components that adds the form rows for
        the current input data during XML generation

        Note:
            As XML generation happens after form.accepts, the input
            field will then hold the submitted value instead of the
            database value; this is required to retain newly added
            inline rows in case form.accepts fails, e.g. due to a
            validation error elsewhere in the form.
    """

    def xml(self):
        """ Generates the XML for this element """

        field = self["_field"]
        handler, data = self["handler"], None

        if field:
            # Read the inline-form data
            element = self.element("#%s" % field) if field else None
            if element:
                value = element["_value"]
                try:
                    data = json.loads(value)
                except JSONERRORS:
                    pass


        if handler and data:

            # Initialize layout
            layout = handler._layout()

            # Build item and action rows
            items, actions, empty, add = handler.form_rows(data, layout)

            # Build the widget
            widget = layout.subform(data, items, actions, empty=empty)

            # Reset layout
            layout.set_columns(None)

            # Restore uploads after validation failure
            if handler.upload:
                hidden = DIV(_class="hidden", _style="display:none")
                for k, v in handler.upload.items():
                    hidden.append(INPUT(_type = "text",
                                        _id = k,
                                        _name = k,
                                        _value = v,
                                        _style = "display:none",
                                        ))
            else:
                hidden = ""

            # Append elements
            self.append(hidden)
            self.append(widget)
            self.append(add)

        return super().xml()

# =============================================================================
class InlineComponent(SubForm):
    """
        Form element for an inline-component-form

        This form element allows CRUD of multi-record-components within
        the main record form. It renders a single hidden text field with a
        JSON representation of the component records, and a widget which
        facilitates client-side manipulation of this JSON.

        This widget is a row of fields per component record.

        The widget uses the s3.ui.inline_component.js script for client-side
        manipulation of the JSON data. Changes made by the script will be
        validated through Ajax-calls to the CRUD.validate() method.
        During accept(), the component gets updated according to the JSON
        returned.
    """

    prefix = "sub"

    def __init__(self, selector, **options):

        super().__init__(selector, **options)

        self.resource = None
        self.upload = {}

    # -------------------------------------------------------------------------
    def resolve(self, resource):
        """
            Method to resolve this form element against the calling resource.

            Args:
                resource: the resource

            Returns:
                a tuple (self, None, Field instance)
        """

        selector = self.selector

        # Check selector
        try:
            component = resource.components[selector]
        except KeyError as e:
            raise SyntaxError("Undefined component: %s" % selector) from e

        # Check permission
        permitted = current.auth.s3_has_permission("read",
                                                   component.tablename,
                                                   )
        if not permitted:
            return (None, None, None)

        options = self.options

        if "name" in options:
            self.alias = options["name"]
            label = self.alias
        else:
            self.alias = "default"
            label = self.selector

        if "label" in options:
            label = options["label"]
        else:
            label = " ".join([s.capitalize() for s in label.split("_")])

        fname = self._formname(separator = "_")
        field = Field(fname, "text",
                      comment = options.get("comment", None),
                      default = self.extract(resource, None),
                      label = label,
                      represent = self.represent,
                      required = options.get("required", False),
                      requires = self.parse,
                      widget = self,
                      )

        return (self, None, field)

    # -------------------------------------------------------------------------
    def extract(self, resource, record_id):
        """
            Initializes this form element for a particular record. Retrieves
            the component data for this record from the database and
            converts them into a JSON string to populate the input field with.

            Args:
                resource: the resource the record belongs to
                record_id: the record ID

            Returns:
                the JSON for the input field.
        """

        self.resource = resource

        component_name = self.selector
        try:
            component = resource.components[component_name]
        except KeyError as e:
            raise AttributeError("Undefined component") from e

        options = self.options

        if component.link:
            link = options.get("link", True)
            if link:
                # For link-table components, embed the link
                # table rather than the component
                component = component.link

        table = component.table
        tablename = component.tablename

        pkey = table._id.name

        fields_opt = options.get("fields", None)
        labels = {}
        if fields_opt:
            fields = []
            for f in fields_opt:
                if isinstance(f, tuple):
                    label, f = f
                    labels[f] = label
                if f in table.fields:
                    fields.append(f)
        else:
            # Really?
            fields = [f.name for f in table if f.readable or f.writable]

        if pkey not in fields:
            fields.insert(0, pkey)

        # Support read-only Virtual Fields
        if "virtual_fields" in options:
            virtual_fields = options["virtual_fields"]
        else:
            virtual_fields = []

        if "orderby" in options:
            orderby = options["orderby"]
        else:
            orderby = component.get_config("orderby")

        if record_id:
            if "filterby" in options:
                # Filter
                f = self._filterby_query()
                if f is not None:
                    component.build_query(filter=f)

            if "extra_fields" in options:
                extra_fields = options["extra_fields"]
            else:
                extra_fields = []
            all_fields = fields + virtual_fields + extra_fields
            start = 0
            limit = 1 if options.multiple is False else None
            data = component.select(all_fields,
                                    start = start,
                                    limit = limit,
                                    represent = True,
                                    raw_data = True,
                                    show_links = False,
                                    orderby = orderby,
                                    )

            records = data["rows"]
            rfields = data["rfields"]

            for f in rfields:
                if f.fname in extra_fields:
                    rfields.remove(f)
                else:
                    s = f.selector
                    if s.startswith("~."):
                        s = s[2:]
                    label = labels.get(s, None)
                    if label is not None:
                        f.label = label

        else:
            records = []
            rfields = []
            for s in fields:
                rfield = component.resolve_selector(s)
                label = labels.get(s, None)
                if label is not None:
                    rfield.label = label
                rfields.append(rfield)
            for f in virtual_fields:
                rfield = component.resolve_selector(f[1])
                rfield.label = f[0]
                rfields.append(rfield)

        headers = [{"name": rfield.fname,
                    "label": s3_str(rfield.label),
                    }
                    for rfield in rfields if rfield.fname != pkey]

        items = []
        has_permission = current.auth.s3_has_permission
        for record in records:

            row = record["_row"]
            row_id = row[str(table._id)]

            item = {"_id": row_id}

            permitted = has_permission("update", tablename, row_id)
            if not permitted:
                item["_readonly"] = True

            for rfield in rfields:

                fname = rfield.fname
                if fname == pkey:
                    continue

                colname = rfield.colname
                field = rfield.field

                widget = field.widget
                if isinstance(widget, LocationSelector):
                    # Use the widget extraction/serialization method
                    value = widget.serialize(widget.extract(row[colname]))
                elif hasattr(field, "formatter"):
                    value = field.formatter(row[colname])
                else:
                    # Virtual Field
                    value = row[colname]

                text = s3_str(record[colname])
                # Text representation is only used in read-forms where
                # representation markup cannot interfere with the inline
                # form logic - so stripping the markup should not be
                # necessary here:
                #if "<" in text:
                #    text = s3_strip_markup(text)

                item[fname] = {"value": value, "text": text}

            items.append(item)

        validate = options.get("validate", None)
        if not validate or \
           not isinstance(validate, tuple) or \
           not len(validate) == 2:
            request = current.request
            validate = (request.controller, request.function)
        c, f = validate

        data = {"controller": c,
                "function": f,
                "resource": resource.tablename,
                "component": component_name,
                "fields": headers,
                "defaults": self._filterby_defaults(),
                "data": items
                }

        return json.dumps(data, separators=JSONSEPARATORS)

    # -------------------------------------------------------------------------
    def parse(self, value, record_id=None):
        """
            Validator method, converts the JSON returned from the input
            field into a Python object.

            Args:
                value: the JSON from the input field.
                record_id: usused (for API compatibility with validators)

            Returns:
                tuple of (value, error), where value is the converted
                JSON, and error the error message if the decoding
                fails, otherwise None
        """

        # @todo: catch uploads during validation errors
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except JSONERRORS:
                import sys
                error = sys.exc_info()[1]
                if hasattr(error, "message"):
                    error = error.message
            else:
                error = None
        else:
            value = None
            error = None

        return (value, error)

    # -------------------------------------------------------------------------
    def __call__(self, field, value, **attributes):
        """
            Widget method for this form element. Renders a table with
            read-rows for existing entries, a variable edit-row to update
            existing entries, and an add-row to add new entries. This widget
            uses s3.inline_component.js to facilitate manipulation of the
            entries.

            Args:
                field: the Field for this form element
                value: the current value for this field
                attributes: keyword attributes for this widget
        """

        T = current.T

        if self.options.readonly is True:
            # Render read-only
            return self.represent(value)

        if value is None:
            value = field.default
        if not isinstance(value, str):
            value = json.dumps(value, separators=JSONSEPARATORS)

        # Input element attributes
        default = {"_type": "hidden",
                   "_value": value,
                   "requires": lambda v: (v, None),
                   }
        attr = StringWidget._attributes(field, default, **attributes)
        attr["_class"] = "%s hide" % attr["_class"]

        # Input element DOM ID
        real_input = "%s_%s" % (self.resource.tablename, field.name)
        attr["_id"] = real_input

        # Build the inline form
        subform = INLINEFORM(INPUT(**attr),
                             _id = self._formname(separator="-"),
                             _field = real_input,
                             _class = "inline-component",
                             handler = self,
                             )

        # Script options
        settings = current.deployment_settings
        js_opts = {"implicitCancelEdit": settings.get_ui_inline_cancel_edit(),
                   "confirmCancelEdit": s3_str(T("Discard changes?")),
                   }
        script = '''S3.inlineComponentsOpts=%s''' % json.dumps(js_opts)
        js_global = current.response.s3.js_global
        if script not in js_global:
            js_global.append(script)

        return subform

    # -------------------------------------------------------------------------
    def form_rows(self, data, layout):
        """
            Renders all inline form-rows from the data

            Args:
                data: the current input data
                layout: the sub-form layout

            Returns:
                tuple (items, actions, empty_flag, inline_open_add)
        """

        has_permission = current.auth.s3_has_permission

        # Find the component
        resource = self.resource
        component = resource.components[data["component"]]
        table = component.table
        tablename = component.tablename

        # Multiple/required options
        options = self.options
        if options.multiple is False:
            multiple = False
        else:
            multiple = True
        single_class = " single" if not multiple else ""
        required = options.get("required", False)

        # Configure the layout with columns
        columns = options.get("columns")
        if columns:
            layout.set_columns(columns, row_actions=multiple)

        # Check if resource is editable/deletable
        get_config = current.s3db.get_config
        setting = get_config(tablename, "editable")
        resource_editable = True if setting is None else bool(setting)
        setting = get_config(tablename, "deletable")
        resource_deletable = True if setting is None else bool(setting)

        fields = data["fields"]
        items = data["data"]

        formname = self._formname()
        empty = True

        # Render the read rows
        item_rows = []
        audit = current.audit
        prefix, name = component.prefix, component.name
        _class = "read-row inline-form%s" % single_class

        for i, item in enumerate(items):

            # Not empty if at least one item
            empty = False

            # Get the item record ID, and determine if editable/deletable
            if "_delete" in item and item["_delete"]:
                continue
            if "_id" in item:
                record_id = item["_id"]
                editable = deletable = False
                if resource_editable:
                    editable = has_permission("update", tablename, record_id)
                if resource_deletable:
                    deletable = has_permission("delete", tablename, record_id)
            else:
                record_id = None
                editable, deletable = resource_editable, resource_deletable

            # Render read-row
            rowname = "%s-%s" % (formname, i)
            read_row = self._render_item(table, item, fields,
                                         editable = editable,
                                         deletable = deletable,
                                         readonly = True,
                                         multiple = multiple,
                                         index = i,
                                         layout = layout,
                                         _id = "read-row-%s" % rowname,
                                         _class = _class,
                                         )

            # Audit READ
            if record_id:
                audit("read", prefix, name, record=record_id, representation="html")

            item_rows.append(read_row)


        # Add the action rows
        action_rows = []
        inline_open_add = ""

        # Edit-row
        _class = "edit-row inline-form hide%s" % single_class
        if required and not empty:
            _class = "%s required" % _class
        edit_item = items[-1] if items else None
        edit_row = self._render_item(table, edit_item, fields,
                                     editable = resource_editable,
                                     deletable = resource_deletable,
                                     readonly = False,
                                     multiple = multiple,
                                     index = 0,
                                     layout = layout,
                                     _id = "edit-row-%s" % formname,
                                     _class = _class,
                                     )
        action_rows.append(edit_row)

        # Add-row
        insertable = get_config(tablename, "insertable")
        if insertable is None:
            insertable = True
        if insertable:
            insertable = has_permission("create", tablename)
        if insertable:
            _class = "add-row inline-form"

            explicit_add = options.explicit_add
            if not multiple:
                explicit_add = False
                if not empty:
                    # Add Rows not relevant
                    _class = "%s hide" % _class
                else:
                    # Mark to client-side JS that we should always validate
                    _class = "%s single" % _class

            if required and empty:
                explicit_add = False
                _class = "%s required" % _class

            # Explicit open-action for add-row (optional)
            if explicit_add:
                # Hide add-row for explicit open-action
                _class = "%s hide" % _class
                if explicit_add is True:
                    label = current.T("Add another")
                else:
                    label = explicit_add
                inline_open_add = A(label, _class="inline-open-add action-lnk")

            empty = False
            add_row = self._render_item(table, None, fields,
                                        editable = True,
                                        deletable = True,
                                        readonly = False,
                                        multiple = multiple,
                                        layout = layout,
                                        _id = "add-row-%s" % formname,
                                        _class = _class,
                                        )
            action_rows.append(add_row)

        # Empty edit row
        empty_row = self._render_item(table, None, fields,
                                      editable = resource_editable,
                                      deletable = resource_deletable,
                                      readonly = False,
                                      multiple = multiple,
                                      index = "default",
                                      layout = layout,
                                      _id = "empty-edit-row-%s" % formname,
                                      _class = "empty-row inline-form hide",
                                      )
        action_rows.append(empty_row)

        # Empty read row
        empty_row = self._render_item(table, None, fields,
                                      editable = resource_editable,
                                      deletable = resource_deletable,
                                      readonly = True,
                                      multiple = multiple,
                                      index = "none",
                                      layout = layout,
                                      _id = "empty-read-row-%s" % formname,
                                      _class = "empty-row inline-form hide",
                                      )
        action_rows.append(empty_row)

        return item_rows, action_rows, empty, inline_open_add

    # -------------------------------------------------------------------------
    def represent(self, value):
        """
            Builds a read-only representation of this sub-form

            Args:
                value: the value returned from extract()
        """

        if isinstance(value, str):
            data = json.loads(value)
        else:
            data = value

        if data["data"] == []:
            # Don't render a subform for NONE
            return current.messages["NONE"]

        resource = self.resource
        component = resource.components[data["component"]]

        layout = self._layout()
        columns = self.options.get("columns")
        if columns:
            layout.set_columns(columns, row_actions=False)

        fields = data["fields"]
        if len(fields) == 1 and self.options.get("render_list", False):
            output = layout.render_list(component, data)
        else:
            output = layout.readonly(component, data)

        # Reset the layout
        layout.set_columns(None)

        return DIV(output,
                   _id = self._formname(separator="-"),
                   _class = "inline-component readonly",
                   )

    # -------------------------------------------------------------------------
    def accept(self, form, master_id=None, format=None):
        """
            Post-processeses this form element against the POST data of the
            request, and create/update/delete any related records.

            Args:
                form: the form
                master_id: the ID of the master record in the form
                format: the data format extension (for audit)
        """

        # Name of the real input field
        fname = self._formname(separator="_")

        options = self.options
        multiple = options.get("multiple", True)
        defaults = options.get("default", {})

        if fname in form.vars:

            # Retrieve the data
            try:
                data = json.loads(form.vars[fname])
            except ValueError:
                return False
            component_name = data.get("component", None)
            if not component_name:
                return False
            data = data.get("data", None)
            if not data:
                return False

            # Get the component
            resource = self.resource
            component = resource.components.get(component_name)
            if not component:
                return False

            # Link table handling
            link = component.link
            if link and options.get("link", True):
                # Data are for the link table
                actuate_link = False
                component = link
            else:
                # Data are for the component
                actuate_link = True

            # Table, tablename, prefix and name of the component
            prefix = component.prefix
            name = component.name
            tablename = component.tablename

            db = current.db
            table = db[tablename]

            s3db = current.s3db
            auth = current.auth

            # Process each item
            has_permission = auth.s3_has_permission
            audit = current.audit
            onaccept = s3db.onaccept

            for item in data:

                if not "_changed" in item and not "_delete" in item:
                    # No changes made to this item - skip
                    continue

                delete = item.get("_delete")
                values = Storage()
                valid = True

                if not delete:
                    # Get the values
                    for f, d in item.items():
                        if f[0] != "_" and d and isinstance(d, dict):

                            field = table[f]
                            widget = field.widget
                            if not hasattr(field, "type"):
                                # Virtual Field
                                continue
                            if field.type == "upload":
                                # Find, rename and store the uploaded file
                                rowindex = item.get("_index", None)
                                if rowindex is not None:
                                    filename = self._store_file(table, f, rowindex)
                                    if filename:
                                        values[f] = filename
                            elif isinstance(widget, LocationSelector):
                                # Value must be processed by widget post-process
                                value, error = widget.postprocess(d["value"])
                                if not error:
                                    values[f] = value
                                else:
                                    valid = False
                                    break
                            else:
                                # Must run through validator again (despite pre-validation)
                                # in order to post-process widget output properly (e.g. UTC
                                # offset subtraction)
                                try:
                                    value, error = s3_validate(table, f, d["value"])
                                except AttributeError:
                                    continue
                                if not error:
                                    values[f] = value
                                else:
                                    valid = False
                                    break

                if not valid:
                    # Skip invalid items
                    continue

                record_id = item.get("_id")

                if not record_id:
                    if delete:
                        # Item has been added and then removed again,
                        # so just ignore it
                        continue

                    if not component.multiple or not multiple:
                        # Do not create a second record in this component
                        query = (resource._id == master_id) & \
                                component.get_join()
                        f = self._filterby_query()
                        if f is not None:
                            query &= f
                        DELETED = current.xml.DELETED
                        if DELETED in table.fields:
                            query &= table[DELETED] != True
                        row = db(query).select(table._id, limitby=(0, 1)).first()
                        if row:
                            record_id = row[table._id]

                if record_id:
                    # Delete..?
                    if delete:
                        authorized = has_permission("delete", tablename, record_id)
                        if not authorized:
                            continue
                        c = s3db.resource(tablename, id=record_id)
                        # Audit happens inside .delete()
                        # Use cascade=True so that the deletion gets
                        # rolled back in case subsequent items fail:
                        success = c.delete(cascade=True, format="html")

                    # ...or update?
                    else:
                        authorized = has_permission("update", tablename, record_id)
                        if not authorized:
                            continue
                        query = (table._id == record_id)
                        success = db(query).update(**values)
                        values[table._id.name] = record_id

                        # Post-process update
                        if success:
                            audit("update", prefix, name,
                                  record=record_id, representation=format)
                            # Update super entity links
                            s3db.update_super(table, values)
                            # Update realm
                            update_realm = s3db.get_config(table, "update_realm")
                            if update_realm:
                                auth.set_realm_entity(table, values,
                                                      force_update=True)
                            # Onaccept
                            onaccept(table, Storage(vars=values), method="update")
                else:
                    # Create a new record
                    authorized = has_permission("create", tablename)
                    if not authorized:
                        continue

                    # Get master record ID
                    pkey = component.pkey
                    mastertable = resource.table
                    if pkey != mastertable._id.name:
                        query = (mastertable._id == master_id)
                        master = db(query).select(mastertable._id,
                                                  mastertable[pkey],
                                                  limitby = (0, 1)
                                                  ).first()
                        if not master:
                            return False
                    else:
                        master = Storage({pkey: master_id})

                    if actuate_link:
                        # Data are for component => apply component defaults
                        values = component.get_defaults(master,
                                                        defaults = defaults,
                                                        data = values,
                                                        )

                    if not actuate_link or not link:
                        # Add master record ID as linked directly
                        values[component.fkey] = master[pkey]
                    else:
                        # Check whether the component is a link table and
                        # we're linking to that via something like pr_person
                        # from hrm_human_resource
                        fkey = component.fkey
                        if fkey != "id" and fkey in component.fields and fkey not in values:
                            if fkey == "pe_id" and pkey == "person_id":
                                # Need to lookup the pe_id manually (bad that we need this
                                # special case, must be a better way but this works for now)
                                ptable = s3db.pr_person
                                query = (ptable.id == master[pkey])
                                person = db(query).select(ptable.pe_id,
                                                          limitby = (0, 1)
                                                          ).first()
                                if person:
                                    values["pe_id"] = person.pe_id
                                else:
                                    current.log.debug("S3Forms: Cannot find person with ID: %s" % master[pkey])
                            elif resource.tablename == "pr_person" and \
                                 fkey == "case_id" and pkey == "id":
                                # Using dvr_case as a link between pr_person & e.g. project_activity
                                # @ToDo: Work out generalisation & move to option if-possible
                                ltable = component.link.table
                                query = (ltable.person_id == master[pkey])
                                link_record = db(query).select(ltable.id,
                                                               limitby = (0, 1)
                                                               ).first()
                                if link_record:
                                    values[fkey] = link_record[pkey]
                                else:
                                    current.log.debug("S3Forms: Cannot find case for person ID: %s" % master[pkey])

                            else:
                                values[fkey] = master[pkey]

                    # Create the new record
                    # use _table in case we are using an alias
                    try:
                        record_id = component._table.insert(**values)
                    except:
                        current.log.debug("S3Forms: Cannot insert values %s into table: %s" % (values, component._table))
                        raise

                    # Post-process create
                    if record_id:
                        # Ensure we're using the real table, not an alias
                        table = db[tablename]
                        # Audit
                        audit("create", prefix, name,
                              record = record_id,
                              representation = format,
                              )
                        # Add record_id
                        values[table._id.name] = record_id
                        # Update super entity link
                        s3db.update_super(table, values)
                        # Update link table
                        if link and actuate_link and \
                           options.get("update_link", True):
                            link.update_link(master, values)
                        # Set record owner
                        auth.s3_set_record_owner(table, record_id)
                        # onaccept
                        subform = Storage(vars=Storage(values))
                        onaccept(table, subform, method="create")

            # Success
            return True
        else:
            return False

    # -------------------------------------------------------------------------
    # Utility methods
    # -------------------------------------------------------------------------
    def _formname(self, separator=None):
        """
            Generates a string representing the formname

            Args:
                separator: separator to prepend a prefix
        """

        if separator:
            return "%s%s%s%s" % (self.prefix,
                                 separator,
                                 self.alias,
                                 self.selector)
        else:
            return "%s%s" % (self.alias, self.selector)

    # -------------------------------------------------------------------------
    def _layout(self):
        """
            Initializes and returns the current layout
        """

        layout = self.options.layout
        if not layout:
            layout = current.deployment_settings.get_ui_inline_component_layout()
        elif isinstance(layout, type):
            layout = layout()
        return layout

    # -------------------------------------------------------------------------
    def _render_item(self,
                     table,
                     item,
                     fields,
                     readonly = True,
                     editable = False,
                     deletable = False,
                     multiple = True,
                     index = "none",
                     layout = None,
                     **attributes):
        """
            Renders an inline form-row

            Args:
                table: the database table
                item: the data
                fields: the fields to render (list of strings)
                readonly: render a read-row (otherwise edit-row)
                editable: whether the record can be edited
                deletable: whether the record can be deleted
                multiple: whether multiple records can be added
                index: the row index
                layout: the subform layout (SubFormLayout)
                attributes: HTML attributes for the row
        """

        s3 = current.response.s3

        rowtype = "read" if readonly else "edit"
        pkey = table._id.name

        data = {}
        formfields = []
        formname = self._formname()
        for f in fields:

            # Construct a row-specific field name
            fname = f["name"]
            idxname = "%s_i_%s_%s_%s" % (formname, fname, rowtype, index)

            # Parent and caller for add-popup
            if not readonly:
                # Use unaliased name to avoid need to create additional controllers
                parent = original_tablename(table).split("_", 1)[1]
                caller = "sub_%s_%s" % (formname, idxname)
                popup = Storage(parent=parent, caller=caller)
            else:
                popup = None

            # Custom label
            label = f.get("label", DEFAULT)

            # Use S3UploadWidget for upload fields
            if str(table[fname].type) == "upload":
                widget = S3UploadWidget.widget
            else:
                widget = DEFAULT

            # Get a Field instance for SQLFORM.factory
            formfield = self._rename_field(table[fname],
                                           idxname,
                                           comments = False,
                                           label = label,
                                           popup = popup,
                                           skip_validation = True,
                                           widget = widget,
                                           )

            # Reduced options set?
            if "filterby" in self.options:
                options = self._filterby_options(fname)
                if options:
                    if len(options) < 2:
                        requires = IS_IN_SET(options, zero=None)
                    else:
                        requires = IS_IN_SET(options)
                    formfield.requires = SKIP_VALIDATION(requires)

            # Get filterby-default
            filterby_defaults = self._filterby_defaults()
            if filterby_defaults and fname in filterby_defaults:
                default = filterby_defaults[fname]["value"]
                formfield.default = default

            # Add the data for this field (for existing rows)
            if index is not None and item and fname in item:
                if formfield.type == "upload":
                    filename = item[fname]["value"]
                    if current.request.env.request_method == "POST":
                        if "_index" in item and item.get("_changed", False):
                            rowindex = item["_index"]
                            filename = self._store_file(table, fname, rowindex)
                    data[idxname] = filename
                else:
                    value = item[fname]["value"]
                    if type(value) is str:
                        value = s3_str(value)
                    widget = formfield.widget
                    if isinstance(widget, LocationSelector):
                        # Use the widget parser to get at the selected ID
                        value, error = widget.parse(value).get("id"), None
                    else:
                        # Use the validator to get at the original value
                        value, error = s3_validate(table, fname, value)
                    if error:
                        value = None
                    data[idxname] = value
            formfields.append(formfield)

        if not data:
            data = None
        elif pkey not in data:
            data[pkey] = None

        # Render the subform
        subform_name = "sub_%s" % formname
        rowstyle = layout.rowstyle_read if readonly else layout.rowstyle
        subform = SQLFORM.factory(*formfields,
                                  record = data,
                                  showid = False,
                                  formstyle = rowstyle,
                                  upload = s3.download_url,
                                  readonly = readonly,
                                  table_name = subform_name,
                                  separator = ":",
                                  submit = False,
                                  buttons = [])
        subform = subform[0]

        # Retain any CSS classes added by the layout
        subform_class = subform["_class"]
        subform.update(**attributes)
        if subform_class:
            subform.add_class(subform_class)

        if multiple:
            # Render row actions
            layout.actions(subform,
                           formname,
                           index,
                           item = item,
                           readonly = readonly,
                           editable = editable,
                           deletable = deletable,
                           )

        return subform

    # -------------------------------------------------------------------------
    def _filterby_query(self):
        """
            Renders the filterby-options as Query to apply when retrieving
            the existing rows in this inline-component
        """

        filterby = self.options["filterby"]
        if not filterby:
            return None
        if not isinstance(filterby, (list, tuple)):
            filterby = [filterby]

        component = self.resource.components[self.selector]
        table = component.table

        query = None
        for f in filterby:
            fieldname = f["field"]
            if fieldname not in table.fields:
                continue
            field = table[fieldname]
            if "options" in f:
                options = f["options"]
            else:
                continue
            if "invert" in f:
                invert = f["invert"]
            else:
                invert = False
            if not isinstance(options, (list, tuple)):
                if invert:
                    q = (field != options)
                else:
                    q = (field == options)
            else:
                if invert:
                    q = (~(field.belongs(options)))
                else:
                    q = (field.belongs(options))
            if query is None:
                query = q
            else:
                query &= q

        return query

    # -------------------------------------------------------------------------
    def _filterby_defaults(self):
        """
            Renders the defaults for this inline-component as a dict
            for the real-input JSON
        """

        filterby = self.options.get("filterby")
        if filterby is None:
            return None

        if not isinstance(filterby, (list, tuple)):
            filterby = [filterby]

        component = self.resource.components[self.selector]
        table = component.table

        defaults = {}
        for f in filterby:
            fieldname = f["field"]
            if fieldname not in table.fields:
                continue
            if "default" in f:
                default = f["default"]
            elif "options" in f:
                options = f["options"]
                if "invert" in f and f["invert"]:
                    continue
                if isinstance(options, (list, tuple)):
                    if len(options) != 1:
                        continue
                    default = options[0]
                else:
                    default = options
            else:
                continue

            if default is not None:
                defaults[fieldname] = {"value": default}

        return defaults

    # -------------------------------------------------------------------------
    def _filterby_options(self, fieldname):
        """
            Re-renders the options list for a field if there is a
            filterby-restriction.

            Args:
                fieldname: the name of the field
        """

        component = self.resource.components[self.selector]
        table = component.table

        if fieldname not in table.fields:
            return None
        field = table[fieldname]

        filterby = self.options["filterby"]
        if filterby is None:
            return None
        if not isinstance(filterby, (list, tuple)):
            filterby = [filterby]

        filter_fields = dict((f["field"], f) for f in filterby)
        if fieldname not in filter_fields:
            return None

        filterby = filter_fields[fieldname]
        if "options" not in filterby:
            return None

        # Get the options list for the original validator
        requires = field.requires
        if not isinstance(requires, (list, tuple)):
            requires = [requires]
        if requires:
            r = requires[0]
            if isinstance(r, IS_EMPTY_OR):
                #empty = True
                r = r.other
            # Currently only supporting IS_IN_SET
            if not isinstance(r, IS_IN_SET):
                return None
        else:
            return None
        r_opts = r.options()

        # Get the filter options
        options = filterby["options"]
        if not isinstance(options, (list, tuple)):
            options = [options]
        subset = []
        if "invert" in filterby:
            invert = filterby["invert"]
        else:
            invert = False

        # Compute reduced options list
        for o in r_opts:
            if invert:
                if isinstance(o, (list, tuple)):
                    if o[0] not in options:
                        subset.append(o)
                elif isinstance(r_opts, dict):
                    if o not in options:
                        subset.append((o, r_opts[o]))
                elif o not in options:
                    subset.append(o)
            else:
                if isinstance(o, (list, tuple)):
                    if o[0] in options:
                        subset.append(o)
                elif isinstance(r_opts, dict):
                    if o in options:
                        subset.append((o, r_opts[o]))
                elif o in options:
                    subset.append(o)

        return subset

    # -------------------------------------------------------------------------
    def _store_file(self, table, fieldname, rowindex):
        """
            Finds, renames and stores an uploaded file and returns it's
            new pathname
        """

        field = table[fieldname]

        formname = self._formname()
        upload = "upload_%s_%s_%s" % (formname, fieldname, rowindex)

        post_vars = current.request.post_vars
        if upload in post_vars:

            f = post_vars[upload]
            if hasattr(f, "file"):
                # Newly uploaded file (FieldStorage)
                (sfile, ofilename) = (f.file, f.filename)
                nfilename = field.store(sfile,
                                        ofilename,
                                        field.uploadfolder)
                self.upload[upload] = nfilename
                return nfilename

            elif isinstance(f, str):
                # Previously uploaded file
                return f

        return None

# =============================================================================
class InlineValueSet(SubForm):

    # -------------------------------------------------------------------------
    def __init__(self, selector, **options):
        """
            Args:
                selector: the data object selector
                options: options for the form element
        """

        super().__init__(selector, **options)

        self.alias = None

    # -------------------------------------------------------------------------
    def resolve(self, resource):
        """
            Method to resolve this form element against the calling resource.
            To be implemented in subclass.

            Args:
                resource: the resource

            Returns:
                a tuple (form element,
                         original field name,
                         Field instance for the form renderer
                         )

            Note:
                The form element can be None for the main table, the component
                alias for a subtable, or this form element instance for a
                subform.

                If None is returned as Field instance, this form element will
                not be rendered at all. Besides setting readable/writable
                in the Field instance, this can be another mechanism to
                control access to form elements.
        """

        return None, None, None

    # -------------------------------------------------------------------------
    def extract(self, resource, record_id):
        """
            Initialize this form element for a particular record. This
            method will be called by the form renderer to populate the
            form for an existing record. To be implemented in subclass.

            Args:
                resource: the resource the record belongs to
                record_id: the record ID

            Returns:
                the value for the input field that corresponds
                to the specified record.
        """

        return None

    # -------------------------------------------------------------------------
    def parse(self, value, record_id=None):
        """
            Validator method for the input field, used to extract the
            data from the input field and prepare them for further
            processing by the accept()-method. To be implemented in
            subclass and set as requires=self.parse for the input field
            in the resolve()-method of this form element.

            Args:
                value: the value returned from the input field
                record_id: usused (for API compatibility with validators)

            Returns:
                tuple of (value, error) where value is the pre-processed
                field value and error an error message in case of invalid
                data, or None.
        """

        return (value, None)

    # -------------------------------------------------------------------------
    def __call__(self, field, value, **attributes):
        """
            Widget renderer for the input field. To be implemented in
            subclass (if required) and to be set as widget=self for the
            field returned by the resolve()-method of this form element.

            Args:
                field: the input field
                value: the value to populate the widget
                attributes: attributes for the widget

            Returns:
                the widget for this form element as HTML helper
        """

        raise NotImplementedError

    # -------------------------------------------------------------------------
    def represent(self, value):
        """
            Read-only representation of this form element. This will be
            used instead of the __call__() method when the form element
            is to be rendered read-only.

            Args:
                value: the value as returned from extract()

            Returns:
                the read-only representation of this element as
                string or HTML helper
        """

        return ""

    # -------------------------------------------------------------------------
    def accept(self, form, master_id=None, format=None):
        """
            Post-process this form element and perform the related
            transactions. This method will be called after the main
            form has been accepted, where the master record ID will
            be provided.

            Args:
                form: the form
                master_id: the master record ID
                format: the data format extension

            Returns:
                True on success, False on error
        """

        return True

# =============================================================================
class InlineLink(InlineComponent):
    """
        Subform to edit link table entries for the master record

        Keyword Args:
            ** Common options:

            readonly: render read-only always (bool)
            multiple: allow selection of multiple options (bool, default True)
            widget: which widget to use (str), one of:
                            - multiselect (default)
                            - groupedopts (default when cols is specified)
                            - hierarchy   (requires hierarchical lookup-table)
                            - cascade     (requires hierarchical lookup-table)
            render_list: in read-only mode, render HTML list rather than
                         comma-separated strings (bool, default False)

            ** Options for groupedopts widget:

            cols: number of columns for grouped ptions (int, default: None)
            orientation: orientation for grouped options order (str), one of:
                            - cols
                            - rows
            size: maximum number of items per group in grouped options,
                  None to disable grouping
            sort: sort grouped options (bool, always True when grouping,
                  i.e. size!=None)
            help_field: additional field in the look-up table to render as
                        tooltip for grouped options (field name, str)
            table: render grouped options as HTML TABLE rather than nested
                   DIVs (bool, default True)

            ** Options for multi-select widget:

            header: multi-select to show a header with bulk-select options
                    and optional search-field (bool)
            search: show the search-field in the header (bool)
            selectedList: how many items to show on multi-select button before
                          collapsing into number (int)
            noneSelectedText: placeholder text on multi-select button (str)
            columns: Foundation column-width for the widget (int, for custom forms)
            create: Options to create a new record, dict:
                            {"c": "controller",
                             "f": "function",
                             "label": "label",
                             "parent": "parent", (optional: which function to lookup options from)
                             "child": "child", (optional: which field to lookup options for)
                             }

            ** Options-filtering:
               - multiselect and groupedopts only
               - for hierarchy and cascade widgets, use the "filter" option

            requires: validator to determine the selectable options (defaults
                      to field validator)
            filterby: filter look-up options, a dict {selector: values}, each
                      selector can be a field in the look-up table itself or
                      in another table linked to it
            match: filter look-up options, analogous to filterby, but instead
                   of values, specifies selectors to retrieve the filter values
                   from the master resource, i.e. {selector: master_selector}

            ** Options for hierarchy and cascade widgets:

            levels: ordered list of labels for hierarchy levels (top-down order),
                    to override the lookup-table's "hierarchy_levels" setting,
                    cascade-widget only
            represent: representation function for hierarchy nodes (defaults
                       to field represent)
            leafonly: only leaf nodes can be selected (bool)
            cascade: automatically select the entire branch when a parent
                     node is newly selected; with multiple=False, this will
                     auto-select single child options (bool, default True when
                     leafonly=True)
            filter: filter expression to filter the selectable options
                    (S3ResourceQuery)
    """

    prefix = "link"

    # -------------------------------------------------------------------------
    def extract(self, resource, record_id):
        """
            Get all existing links for record_id.

            Args:
                resource: the resource the record belongs to
                record_id: the record ID

            Returns:
                list of component record IDs this record is
                linked to via the link table
        """

        self.resource = resource
        component, link = self.get_link()

        # Customise resources
        from ..controller import CRUDRequest
        r = CRUDRequest(resource.prefix,
                        resource.name,
                        # Current request args/vars could be in a different
                        # resource context, so must override them here:
                        args = [],
                        get_vars = {},
                        )
        for tablename in (component.tablename, link.tablename):
            if tablename:
                r.customise_resource(tablename)

        if record_id:
            rkey = component.rkey
            rows = link.select([rkey], as_rows=True)
            if rows:
                rkey = str(link.table[rkey])
                values = self.subset([row[rkey] for row in rows])
            else:
                values = []
        else:
            # Use default
            values = [link.table[self.options.field].default]

        return values

    # -------------------------------------------------------------------------
    def __call__(self, field, value, **attributes):
        """
            Widget renderer, currently supports multiselect (default),
            hierarchy and groupedopts widgets.

            Args:
                field: the input field
                value: the value to populate the widget
                attributes: attributes for the widget

            Returns:
                the widget
        """

        options = self.options
        component, link = self.get_link()

        has_permission = current.auth.s3_has_permission
        ltablename = link.tablename

        # User must have permission to create and delete
        # link table entries (which is what this widget is about):
        if options.readonly is True or \
           not has_permission("create", ltablename) or \
           not has_permission("delete", ltablename):
            # Render read-only
            return self.represent(value)

        multiple = options.get("multiple", True)
        options["multiple"] = multiple

        # Field dummy
        kfield = link.table[component.rkey]
        dummy_field = Storage(name = field.name,
                              type = kfield.type,
                              label = options.label or kfield.label,
                              represent = kfield.represent,
                              )

        # Widget type
        widget = options.get("widget")
        if widget not in ("hierarchy", "cascade"):
            requires = options.get("requires")
            if requires is None:
                # Get the selectable entries for the widget and construct
                # a validator from it
                opts = self.get_options()
                zero = options.get("zero", XML("&nbsp"))
                if multiple or zero is not None:
                    # Drop the empty option
                    # - multiple does not need one (must de-select all instead)
                    # - otherwise, it shall be replaced by the zero-option
                    opts = {k: v for k, v in opts.items() if k != ""}

                requires = IS_IN_SET(opts,
                                     multiple = multiple,
                                     zero = None if multiple else zero,
                                     sort = options.get("sort", True),
                                     )
                if zero is not None:
                    # Allow deselecting all (or single: selection of explicit none)
                    # NB this is the default, unless zero is explicitly set to None
                    requires = IS_EMPTY_OR(requires)

            dummy_field.requires = requires

        # Helper to extract widget options
        widget_opts = lambda keys: {k: v for k, v in options.items() if k in keys}

        # Instantiate the widget
        if widget == "groupedopts" or not widget and "cols" in options:
            from .widgets import S3GroupedOptionsWidget
            w_opts = widget_opts(("cols",
                                  "help_field",
                                  "multiple",
                                  "orientation",
                                  "size",
                                  "sort",
                                  "table",
                                  ))
            w = S3GroupedOptionsWidget(**w_opts)
        elif widget == "hierarchy":
            from .widgets import S3HierarchyWidget
            w_opts = widget_opts(("multiple",
                                  "filter",
                                  "leafonly",
                                  "cascade",
                                  "represent",
                                  ))
            w_opts["lookup"] = component.tablename
            w = S3HierarchyWidget(**w_opts)
        elif widget == "cascade":
            from .widgets import S3CascadeSelectWidget
            w_opts = widget_opts(("levels",
                                  "multiple",
                                  "filter",
                                  "leafonly",
                                  "cascade",
                                  "represent",
                                  ))
            w_opts["lookup"] = component.tablename
            w = S3CascadeSelectWidget(**w_opts)
        else:
            # Default to multiselect
            from .widgets import S3MultiSelectWidget
            w_opts = widget_opts(("multiple",
                                  "search",
                                  "header",
                                  "selectedList",
                                  "noneSelectedText",
                                  "columns",
                                  "create",
                                  ))
            w = S3MultiSelectWidget(**w_opts)

        # Render the widget
        attr = dict(attributes)
        attr["_id"] = field.name
        if not link.table[options.field].writable:
            _class = attr.get("_class", None)
            if _class:
                attr["_class"] = "%s hide" % _class
            else:
                attr["_class"] = "hide"
        widget = w(dummy_field, value, **attr)
        if hasattr(widget, "add_class"):
            widget.add_class("inline-link")

        # Append the attached script to jquery_ready
        script = options.get("script")
        if script:
            current.response.s3.jquery_ready.append(script)

        return widget

    # -------------------------------------------------------------------------
    def validate(self, form):
        """
            Validate this link, currently only checking whether it has
            a value when required=True

            Args:
                form: the form
        """

        required = self.options.required
        if not required:
            return

        fname = self._formname(separator="_")
        values = form.vars.get(fname)

        if not values:
            error = current.T("Value Required") \
                    if required is True else required
            form.errors[fname] = error

    # -------------------------------------------------------------------------
    def accept(self, form, master_id=None, format=None):
        """
            Post-processes this subform element against the POST data,
            and create/update/delete any related records.

            Args:
                form: the master form
                master_id: the ID of the master record in the form
                format: the data format extension (for audit)

            TODO implement audit
        """

        from ..resource import FS

        s3db = current.s3db

        # Name of the real input field
        fname = self._formname(separator="_")
        resource = self.resource

        success = False

        if fname in form.vars:

            # Extract the new values from the form
            values = form.vars[fname]
            if values is None:
                values = []
            elif not isinstance(values, (list, tuple, set)):
                values = [values]
            values = set(str(v) for v in values)

            # Get the link table
            component, link = self.get_link()

            # Get the master identity (pkey)
            pkey = component.pkey
            if pkey == resource._id.name:
                master = {pkey: master_id}
            else:
                # Different pkey (e.g. super-key) => reload the master
                query = (resource._id == master_id)
                master = current.db(query).select(resource.table[pkey],
                                                  limitby=(0, 1)).first()

            if master:
                # Find existing links
                query = FS(component.lkey) == master[pkey]
                lresource = s3db.resource(link.tablename, filter = query)
                rows = lresource.select([component.rkey], as_rows=True)

                # Determine which to delete and which to add
                if rows:
                    rkey = link.table[component.rkey]
                    current_ids = set(str(row[rkey]) for row in rows)
                    delete = current_ids - values
                    insert = values - current_ids
                else:
                    delete = None
                    insert = values

                # Delete links (of the valid subset) which are no longer used
                if delete:
                    query &= FS(component.rkey).belongs(self.subset(delete))
                    lresource = s3db.resource(link.tablename, filter = query)
                    lresource.delete()

                # Insert new links
                insert.discard("")
                if insert:
                    # Insert new links
                    for record_id in insert:
                        record = {component.fkey: record_id}
                        link.update_link(master, record)

                success = True

        return success

    # -------------------------------------------------------------------------
    def represent(self, value):
        """
            Read-only representation of this subform.

            Args:
                value: the value as returned from extract()

            Returns:
                the read-only representation
        """

        component, link = self.get_link()

        # Use the represent of rkey if it supports bulk, otherwise
        # instantiate an S3Represent from scratch:
        rkey = link.table[component.rkey]
        represent = rkey.represent
        if not hasattr(represent, "bulk"):
            # Pick the first field from the list that is available:
            lookup_field = None
            for fname in ("name", "tag"):
                if fname in component.fields:
                    lookup_field = fname
                    break
            represent = S3Represent(lookup = component.tablename,
                                    fields = [lookup_field],
                                    )

        # Represent all values
        if isinstance(value, (list, tuple, set)):
            result = represent.bulk(list(value))
            if None not in value:
                result.pop(None, None)
        else:
            result = represent.bulk([value])

        # Sort them
        def labels_sorted(labels):

            try:
                s = sorted(labels)
            except TypeError:
                if any(isinstance(l, DIV) for l in labels):
                    # Don't sort labels if they contain markup
                    s = labels
                else:
                    s = sorted(s3_str(l) if l is not None else "-" for l in labels)
            return s
        labels = labels_sorted(result.values())

        if self.options.get("render_list"):
            if value is None or value == [None]:
                # Don't render as list if empty
                return current.messages.NONE
            else:
                # Render as HTML list
                return UL([LI(l) for l in labels],
                          _class = "s3-inline-link",
                          )
        else:
            # Render as comma-separated list of strings
            # (using TAG rather than join() to support HTML labels)
            return TAG[""](list(chain.from_iterable([[l, ", "]
                                                    for l in labels]))[:-1])

    # -------------------------------------------------------------------------
    def subset(self, values):
        """
            Reduces a list of values to the applicable subset of options,
            to limit extraction and deletion of existing links as per
            requires|filterby|match options.

            Args:
                values: list|tuple|set of values to filter
            Returns:
                list of filtered values
        """

        # Apply filterby/match
        has_option = self.options.get
        subset = None
        validator = has_option("requires")
        if validator and hasattr(validator, "options"):
            subset = {str(o) for o, _ in validator.options()}
        elif has_option("filterby") or has_option("match"):
            subset = {str(o) for o in self.get_options()}
        if subset:
            values = list(filter(lambda key: str(key) in subset, values))

        return values

    # -------------------------------------------------------------------------
    def get_options(self):
        """
            Get the options for the widget

            Returns:
                dict {value: representation} of options
        """

        resource = self.resource
        component, link = self.get_link()

        rkey = link.table[component.rkey]

        # Lookup rkey options from rkey validator
        opts = []
        requires = rkey.requires
        if not isinstance(requires, (list, tuple)):
            requires = [requires]
        if requires:
            validator = requires[0]
            if isinstance(validator, IS_EMPTY_OR):
                validator = validator.other
            try:
                opts = validator.options()
            except AttributeError:
                pass

        # Filter these options?
        widget_opts_get = self.options.get

        filter_query = None
        subquery = self.subquery
        filterby = widget_opts_get("filterby")
        if filterby:
            # Field shall match one of the specified values
            for selector, values in filterby.items():

                q = subquery(selector, values)
                filter_query = filter_query & q if filter_query else q

        filterby = widget_opts_get("match")
        if filterby and resource._rows:
            # Field shall match one of the values in the field
            # specified by expr
            for selector, expr in filterby.items():

                # Get the values in the match-field
                rfield = resource.resolve_selector(expr)
                colname = rfield.colname
                rows = resource.select([expr], as_rows=True)
                values = [row[colname] for row in rows]

                q = subquery(selector, values)
                filter_query = filter_query & q if filter_query else q

        if filter_query is not None:
            # Select the filtered component rows
            filter_resource = current.s3db.resource(component.tablename,
                                                    filter = filter_query,
                                                    )
            rows = filter_resource.select(["id"], as_rows=True)

            # Reduce the options to the thus selected rows
            values = set(str(row[component.table._id]) for row in rows)
            filtered_opts = [opt for opt in opts if str(opt[0]) in values]
            opts = filtered_opts

        return dict(opts)

    # -------------------------------------------------------------------------
    @staticmethod
    def subquery(selector, values):
        """
            Construct a query for selector to match values; taking
            into account the special case of None (helper function
            for get_options).

            Args:
                selector: the field selector (str)
                values: the values to match (list|tuple|set or single value)

            Returns:
                the query
        """

        field = FS(selector)

        if isinstance(values, (list, tuple, set)):
            if None in values:
                filter_values = [v for v in values if v is not None]
                if filter_values:
                    query = (field.belongs(filter_values)) | (field == None)
                else:
                    query = (field == None)
            else:
                query = (field.belongs(list(values)))
        else:
            query = (field == values)

        return query

    # -------------------------------------------------------------------------
    def get_link(self):
        """
            Find the target component and its linktable

            Returns:
                tuple of CRUDResource instances (component, link)
        """

        selector = self.selector
        try:
            component = self.resource.components[selector]
        except KeyError as e:
            raise SyntaxError("Undefined component: %s" % selector) from e

        link = component.link
        if not link:
            # @todo: better error message
            raise SyntaxError("No linktable for %s" % selector)

        return (component, link)

