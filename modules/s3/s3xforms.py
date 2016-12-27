# -*- coding: utf-8 -*-

""" S3 XForms API

    @copyright: 2014-2016 (c) Sahana Software Foundation
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

__all__ = ("S3XForms",
           "S3XFormsWidget",
           )

from gluon import *
from s3rest import S3Method
from s3utils import s3_unicode

# =============================================================================
class S3XForms(S3Method):
    """ XForm-based CRUD Handler """

    # -------------------------------------------------------------------------
    def apply_method(self, r, **attr):
        """
            Apply CRUD methods

            @param r: the S3Request
            @param attr: controller parameters for the request

            @return: output object to send to the view
        """

        if r.http == "GET":
            return self.form(r, **attr)
        else:
            r.error(405, current.ERROR.BAD_METHOD)

    # -------------------------------------------------------------------------
    def form(self, r, **attr):
        """
            Generate an XForms form for the current resource

            @param r: the S3Request
            @param attr: controller parameters for the request
        """

        resource = self.resource

        # @todo: apply xform-setting
        form = S3XFormsForm(resource.table)

        response = current.response
        response.headers["Content-Type"] = "application/xhtml+xml"
        return form

    # -------------------------------------------------------------------------
    @staticmethod
    def formlist():
        """
            Retrieve a list of available XForms

            @return: a list of tuples (url, title) of available XForms
        """

        resources = current.deployment_settings.get_xforms_resources()

        xforms = []
        if resources:
            s3db = current.s3db
            for item in resources:

                # Parse item options
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

                # Get the resource
                try:
                    resource = s3db.resource(tablename)
                except AttributeError:
                    current.log.warning("XForms: non-existent resource %s" % tablename)
                    continue

                if title is None:
                    title = " ".join(w.capitalize() for w in resource.name.split("_"))

                # Options can override target controller/function and URL vars
                c = options.get("c", "xforms")
                f = options.get("f", "forms")
                url_vars = options.get("vars", {})

                config = resource.get_config("xform")
                if config:
                    if isinstance(config, dict):
                        # Template-based XForm
                        collection = config.get("collection")
                        if not collection:
                            continue
                        table = resource.table
                        DELETED = current.xml.DELETED
                        if DELETED in table:
                            query = table[DELETED] != True
                        else:
                            query = table.id > 0
                        public = options.get("check", "public")
                        if public in table:
                            query &= table[public] == True
                        title_field = options.get("title", "name")
                        # @todo: audit
                        rows = current.db(query).select(table._id,
                                                        table[title_field],
                                                        )
                        native = c == "xforms"
                        for row in rows:
                            if native:
                                args = [tablename, row[table._id]]
                            else:
                                args = [row[table._id], "xform.xhtml"]
                            url = URL(c = c,
                                      f = f,
                                      args = args,
                                      vars = url_vars,
                                      host = True,
                                      extension = "",
                                      )
                            xforms.append((url, row[title_field]))
                    else:
                        # Custom XForm => not supported yet, skip
                        continue
                else:
                    # Introspective XForm
                    if c == "xforms":
                        args = [tablename]
                    else:
                        args = ["xform.xhtml"]
                    url = URL(c = c,
                              f = f,
                              args = args,
                              vars = url_vars,
                              host = True,
                              extension = "",
                              )
                    xforms.append((url, title))

        return xforms

# =============================================================================
class S3XFormsWidget(object):
    """ XForms Form Widget (Base Class) """

    def __init__(self, translate = True):
        """
            Constructor

            @param translate: enable/disable label translation
        """

        self.translate = translate
        self._strings = {}

    # -------------------------------------------------------------------------
    def __call__(self, field, label, ref):
        """
            Form builder entry point

            @param field: the Field or a Storage with field information
            @param label: the label
            @param ref: the reference (string) that links the widget
                        with the data model

            @return: tuple (widget, dict of i18n-strings)
        """

        if not field:
            raise SyntaxError("Field is required")

        if not ref:
            raise SyntaxError("Reference is required")
        self.ref = ref
        attr = {"_ref": ref}

        self.setstr("label", label)
        comment = field.comment
        if comment and isinstance(comment, basestring):
            # @todo: support LazyT, and extract hints from
            #        S3PopupLinks or other tooltip DIVs
            self.setstr("hint", comment)

        return self.widget(field, attr), self._strings

    # -------------------------------------------------------------------------
    def widget(self, field, attr):
        """
            Render the XForms Widget.

            @param field: the Field or a Storage with field information
            @param attr: dict with XML attributes for the widget, including
                         the mandatory "ref" attribute that links the widget
                         to the data model
        """

        # To be implemented in subclass
        raise NotImplementedError

    # -------------------------------------------------------------------------
    def hint(self):
        """
            Render the hint for this formfield

            @return: a <hint> element, or an empty tag if not available
        """

        return self.getstr("hint", "hint", default=TAG[""]())

    # -------------------------------------------------------------------------
    def label(self):
        """
            Render the label for this formfield

            @return: a <label> element, or an empty tag if not available
        """

        return self.getstr("label", "label")

    # -------------------------------------------------------------------------
    def setstr(self, key, string=None):
        """
            Add a translatable string to this widget

            @param key: the key for the string
            @param string: the string, or None to remove the key
        """

        ref = "%s:%s" % (self.ref, key)

        strings = self._strings
        if string:
            if hasattr(string, "flatten"):
                string = string.flatten()
            strings[ref] = string
        elif key in strings:
            del strings[ref]
        return

    # -------------------------------------------------------------------------
    def getstr(self, tag, key, default=None):
        """
            Get a translated string reference

            @param tag: the tag to wrap the string reference
            @param key: the key for the string
        """

        empty = False
        ref = "%s:%s" % (self.ref, key)

        translations = self._strings
        if ref in translations:
            string = translations[ref]
        elif default is not None:
            return default
        else:
            ref = None
            string = ""

        widget = TAG[str(tag)]

        if self.translate and ref:
            return widget(_ref="jr:itext('%s')" % ref)
        else:
            return widget(string)

# =============================================================================
class S3XFormsStringWidget(S3XFormsWidget):
    """ String Input Widget for XForms """

    def widget(self, field, attr):
        """ Widget renderer (parameter description see base class) """

        return TAG["input"](self.label(), self.hint(), **attr)

# =============================================================================
class S3XFormsTextWidget(S3XFormsWidget):
    """ Text (=multi-line string) Input Widget for XForms """

    def widget(self, field, attr):
        """ Widget renderer (parameter description see base class) """

        return TAG["input"](self.label(), self.hint(), **attr)

# =============================================================================
class S3XFormsReadonlyWidget(S3XFormsWidget):
    """ Read-only Widget for XForms """

    def widget(self, field, attr):
        """ Widget renderer (parameter description see base class) """

        attr["_readonly"] = "true"
        attr["_default"] = s3_unicode(field.default)

        return TAG["input"](self.label(), **attr)

# =============================================================================
class S3XFormsOptionsWidget(S3XFormsWidget):
    """ Options Widget for XForms """

    def widget(self, field, attr):
        """ Widget renderer (parameter description see base class) """

        requires = field.requires
        if not hasattr(requires, "options"):
            return TAG["input"](self.label(), **attr)

        items = [self.label(), self.hint()] + self.items(requires.options())
        return TAG["select1"](items, **attr)

    # -------------------------------------------------------------------------
    def items(self, options):
        """
            Render the items for the selector

            @param options: the options, list of tuples (value, text)
        """

        items = []
        setstr = self.setstr
        getstr = self.getstr
        for index, option in enumerate(options):

            value, text = option
            key = "option%s" % index
            if hasattr(text, "m") or hasattr(text, "flatten"):
                setstr(key, text)
                text = getstr("label", key)
            else:
                text = TAG["label"](text)

            items.append(TAG["item"](text,
                                     TAG["value"](value),
                                     ))
        return items

# =============================================================================
class S3XFormsMultipleOptionsWidget(S3XFormsOptionsWidget):
    """ Multiple Options Widget for XForms """

    def widget(self, field, attr):
        """ Widget renderer (parameter description see base class) """

        requires = field.requires
        if not hasattr(requires, "options"):
            return TAG["input"](self.label(), **attr)

        items = [self.label(), self.hint()] + self.items(requires.options())
        return TAG["select"](items, **attr)

# =============================================================================
class S3XFormsBooleanWidget(S3XFormsWidget):
    """ Boolean Widget for XForms """

    def widget(self, field, attr):
        """ Widget renderer (parameter description see base class) """

        T = current.T
        setstr = self.setstr
        setstr("false", T("No")) # @todo: use field-represent instead
        setstr("true", T("Yes")) # @todo: use field-represent instead

        getstr = self.getstr
        items = [self.label(),
                 self.hint(),
                 TAG["item"](getstr("label", "true"), TAG["value"](1)),
                 TAG["item"](getstr("label", "true"), TAG["value"](0)),
                 ]
        return TAG["select1"](items, **attr)

# =============================================================================
class S3XFormsUploadWidget(S3XFormsWidget):
    """ Upload Widget for XForms (currently only for image-upload) """

    def widget(self, field, attr):
        """ Widget renderer (parameter description see base class) """

        attr["_mediatype"] = "image/*"
        return TAG["upload"](self.label(), self.hint(), **attr)

# =============================================================================
class S3XFormsField(object):
    """
        Class representing an XForms form field.

        After initialization, the XForms elements for the form field
        can be accessed via lazy properties:

            - model             the model node for the field
            - binding           the binding tag for the field
            - widget            the form widget
            - strings           the strings for internationalization

        @todo: implement specialized widgets
        @todo: extend constraint introspection
    """

    # Mapping field type <=> XForms widget
    widgets = {
        "string": S3XFormsStringWidget,
        "text": S3XFormsTextWidget,
        "integer": S3XFormsStringWidget,
        "double": S3XFormsStringWidget,
        "decimal": S3XFormsStringWidget,
        "time": S3XFormsStringWidget,
        "date": S3XFormsStringWidget,
        "datetime": S3XFormsStringWidget,
        "upload": S3XFormsUploadWidget,
        "boolean": S3XFormsBooleanWidget,
        "options": S3XFormsOptionsWidget,
        "multiple": S3XFormsMultipleOptionsWidget,
        #"radio": S3XFormsRadioWidget,
        #"checkboxes": S3XFormsCheckboxesWidget,
    }

    # Type mapping web2py <=> XForms
    types = {"string": "string",
             "double": "decimal",
             "date": "date",
             "datetime": "datetime",
             "integer": "int",
             "boolean": "boolean",
             "upload": "binary",
             "text": "text",
             }

    # -------------------------------------------------------------------------
    def __init__(self, tablename, field, translate=True):
        """
            Constructor

            @param tablename: the table name
            @param field: the Field or a Storage with field information
            @param translate: enable/disable label translation
        """

        self.tablename = tablename
        self.field = field

        self.name = field.name
        self.ref = "/%s/%s" % (self.tablename, self.name)

        self.translate = translate

        # Initialize properties
        self._model = None
        self._binding = None
        self._strings = None
        self._widget = None

    # -------------------------------------------------------------------------
    @property
    def model(self):
        """
            The model node for this form field (lazy property)
        """
        if self._model is None:
            self._introspect()
        return self._model

    # -------------------------------------------------------------------------
    @property
    def binding(self):
        """
            The binding for this form field (lazy property)
        """

        if self._binding is None:
            self._introspect()
        return self._binding

    # -------------------------------------------------------------------------
    @property
    def strings(self):
        """
            The dict of i18n-strings for this form field (lazy property)
        """

        if self._strings is None:
            self._introspect()
        return self._strings

    # -------------------------------------------------------------------------
    @property
    def widget(self):
        """
            The widget for this form field (lazy property)
        """

        if self._widget is None:
            self._introspect()
        return self._widget

    # -------------------------------------------------------------------------
    def _introspect(self):
        """
            Introspect the field type and constraints, generate model,
            binding and widget and extract i18n strings. The results
            can be accessed via the lazy properties model, binding, widget,
            and strings.

            @return: nothing
        """

        field = self.field

        # Initialize i18n strings
        self._strings = {}

        # Tag for the model
        self._model = TAG[self.name]()

        # Is the field writable/required?
        readonly = None # "false()"
        required = None # "false()"
        if not field.writable:
            readonly = "true()"
        elif self._required(field):
            required = "true()"

        # Basic binding attributes
        attr = {"_nodeset": self.ref,
                "_required": required,
                "_readonly": readonly,
                }

        # Get the xforms field type
        fieldtype = self.types.get(str(field.type), "string")

        # Introspect validators
        requires = field.requires
        options = False
        multiple = False
        if requires:
            if not isinstance(requires, list):
                requires = [requires]
            # Does the field have options?
            first = requires[0]
            if hasattr(first, "options"):
                options = True
                if hasattr(first, "multiple") and first.multiple:
                    multiple = True
            # Does the field have a minimum and/or maximum constraint?
            elif fieldtype in ("decimal", "int", "date", "datetime"):
                constraint = self._range(requires)
                if constraint:
                    attr["_constraint"] = constraint

        # Add the field type to binding
        if not options:
            attr["_type"] = fieldtype

        # Binding
        self._binding = TAG["bind"](**attr)

        # Determine the widget
        if hasattr(field, "xform"):
            # Custom widget
            widget = field.xform
        else:
            # Determine the widget type
            if not field.writable:
                widget_type = "readonly"
            else:
                widget_type = str(field.type)
                if options:
                    if multiple:
                        widget_type = "multiple"
                    else:
                        widget_type = "options"

            widgets = self.widgets
            if widget_type in widgets:
                widget = widgets[widget_type]
            else:
                widget = None

        if widget is not None:
            # Instantiate the widget if necessary
            if isinstance(widget, type):
                widget = widget(translate=self.translate)

            # Get the label
            if hasattr(field, "label"):
                label = field.label
            else:
                label = None
            if not label:
                label = current.T(" ".join(s.capitalize()
                                  for s in self.name.split("_")).strip())

            # Render the widget and update i18n strings
            self._widget, strings = widget(field, label, self.ref)
            if self.translate:
                self._strings.update(strings)
        else:
            # Unsupported widget type => render an empty tag
            self._widget = TAG[""]()

        return

    # -------------------------------------------------------------------------
    @staticmethod
    def _range(validators):
        """
            Introspect range constraints, convert to string for binding

            @param validators: a sequence of validators
            @return: a string with the range constraints
        """

        constraints = []

        for validator in validators:
            if hasattr(validator, "other"):
                v = validator.other
            else:
                v = validator
            if isinstance(v, (IS_INT_IN_RANGE, IS_FLOAT_IN_RANGE)):
                maximum = v.maximum
                if maximum is not None:
                    constraints.append(". < %s" % maximum)
                minimum = v.minimum
                if minimum is not None:
                    constraints.append(". > %s" % minimum)
        if constraints:
            return "(%s)" % " and ".join(constraints)
        return None

    # -------------------------------------------------------------------------
    @staticmethod
    def _required(field):
        """
            Determine whether field is required

            @param field: the Field or a Storage with field information
            @return: True if field is required, else False
        """

        required = False
        validators = field.requires
        if isinstance(validators, IS_EMPTY_OR):
            required = False
        else:
            required = field.required or field.notnull
        if not required and validators:
            if not isinstance(validators, (list, tuple)):
                validators = [validators]
            for v in validators:
                if hasattr(v, "options"):
                    if hasattr(v, "zero") and v.zero is None:
                        continue
                if hasattr(v, "mark_required"):
                    if v.mark_required:
                        required = True
                        break
                    else:
                        continue
                try:
                    val, error = v("")
                except TypeError:
                    # default validator takes no args
                    pass
                else:
                    if error:
                        required = True
                        break
        return required

# =============================================================================
class S3XFormsForm(object):
    """ XForms Form Generator """

    def __init__(self, table, name=None, translate=True):
        """
            Constructor

            @param table: the database table
            @param name: optional alternative form name
            @param translate: enable/disable translation of strings
        """

        self.table = table

        if name:
            self.name = name
        elif hasattr(table, "_tablename"):
            self.name = table._tablename
        else:
            self.name = str(table)

        # Initialize the form fields
        fields = []
        append = fields.append
        for field in table:
            if field.readable:
                append(S3XFormsField(table, field, translate=translate))
        self._fields = fields

        self.translate = translate

    # -------------------------------------------------------------------------
    def xml(self):
        """
            Render this form as XML string

            @return: XML as string
        """

        ns = {"_xmlns": "http://www.w3.org/2002/xforms",
              "_xmlns:h": "http://www.w3.org/1999/xhtml",
              "_xmlns:ev": "http://www.w3.org/2001/xml-events",
              "_xmlns:xsd": "http://www.w3.org/2001/XMLSchema",
              "_xmlns:jr": "http://openrosa.org/javarosa",
              }

        document = TAG["h:html"](self._head(), self._body(), **ns)
        return document.xml()

    # -------------------------------------------------------------------------
    def _head(self):
        """
            Get the HTML head for this form

            @return: an <h:head> tag
        """

        # @todo: introspect title (in caller, then pass-in)
        title = TAG["h:title"](self.name)
        model = self._model()

        return TAG["h:head"](title, model)

    # -------------------------------------------------------------------------
    def _body(self):
        """
            Get the HTML body for this form

            @return: an <h:body> tag
        """

        widgets = self._widgets()
        return TAG["h:body"](widgets)

    # -------------------------------------------------------------------------
    def _model(self):
        """
            Get the model for this form

            @return: a <model> tag with instance, bindings and i18n strings
        """

        instance = self._instance()
        bindings = self._bindings()
        translations = self._translations()


        return TAG["model"](instance,
                            bindings,
                            translations,
                            )

    # -------------------------------------------------------------------------
    def _instance(self):
        """
            Get the instance for this form

            @return: an <instance> tag with all form field nodes
        """

        nodes = []
        append = nodes.append

        for field in self._fields:
            append(field.model)

        return TAG["instance"](TAG[self.name](nodes), _id=self.name)

    # -------------------------------------------------------------------------
    def _bindings(self):
        """
            Get the bindings for this form

            @return: a TAG with the bindings
        """

        bindings = []
        append = bindings.append

        for field in self._fields:
            append(field.binding)

        return TAG[""](bindings)

    # -------------------------------------------------------------------------
    def _widgets(self):
        """
            Get the widgets for this form

            @return: a TAG with the widgets
        """

        strings = self._strings

        widgets = []
        append = widgets.append

        fields = self._fields
        for field in self._fields:
            append(field.widget)
        return TAG[""](widgets)

    # -------------------------------------------------------------------------
    def _strings(self):
        """
            Get a dict with all i18n strings for this form

            @return: a dict {key: string}
        """

        strings = {}
        if self.translate:
            update = strings.update
            for field in self._fields:
                update(field.strings)
        return strings

    # -------------------------------------------------------------------------
    def _translations(self):
        """
            Render the translations for all configured languages

            @returns: translation tags
        """

        T = current.T
        translations = TAG[""]()

        strings = self._strings()
        if self.translate and strings:
            append_translation = translations.append

            languages = [l for l in current.response.s3.l10n_languages
                           if l != "en"]
            languages.insert(0, "en")
            for language in languages:
                translation = TAG["translation"](_lang=language)
                append_string = translation.append
                for key, string in strings.items():
                    tstr = T(string.m if hasattr(string, "m") else string,
                             language = language,
                             )
                    append_string(TAG["text"](TAG["value"](tstr), _id=key))

                if len(translation):
                    append_translation(translation)

        return TAG["itext"](translations)

# END =========================================================================
