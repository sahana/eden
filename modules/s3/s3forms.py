# -*- coding: utf-8 -*-

""" S3 SQL Forms

    @copyright: 2012-2019 (c) Sahana Software Foundation
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

__all__ = ("S3SQLCustomForm",
           "S3SQLDefaultForm",
           "S3SQLDummyField",
           "S3SQLInlineInstruction",
           "S3SQLSectionBreak",
           "S3SQLVirtualField",
           "S3SQLSubFormLayout",
           "S3SQLVerticalSubFormLayout",
           "S3SQLInlineComponent",
           "S3SQLInlineLink",
           )

import json

from itertools import chain

from gluon import *
from gluon.storage import Storage
from gluon.sqlhtml import StringWidget
from gluon.tools import callback
from gluon.validators import Validator

from s3compat import basestring, unicodeT, xrange
from s3dal import Field, original_tablename
from .s3query import FS
from .s3utils import s3_mark_required, s3_store_last_record_id, s3_str, s3_validate
from .s3widgets import S3Selector, S3UploadWidget

# Compact JSON encoding
SEPARATORS = (",", ":")
DEFAULT = lambda: None

# =============================================================================
class S3SQLForm(object):
    """ SQL Form Base Class"""

    # -------------------------------------------------------------------------
    def __init__(self, *elements, **attributes):
        """
            Constructor to define the form and its elements.

            @param elements: the form elements
            @param attributes: form attributes
        """

        self.elements = []
        append = self.elements.append

        debug = current.deployment_settings.get_base_debug()
        for element in elements:
            if not element:
                continue
            if isinstance(element, S3SQLFormElement):
                append(element)
            elif isinstance(element, str):
                append(S3SQLField(element))
            elif isinstance(element, tuple):
                l = len(element)
                if l > 1:
                    label, selector = element[:2]
                    widget = element[2] if l > 2 else DEFAULT
                else:
                    selector = element[0]
                    label = widget = DEFAULT
                append(S3SQLField(selector, label=label, widget=widget))
            else:
                msg = "Invalid form element: %s" % str(element)
                if debug:
                    raise SyntaxError(msg)
                else:
                    current.log.error(msg)

        opts = {}
        attr = {}
        for k in attributes:
            value = attributes[k]
            if k[:1] == "_":
                attr[k] = value
            else:
                opts[k] = value

        self.attr = attr
        self.opts = opts

    # -------------------------------------------------------------------------
    # Rendering/Processing
    # -------------------------------------------------------------------------
    def __call__(self,
                 request=None,
                 resource=None,
                 record_id=None,
                 readonly=False,
                 message="Record created/updated",
                 format=None,
                 **options):
        """
            Render/process the form. To be implemented in subclass.

            @param request: the S3Request
            @param resource: the target S3Resource
            @param record_id: the record ID
            @param readonly: render the form read-only
            @param message: message upon successful form submission
            @param format: data format extension (for audit)
            @param options: keyword options for the form

            @return: a FORM instance
        """

        return None

    # -------------------------------------------------------------------------
    # Utility functions
    # -------------------------------------------------------------------------
    def __len__(self):
        """
            Support len(crud_form)
        """

        return len(self.elements)

    # -------------------------------------------------------------------------
    def _config(self, key, default=None):
        """
            Get a configuration setting for the current table

            @param key: the setting key
            @param default: fallback value if the setting is not available
        """

        tablename = self.tablename
        if tablename:
            return current.s3db.get_config(tablename, key, default)
        else:
            return default

    # -------------------------------------------------------------------------
    @staticmethod
    def _submit_buttons(readonly=False):
        """
            Render submit buttons

            @param readonly: render the form read-only
            @return: list of submit buttons
        """

        T = current.T
        s3 = current.response.s3
        settings = s3.crud

        if settings.custom_submit:
            submit = [(None,
                       settings.submit_button,
                       settings.submit_style)]
            submit.extend(settings.custom_submit)
            buttons = []
            for name, label, _class in submit:
                if isinstance(label, basestring):
                    label = T(label)
                button = INPUT(_type="submit",
                               _class="btn crud-submit-button",
                               _name=name,
                               _value=label)
                if _class:
                    button.add_class(_class)
                buttons.append(button)
        else:
            buttons = ["submit"]

        # Cancel button
        if not readonly and s3.cancel:
            if not settings.custom_submit:
                if settings.submit_button:
                    submit_label = T(settings.submit_button)
                else:
                    submit_label = T("Save")
                submit_button = INPUT(_type="submit",
                                      _value=submit_label)
                if settings.submit_style:
                    submit_button.add_class(settings.submit_style)
                buttons = [submit_button]

            cancel = s3.cancel
            if isinstance(cancel, DIV):
                cancel_button = cancel
            else:
                cancel_button = A(T("Cancel"),
                                  _class="cancel-form-btn action-lnk")
                if isinstance(cancel, dict):
                    # Script-controlled cancel button (embedded form)
                    if "script" in cancel:
                        # Custom script
                        script = cancel["script"]
                    else:
                        # Default script: hide form, show add-button
                        script = \
'''$('.cancel-form-btn').click(function(){$('#%(hide)s').slideUp('medium',function(){$('#%(show)s').show()})})'''
                    s3.jquery_ready.append(script % cancel)
                elif s3.cancel is True:
                    cancel_button.add_class("s3-cancel")
                else:
                    cancel_button.update(_href=s3.cancel)
            buttons.append(cancel_button)

        return buttons

    # -------------------------------------------------------------------------
    @staticmethod
    def _insert_subheadings(form, tablename, formstyle, subheadings):
        """
            Insert subheadings into forms

            @param form: the form
            @param tablename: the tablename
            @param formstyle: the formstyle
            @param subheadings:
                {"fieldname": "Heading"} or {"fieldname": ["Heading1", "Heading2"]}
        """

        if not subheadings:
            return
        if tablename in subheadings:
            subheadings = subheadings.get(tablename)
        if formstyle.__name__ in ("formstyle_table",
                                  "formstyle_table_inline",
                                  ):
            def create_subheading(represent, tablename, f, level=""):
                return TR(TD(represent, _colspan=3,
                             _class="subheading",
                             ),
                          _class = "subheading",
                          _id = "%s_%s__subheading%s" % (tablename, f, level),
                          )
        else:
            def create_subheading(represent, tablename, f, level=""):
                return DIV(represent,
                           _class = "subheading",
                           _id = "%s_%s__subheading%s" % (tablename, f, level),
                           )

        form_rows = iter(form[0])
        tr = next(form_rows)
        i = 0
        while tr:
            # @ToDo: We need a better way of working than this!
            f = tr.attributes.get("_id", None)
            if not f:
                try:
                    # DIV-based form-style
                    f = tr[0][0].attributes.get("_id", None)
                    if not f:
                        # DRRPP formstyle
                        f = tr[0][0][1][0].attributes.get("_id", None)
                        if not f:
                            # Date fields are inside an extra TAG()
                            f = tr[0][0][1][0][0].attributes.get("_id", None)
                except:
                    # Something else
                    f = None
            if f:
                if f.endswith("__row"):
                    f = f[:-5]
                if f.startswith(tablename):
                    f = f[len(tablename) + 1:] # : -6
                    if f.startswith("sub_"):
                        # Component
                        f = f[4:]
                elif f.startswith("sub-default"):
                    # S3SQLInlineComponent[CheckBox]
                    f = f[11:]
                elif f.startswith("sub_"):
                    # S3GroupedOptionsWidget
                    f = f[4:]
                headings = subheadings.get(f)
                if not headings:
                    try:
                        tr = next(form_rows)
                    except StopIteration:
                        break
                    else:
                        i += 1
                    continue
                if not isinstance(headings, list):
                    headings = [headings]
                inserted = 0
                for heading in headings:
                    subheading = create_subheading(heading, tablename, f, inserted if inserted else "")
                    form[0].insert(i, subheading)
                    i += 1
                    inserted += 1
                if inserted:
                    tr.attributes.update(_class="%s after_subheading" % tr.attributes["_class"])
                    for _i in range(0, inserted):
                        # Iterate over the rows we just created
                        tr = next(form_rows)
            try:
                tr = next(form_rows)
            except StopIteration:
                break
            else:
                i += 1

# =============================================================================
class S3SQLDefaultForm(S3SQLForm):
    """ Standard SQL form """

    # -------------------------------------------------------------------------
    # Rendering/Processing
    # -------------------------------------------------------------------------
    def __call__(self,
                 request=None,
                 resource=None,
                 record_id=None,
                 readonly=False,
                 message="Record created/updated",
                 format=None,
                 **options):
        """
            Render/process the form.

            @param request: the S3Request
            @param resource: the target S3Resource
            @param record_id: the record ID
            @param readonly: render the form read-only
            @param message: message upon successful form submission
            @param format: data format extension (for audit)
            @param options: keyword options for the form

            @todo: describe keyword arguments

            @return: a FORM instance
        """

        if resource is None:
            self.resource = request.resource
            self.prefix, self.name, self.table, self.tablename = \
                request.target()
        else:
            self.resource = resource
            self.prefix = resource.prefix
            self.name = resource.name

            self.tablename = resource.tablename
            self.table = resource.table

        response = current.response
        s3 = response.s3
        settings = s3.crud

        prefix = self.prefix
        name = self.name
        tablename = self.tablename
        table = self.table

        record = None
        labels = None

        self.record_id = record_id

        if not readonly:
            _get = options.get

            # Pre-populate create-form?
            if record_id is None:
                data = _get("data", None)
                from_table = _get("from_table", None)
                from_record = _get("from_record", None)
                map_fields = _get("map_fields", None)
                record = self.prepopulate(from_table=from_table,
                                          from_record=from_record,
                                          map_fields=map_fields,
                                          data=data,
                                          format=format)

            # De-duplicate link table entries
            self.record_id = record_id = self.deduplicate_link(request, record_id)

            # Add asterisk to labels of required fields
            mark_required = self._config("mark_required", default=[])
            labels, required = s3_mark_required(table, mark_required)
            if required:
                # Show the key if there are any required fields.
                s3.has_required = True
            else:
                s3.has_required = False

        # Determine form style
        if format == "plain":
            # Default formstyle works best when we have no formatting
            formstyle = "table3cols"
        elif readonly:
            formstyle = settings.formstyle_read
        else:
            formstyle = settings.formstyle

        # Submit buttons
        buttons = self._submit_buttons(readonly)

        # Generate the form
        if record is None:
            record = record_id
        response.form_label_separator = ""
        form = SQLFORM(table,
                       record = record,
                       record_id = record_id,
                       readonly = readonly,
                       comments = not readonly,
                       deletable = False,
                       showid = False,
                       upload = s3.download_url,
                       labels = labels,
                       formstyle = formstyle,
                       separator = "",
                       submit_button = settings.submit_button,
                       buttons = buttons)

        # Style the Submit button, if-requested
        if settings.submit_style and not settings.custom_submit:
            try:
                form[0][-1][0][0]["_class"] = settings.submit_style
            except:
                # Submit button has been removed or a different formstyle,
                # such as Bootstrap (which is already styled anyway)
                pass

        # Subheadings
        subheadings = options.get("subheadings", None)
        if subheadings:
            self._insert_subheadings(form, tablename, formstyle, subheadings)

        # Process the form
        logged = False
        if not readonly:
            link = _get("link")
            hierarchy = _get("hierarchy")
            onvalidation = _get("onvalidation")
            onaccept = _get("onaccept")
            success, error = self.process(form,
                                          request.post_vars,
                                          onvalidation = onvalidation,
                                          onaccept = onaccept,
                                          hierarchy = hierarchy,
                                          link = link,
                                          http = request.http,
                                          format = format,
                                          )
            if success:
                response.confirmation = message
                logged = True
            elif error:
                response.error = error

        # Audit read
        if not logged and not form.errors:
            current.audit("read", prefix, name,
                          record=record_id, representation=format)

        return form

    # -------------------------------------------------------------------------
    def prepopulate(self,
                    from_table=None,
                    from_record=None,
                    map_fields=None,
                    data=None,
                    format=None):
        """
            Pre-populate the form with values from a previous record or
            controller-submitted data

            @param from_table: the table to copy the data from
            @param from_record: the record to copy the data from
            @param map_fields: field selection/mapping
            @param data: the data to prepopulate the form with
            @param format: the request format extension
        """

        table = self.table
        record = None

        # Pre-populate from a previous record?
        if from_table is not None:

            # Field mapping
            if map_fields:
                if isinstance(map_fields, dict):
                    # Map fields with other names
                    fields = [from_table[map_fields[f]]
                              for f in map_fields
                                if f in table.fields and
                                   map_fields[f] in from_table.fields and
                                   table[f].writable]

                elif isinstance(map_fields, (list, tuple)):
                    # Only use a subset of the fields
                    fields = [from_table[f]
                              for f in map_fields
                                if f in table.fields and
                                   f in from_table.fields and
                                   table[f].writable]
                else:
                    raise TypeError
            else:
                # Use all writable fields
                fields = [from_table[f]
                          for f in table.fields
                            if f in from_table.fields and
                            table[f].writable]

            # Audit read => this is a read method, after all
            prefix, name = from_table._tablename.split("_", 1)
            current.audit("read", prefix, name,
                          record=from_record, representation=format)

            # Get original record
            query = (from_table.id == from_record)
            row = current.db(query).select(limitby=(0, 1), *fields).first()
            if row:
                if isinstance(map_fields, dict):
                    record = Storage([(f, row[map_fields[f]])
                                      for f in map_fields])
                else:
                    record = Storage(row)

        # Pre-populate from call?
        elif isinstance(data, dict):
            record = Storage([(f, data[f])
                              for f in data
                                if f in table.fields and
                                   table[f].writable])

        # Add missing fields to pre-populated record
        if record:
            missing_fields = Storage()
            for f in table.fields:
                if f not in record and table[f].writable:
                    missing_fields[f] = table[f].default
            record.update(missing_fields)
            record[table._id.name] = None

        return record

    # -------------------------------------------------------------------------
    def deduplicate_link(self, request, record_id):
        """
            Change to update if this request attempts to create a
            duplicate entry in a link table

            @param request: the request
            @param record_id: the record ID
        """

        linked = self.resource.linked
        table = self.table

        session = current.session

        if request.env.request_method == "POST" and linked is not None:
            pkey = table._id.name
            post_vars = request.post_vars
            if not post_vars[pkey]:

                lkey = linked.lkey
                rkey = linked.rkey

                def parse_key(value):
                    key = s3_str(value)
                    if key.startswith("{"):
                        # JSON-based selector (e.g. S3LocationSelector)
                        return json.loads(key).get("id")
                    else:
                        # Normal selector (e.g. OptionsWidget)
                        return value

                try:
                    lkey_ = parse_key(post_vars[lkey])
                    rkey_ = parse_key(post_vars[rkey])
                except Exception:
                    return record_id

                query = (table[lkey] == lkey_) & (table[rkey] == rkey_)
                row = current.db(query).select(table._id, limitby=(0, 1)).first()
                if row is not None:
                    tablename = self.tablename
                    record_id = row[pkey]
                    formkey = session.get("_formkey[%s/None]" % tablename)
                    formname = "%s/%s" % (tablename, record_id)
                    session["_formkey[%s]" % formname] = formkey
                    post_vars["_formname"] = formname
                    post_vars[pkey] = record_id

        return record_id

    # -------------------------------------------------------------------------
    def process(self, form, vars,
                onvalidation = None,
                onaccept = None,
                hierarchy = None,
                link = None,
                http = "POST",
                format = None,
                ):
        """
            Process the form

            @param form: FORM instance
            @param vars: request POST variables
            @param onvalidation: callback(function) upon successful form validation
            @param onaccept: callback(function) upon successful form acceptance
            @param hierarchy: the data for the hierarchy link to create
            @param link: component link
            @param http: HTTP method
            @param format: request extension

        """

        table = self.table
        tablename = self.tablename

        # Get the proper onvalidation routine
        if isinstance(onvalidation, dict):
            onvalidation = onvalidation.get(tablename, [])

        # Append link.postprocess to onvalidation
        if link and link.postprocess:
            postprocess = link.postprocess
            if isinstance(onvalidation, list):
                onvalidation.insert(0, postprocess)
            elif onvalidation is not None:
                onvalidation = [postprocess, onvalidation]
            else:
                onvalidation = [postprocess]

        success = True
        error = None

        record_id = self.record_id
        formname = "%s/%s" % (tablename, record_id)
        if form.accepts(vars,
                        current.session,
                        formname=formname,
                        onvalidation=onvalidation,
                        keepvalues=False,
                        hideerror=False):

            # Undelete?
            if vars.get("_undelete"):
                undelete = form.vars.get("deleted") is False
            else:
                undelete = False

            # Audit
            prefix = self.prefix
            name = self.name
            if record_id is None or undelete:
                current.audit("create", prefix, name, form=form,
                              representation=format)
            else:
                current.audit("update", prefix, name, form=form,
                              record=record_id, representation=format)

            form_vars = form.vars

            # Update super entity links
            s3db = current.s3db
            s3db.update_super(table, form_vars)

            # Update component link
            if link and link.postprocess is None:
                resource = link.resource
                master = link.master
                resource.update_link(master, form_vars)

            if form_vars.id:
                if record_id is None or undelete:
                    # Create hierarchy link
                    if hierarchy:
                        from .s3hierarchy import S3Hierarchy
                        h = S3Hierarchy(tablename)
                        if h.config:
                            h.postprocess_create_node(hierarchy, form_vars)
                    # Set record owner
                    auth = current.auth
                    auth.s3_set_record_owner(table, form_vars.id)
                    auth.s3_make_session_owner(table, form_vars.id)
                else:
                    # Update realm
                    update_realm = s3db.get_config(table, "update_realm")
                    if update_realm:
                        current.auth.set_realm_entity(table, form_vars,
                                                      force_update=True)
                # Store session vars
                self.resource.lastid = str(form_vars.id)
                s3_store_last_record_id(tablename, form_vars.id)

            # Execute onaccept
            try:
                callback(onaccept, form, tablename=tablename)
            except:
                error = "onaccept failed: %s" % str(onaccept)
                current.log.error(error)
                # This is getting swallowed
                raise

        else:
            success = False

            if form.errors:

                # Revert any records created within widgets/validators
                current.db.rollback()

                # IS_LIST_OF validation errors need special handling
                errors = []
                for fieldname in form.errors:
                    if fieldname in table:
                        if isinstance(table[fieldname].requires, IS_LIST_OF):
                            errors.append("%s: %s" % (fieldname,
                                                      form.errors[fieldname]))
                        else:
                            errors.append(str(form.errors[fieldname]))
                if errors:
                    error = "\n".join(errors)

            elif http == "POST":

                # Invalid form
                error = current.T("Invalid form (re-opened in another window?)")

        return success, error

# =============================================================================
class S3SQLCustomForm(S3SQLForm):
    """ Custom SQL Form """

    # -------------------------------------------------------------------------
    def insert(self, index, element):
        """
            S.insert(index, object) -- insert object before index
        """

        if not element:
            return
        if isinstance(element, S3SQLFormElement):
            self.elements.insert(index, element)
        elif isinstance(element, str):
            self.elements.insert(index, S3SQLField(element))
        elif isinstance(element, tuple):
            l = len(element)
            if l > 1:
                label, selector = element[:2]
                widget = element[2] if l > 2 else DEFAULT
            else:
                selector = element[0]
                label = widget = DEFAULT
            self.elements.insert(index, S3SQLField(selector, label=label, widget=widget))
        else:
            msg = "Invalid form element: %s" % str(element)
            if current.deployment_settings.get_base_debug():
                raise SyntaxError(msg)
            else:
                current.log.error(msg)

    # -------------------------------------------------------------------------
    def append(self, element):
        """
            S.append(object) -- append object to the end of the sequence
        """

        self.insert(len(self), element)

    # -------------------------------------------------------------------------
    # Rendering/Processing
    # -------------------------------------------------------------------------
    def __call__(self,
                 request=None,
                 resource=None,
                 record_id=None,
                 readonly=False,
                 message="Record created/updated",
                 format=None,
                 **options):
        """
            Render/process the form.

            @param request: the S3Request
            @param resource: the target S3Resource
            @param record_id: the record ID
            @param readonly: render the form read-only
            @param message: message upon successful form submission
            @param format: data format extension (for audit)
            @param options: keyword options for the form

            @return: a FORM instance
        """

        db = current.db
        response = current.response
        s3 = response.s3

        # Determine the target resource
        if resource is None:
            resource = request.resource
            self.prefix, self.name, self.table, self.tablename = \
                request.target()
        else:
            self.prefix = resource.prefix
            self.name = resource.name
            self.tablename = resource.tablename
            self.table = resource.table
        self.resource = resource

        # Resolve all form elements against the resource
        subtables = set()
        subtable_fields = {}
        fields = []
        components = []

        for element in self.elements:
            alias, name, field = element.resolve(resource)

            if isinstance(alias, str):
                subtables.add(alias)

                if field is not None:
                    fields_ = subtable_fields.get(alias)
                    if fields_ is None:
                        fields_ = []
                    fields_.append((name, field))
                    subtable_fields[alias] = fields_

            elif isinstance(alias, S3SQLFormElement):
                components.append(alias)

            if field is not None:
                fields.append((alias, name, field))

        self.subtables = subtables
        self.components = components

        rcomponents = resource.components

        # Customise subtables
        if subtables:
            if not request:
                # Create dummy S3Request
                from .s3rest import S3Request
                r = S3Request(resource.prefix,
                              resource.name,
                              # Current request args/vars could be in a different
                              # resource context, so must override them here:
                              args = [],
                              get_vars = {},
                              )
            else:
                r = request

            customise_resource = current.deployment_settings.customise_resource
            for alias in subtables:

                # Get tablename
                component = rcomponents.get(alias)
                if not component:
                    continue
                tablename = component.tablename

                # Run customise_resource
                customise = customise_resource(tablename)
                if customise:
                    customise(r, tablename)

                # Apply customised attributes to renamed fields
                # => except default, label, requires and widget, which can be overridden
                #    in S3SQLField.resolve instead
                renamed_fields = subtable_fields.get(alias)
                if renamed_fields:
                    table = component.table
                    for name, renamed_field in renamed_fields:
                        original_field = table[name]
                        for attr in ("comment",
                                     "default",
                                     "readable",
                                     "represent",
                                     "requires",
                                     "update",
                                     "writable",
                                     ):
                            setattr(renamed_field,
                                    attr,
                                    getattr(original_field, attr),
                                    )

        # Mark required fields with asterisk
        if not readonly:
            mark_required = self._config("mark_required", default=[])
            labels, required = s3_mark_required(self.table, mark_required)
            if required:
                # Show the key if there are any required fields.
                s3.has_required = True
            else:
                s3.has_required = False
        else:
            labels = None

        # Choose formstyle
        settings = s3.crud
        if format == "plain":
            # Simple formstyle works best when we have no formatting
            formstyle = "table3cols"
        elif readonly:
            formstyle = settings.formstyle_read
        else:
            formstyle = settings.formstyle

        # Retrieve the record
        record = None
        if record_id is not None:
            query = (self.table._id == record_id)
            # @ToDo: limit fields (at least not meta)
            record = db(query).select(limitby=(0, 1)).first()
        self.record_id = record_id
        self.subrows = Storage()

        # Populate the form
        data = None
        noupdate = []
        forbidden = []
        has_permission = current.auth.s3_has_permission

        if record is not None:

            # Retrieve the subrows
            subrows = self.subrows
            for alias in subtables:

                # Get the join for this subtable
                component = rcomponents.get(alias)
                if not component or component.multiple:
                    continue
                join = component.get_join()
                q = query & join

                # Retrieve the row
                # @todo: Should not need .ALL here
                row = db(q).select(component.table.ALL,
                                   limitby = (0, 1),
                                   ).first()

                # Check permission for this subrow
                ctname = component.tablename
                if not row:
                    permitted = has_permission("create", ctname)
                    if not permitted:
                        forbidden.append(alias)
                    continue
                else:
                    cid = row[component.table._id]
                    permitted = has_permission("read", ctname, cid)
                    if not permitted:
                        forbidden.append(alias)
                        continue
                    permitted = has_permission("update", ctname, cid)
                    if not permitted:
                        noupdate.append(alias)

                # Add the row to the subrows
                subrows[alias] = row

            # Build the data Storage for the form
            pkey = self.table._id
            data = Storage({pkey.name:record[pkey]})
            for alias, name, field in fields:

                if alias is None:
                    # Field in the master table
                    if name in record:
                        value = record[name]
                        # Field Method?
                        if callable(value):
                            value = value()
                        data[field.name] = value

                elif alias in subtables:
                    # Field in a subtable
                    if alias in subrows and \
                       subrows[alias] is not None and \
                       name in subrows[alias]:
                        data[field.name] = subrows[alias][name]

                elif hasattr(alias, "extract"):
                    # Form element with custom extraction method
                    data[field.name] = alias.extract(resource, record_id)

        else:
            # Record does not exist
            self.record_id = record_id = None

            # Check create-permission for subtables
            for alias in subtables:
                component = rcomponents.get(alias)
                if not component:
                    continue
                permitted = has_permission("create", component.tablename)
                if not permitted:
                    forbidden.append(alias)

        # Apply permissions for subtables
        fields = [f for f in fields if f[0] not in forbidden]
        for a, n, f in fields:
            if a:
                if a in noupdate:
                    f.writable = False
                if labels is not None and f.name not in labels:
                    if f.required:
                        flabels = s3_mark_required([f], mark_required=[f])[0]
                        labels[f.name] = flabels[f.name]
                    elif f.label:
                        labels[f.name] = "%s:" % f.label
                    else:
                        labels[f.name] = ""

        if readonly:
            # Strip all comments
            for a, n, f in fields:
                f.comment = None
        else:
            # Mark required subtable-fields (retaining override-labels)
            for alias in subtables:
                component = rcomponents.get(alias)
                if not component:
                    continue
                mark_required = component.get_config("mark_required", [])
                ctable = component.table
                sfields = dict((n, (f.name, f.label))
                               for a, n, f in fields
                               if a == alias and n in ctable)
                slabels = s3_mark_required([ctable[n] for n in sfields],
                                           mark_required=mark_required,
                                           map_names=sfields)[0]
                if labels:
                    labels.update(slabels)
                else:
                    labels = slabels

        self.subtables = [s for s in self.subtables if s not in forbidden]

        # Aggregate the form fields
        formfields = [f[-1] for f in fields]

        # Submit buttons
        buttons = self._submit_buttons(readonly)

        # Render the form
        tablename = self.tablename
        response.form_label_separator = ""
        form = SQLFORM.factory(record = data,
                               showid = False,
                               labels = labels,
                               formstyle = formstyle,
                               table_name = tablename,
                               upload = s3.download_url,
                               readonly = readonly,
                               separator = "",
                               submit_button = settings.submit_button,
                               buttons = buttons,
                               *formfields)

        # Style the Submit button, if-requested
        if settings.submit_style and not settings.custom_submit:
            try:
                form[0][-1][0][0]["_class"] = settings.submit_style
            except:
                # Submit button has been removed or a different formstyle,
                # such as Bootstrap (which is already styled anyway)
                pass

        # Subheadings
        subheadings = options.get("subheadings", None)
        if subheadings:
            self._insert_subheadings(form, tablename, formstyle, subheadings)

        # Process the form
        formname = "%s/%s" % (tablename, record_id)
        post_vars = request.post_vars
        if form.accepts(post_vars,
                        current.session,
                        onvalidation = self.validate,
                        formname = formname,
                        keepvalues = False,
                        hideerror = False,
                        ):

            # Undelete?
            if post_vars.get("_undelete"):
                undelete = post_vars.get("deleted") is False
            else:
                undelete = False

            link = options.get("link")
            hierarchy = options.get("hierarchy")
            self.accept(form,
                        format = format,
                        link = link,
                        hierarchy = hierarchy,
                        undelete = undelete,
                        )
            # Post-process the form submission after all records have
            # been accepted and linked together (self.accept() has
            # already updated the form data with any new keys here):
            postprocess = self.opts.get("postprocess", None)
            if postprocess:
                try:
                    callback(postprocess, form, tablename=tablename)
                except:
                    error = "postprocess failed: %s" % postprocess
                    current.log.error(error)
                    raise
            response.confirmation = message

        if form.errors:
            # Revert any records created within widgets/validators
            db.rollback()

            response.error = current.T("There are errors in the form, please check your input")

        return form

    # -------------------------------------------------------------------------
    def validate(self, form):
        """
            Run the onvalidation callbacks for the master table
            and all subtables in the form, and store any errors
            in the form.

            @param form: the form
        """

        s3db = current.s3db
        config = self._config

        # Validate against the main table
        if self.record_id:
            onvalidation = config("update_onvalidation",
                           config("onvalidation", None))
        else:
            onvalidation = config("create_onvalidation",
                           config("onvalidation", None))
        if onvalidation is not None:
            try:
                callback(onvalidation, form, tablename=self.tablename)
            except:
                error = "onvalidation failed: %s" % str(onvalidation)
                current.log.error(error)
                raise

        # Validate against all subtables
        get_config = s3db.get_config
        for alias in self.subtables:

            # Extract the subtable data
            subdata = self._extract(form, alias)
            if not subdata:
                continue

            # Get the onvalidation callback for this subtable
            subtable = self.resource.components[alias].table
            subform = Storage(vars=subdata, errors=Storage())

            rows = self.subrows
            if alias in rows and rows[alias] is not None:
                # Add the record ID for update-onvalidation
                pkey = subtable._id
                subform.vars[pkey.name] = rows[alias][pkey]
                subonvalidation = get_config(subtable._tablename,
                                             "update_onvalidation",
                                  get_config(subtable._tablename,
                                             "onvalidation", None))
            else:
                subonvalidation = get_config(subtable._tablename,
                                             "create_onvalidation",
                                  get_config(subtable._tablename,
                                             "onvalidation", None))

            # Validate against the subtable, store errors in form
            if subonvalidation is not None:
                try:
                    callback(subonvalidation, subform,
                             tablename = subtable._tablename)
                except:
                    error = "onvalidation failed: %s" % str(subonvalidation)
                    current.log.error(error)
                    raise
                for fn in subform.errors:
                    dummy = "sub_%s_%s" % (alias, fn)
                    form.errors[dummy] = subform.errors[fn]

        # Validate components (e.g. Inline-Forms)
        for component in self.components:
            if hasattr(component, "validate"):
                component.validate(form)

        return

    # -------------------------------------------------------------------------
    def accept(self,
               form,
               format=None,
               link=None,
               hierarchy=None,
               undelete=False):
        """
            Create/update all records from the form.

            @param form: the form
            @param format: data format extension (for audit)
            @param link: resource.link for linktable components
            @param hierarchy: the data for the hierarchy link to create
            @param undelete: reinstate a previously deleted record
        """

        db = current.db
        table = self.table

        # Create/update the main record
        main_data = self._extract(form)
        master_id, master_form_vars = self._accept(self.record_id,
                                                   main_data,
                                                   format = format,
                                                   link = link,
                                                   hierarchy = hierarchy,
                                                   undelete = undelete,
                                                   )
        if not master_id:
            return
        else:
            main_data[table._id.name] = master_id
            # Make sure lastid is set even if master has no data
            # (otherwise *_next redirection will fail)
            self.resource.lastid = str(master_id)

        # Create or update the subtables
        for alias in self.subtables:

            subdata = self._extract(form, alias=alias)
            if not subdata:
                continue

            component = self.resource.components[alias]
            subtable = component.table

            # Get the key (pkey) of the master record to link the
            # subtable record to, and update the subdata with it
            pkey = component.pkey
            if pkey != table._id.name and pkey not in main_data:
                row = db(table._id == master_id).select(table[pkey],
                                                        limitby=(0, 1)).first()
                if not row:
                    return
                main_data[pkey] = row[table[pkey]]
            if component.link:
                link = Storage(resource = component.link,
                               master = main_data,
                               )
            else:
                link = None
                subdata[component.fkey] = main_data[pkey]

            # Do we already have a record for this component?
            rows = self.subrows
            if alias in rows and rows[alias] is not None:
                # Yes => get the subrecord ID
                subid = rows[alias][subtable._id]
            else:
                # No => apply component defaults
                subid = None
                subdata = component.get_defaults(main_data,
                                                 data = subdata,
                                                 )
            # Accept the subrecord
            self._accept(subid,
                         subdata,
                         alias = alias,
                         link = link,
                         format = format,
                         )

        # Accept components (e.g. Inline-Forms)
        for item in self.components:
            if hasattr(item, "accept"):
                item.accept(form,
                            master_id = master_id,
                            format = format,
                            )

        # Update form with master form_vars
        form_vars = form.vars
        # ID
        form_vars[table._id.name] = master_id
        # Super entities (& anything added manually in table's onaccept)
        for var in master_form_vars:
            if var not in form_vars:
                form_vars[var] = master_form_vars[var]
        return

    # -------------------------------------------------------------------------
    # Utility functions
    # -------------------------------------------------------------------------
    def _extract(self, form, alias=None):
        """
            Extract data for a subtable from the form

            @param form: the form
            @param alias: the component alias of the subtable
        """

        if alias is None:
            return self.table._filter_fields(form.vars)
        else:
            subform = Storage()
            alias_length = len(alias)
            form_vars = form.vars
            for k in form_vars:
                if k[:4] == "sub_" and \
                   k[4:4 + alias_length + 1] == "%s_" % alias:
                    fn = k[4 + alias_length + 1:]
                    subform[fn] = form_vars[k]
            return subform

    # -------------------------------------------------------------------------
    def _accept(self,
                record_id,
                data,
                alias=None,
                format=None,
                hierarchy=None,
                link=None,
                undelete=False):
        """
            Create or update a record

            @param record_id: the record ID
            @param data: the data
            @param alias: the component alias
            @param format: the request format (for audit)
            @param hierarchy: the data for the hierarchy link to create
            @param link: resource.link for linktable components
            @param undelete: reinstate a previously deleted record
        """

        if alias is not None:
            # Subtable
            if not data or \
               not record_id and all(value is None for value in data.values()):
                # No data => skip
                return None, Storage()
        elif record_id and not data:
            # Existing master record, no data => skip, but return
            # record_id to allow update of inline-components:
            return record_id, Storage()

        s3db = current.s3db

        if alias is None:
            component = self.resource
        else:
            component = self.resource.components[alias]

        # Get the DB table (without alias)
        table = component.table
        tablename = component.tablename
        if component._alias != tablename:
            unaliased = s3db.table(component.tablename)
            # Must retain custom defaults of the aliased component:
            for field in table:
                field_ = unaliased[field.name]
                field_.default = field.default
                field_.update = field.update
            table = unaliased

        get_config = s3db.get_config

        oldrecord = None
        if record_id:
            # Update existing record
            accept_id = record_id
            db = current.db
            onaccept = get_config(tablename, "update_onaccept",
                       get_config(tablename, "onaccept", None))

            table_fields = table.fields
            query = (table._id == record_id)
            if onaccept:
                # Get oldrecord in full to save in form
                oldrecord = db(query).select(limitby=(0, 1)).first()
            elif "deleted" in table_fields:
                oldrecord = db(query).select(table.deleted,
                                             limitby=(0, 1)).first()
            else:
                oldrecord = None

            if undelete:
                # Restoring a previously deleted record
                if "deleted" in table_fields:
                    data["deleted"] = False
                if "created_by" in table_fields and current.auth.user:
                    data["created_by"] = current.auth.user.id
                if "created_on" in table_fields:
                    data["created_on"] = current.request.utcnow
            elif oldrecord and "deleted" in oldrecord and oldrecord.deleted:
                # Do not (ever) update a deleted record that we don't
                # want to restore, otherwise this may set foreign keys
                # in a deleted record!
                return accept_id
            db(table._id == record_id).update(**data)
        else:
            # Insert new record
            accept_id = table.insert(**data)
            if not accept_id:
                raise RuntimeError("Could not create record")
            onaccept = get_config(tablename, "create_onaccept",
                       get_config(tablename, "onaccept", None))

        data[table._id.name] = accept_id
        prefix, name = tablename.split("_", 1)
        form_vars = Storage(data)
        form = Storage(vars=form_vars, record=oldrecord)

        # Audit
        if record_id is None or undelete:
            current.audit("create", prefix, name, form=form,
                          representation=format)
        else:
            current.audit("update", prefix, name, form=form,
                          record=accept_id, representation=format)

        # Update super entity links
        s3db.update_super(table, form_vars)

        # Update component link
        if link and link.postprocess is None:
            resource = link.resource
            master = link.master
            resource.update_link(master, form_vars)

        if accept_id:
            if record_id is None or undelete:
                # Create hierarchy link
                if hierarchy:
                    from .s3hierarchy import S3Hierarchy
                    h = S3Hierarchy(tablename)
                    if h.config:
                        h.postprocess_create_node(hierarchy, form_vars)
                # Set record owner
                auth = current.auth
                auth.s3_set_record_owner(table, accept_id)
                auth.s3_make_session_owner(table, accept_id)
            else:
                # Update realm
                update_realm = get_config(table, "update_realm")
                if update_realm:
                    current.auth.set_realm_entity(table, form_vars,
                                                  force_update = True,
                                                  )

            # Store session vars
            component.lastid = str(accept_id)
            s3_store_last_record_id(tablename, accept_id)

            # Execute onaccept
            try:
                callback(onaccept, form, tablename=tablename)
            except:
                error = "onaccept failed: %s" % str(onaccept)
                current.log.error(error)
                # This is getting swallowed
                raise

        if alias is None:
            # Return master_form_vars
            return accept_id, form.vars
        else:
            return accept_id

# =============================================================================
class S3SQLFormElement(object):
    """ SQL Form Element Base Class """

    # -------------------------------------------------------------------------
    def __init__(self, selector, **options):
        """
            Constructor to define the form element, to be extended
            in subclass.

            @param selector: the data object selector
            @param options: options for the form element
        """

        self.selector = selector
        self.options = Storage(options)

    # -------------------------------------------------------------------------
    def resolve(self, resource):
        """
            Method to resolve this form element against the calling resource.
            To be implemented in subclass.

            @param resource: the resource
            @return: a tuple
                        (
                            form element,
                            original field name,
                            Field instance for the form renderer
                        )

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
    # Utility methods
    # -------------------------------------------------------------------------
    @staticmethod
    def _rename_field(field, name,
                      comments=True,
                      label=DEFAULT,
                      popup=None,
                      skip_post_validation=False,
                      widget=DEFAULT):
        """
            Rename a field (actually: create a new Field instance with the
            same attributes as the given Field, but a different field name).

            @param field: the original Field instance
            @param name: the new name
            @param comments: render comments - if set to False, only
                             navigation items with an inline() renderer
                             method will be rendered (unless popup is None)
            @param label: override option for the original field label
            @param popup: only if comments=False, additional vars for comment
                          navigation items (e.g. AddResourceLink), None prevents
                          rendering of navigation items
            @param skip_post_validation: skip field validation during POST,
                                         useful for client-side processed
                                         dummy fields.
            @param widget: override option for the original field widget
        """

        if label is DEFAULT:
            label = field.label
        if widget is DEFAULT:
            # Some widgets may need disabling during POST
            widget = field.widget

        if not hasattr(field, "type"):
            # Virtual Field
            field = Storage(comment=None,
                            type="string",
                            length=255,
                            unique=False,
                            uploadfolder=None,
                            autodelete=False,
                            label="",
                            writable=False,
                            readable=True,
                            default=None,
                            update=None,
                            compute=None,
                            represent=lambda v: v or "",
                            )
            requires = None
            required = False
            notnull = False
        elif skip_post_validation and \
             current.request.env.request_method == "POST":
            requires = SKIP_POST_VALIDATION(field.requires)
            required = False
            notnull = False
        else:
            requires = field.requires
            required = field.required
            notnull = field.notnull

        if not comments:
            if popup:
                comment = field.comment
                if hasattr(comment, "clone"):
                    comment = comment.clone()
                if hasattr(comment, "renderer") and \
                   hasattr(comment, "inline") and \
                   isinstance(popup, dict):
                    comment.vars.update(popup)
                    comment.renderer = comment.inline
                else:
                    comment = None
            else:
                comment = None
        else:
            comment = field.comment

        f = Field(str(name),
                  type = field.type,
                  length = field.length,

                  required = required,
                  notnull = notnull,
                  unique = field.unique,

                  uploadfolder = field.uploadfolder,
                  autodelete = field.autodelete,

                  comment = comment,
                  label = label,
                  widget = widget,

                  default = field.default,

                  writable = field.writable,
                  readable = field.readable,

                  update = field.update,
                  compute = field.compute,

                  represent = field.represent,
                  requires = requires)

        return f

# =============================================================================
class S3SQLField(S3SQLFormElement):
    """
        Base class for regular form fields

        A regular form field is a field in the main form, which can be
        fields in the main record or in a subtable (single-record-component).
    """

    # -------------------------------------------------------------------------
    def resolve(self, resource):
        """
            Method to resolve this form element against the calling resource.

            @param resource: the resource
            @return: a tuple
                        (
                            subtable alias (or None for main table),
                            original field name,
                            Field instance for the form renderer
                        )
        """

        # Import S3ResourceField only here, to avoid circular dependency
        from .s3query import S3ResourceField

        rfield = S3ResourceField(resource, self.selector)

        field = rfield.field
        if field is None:
            raise SyntaxError("Invalid selector: %s" % self.selector)

        tname = rfield.tname

        options_get = self.options.get
        label = options_get("label", DEFAULT)
        widget = options_get("widget", DEFAULT)

        if resource._alias:
            tablename = resource._alias
        else:
            tablename = resource.tablename

        if tname == tablename:
            # Field in the main table

            if label is not DEFAULT:
                field.label = label
            if widget is not DEFAULT:
                field.widget = widget

            return None, field.name, field

        else:
            for alias, component in resource.components.loaded.items():
                if component.multiple:
                    continue
                if component._alias:
                    tablename = component._alias
                else:
                    tablename = component.tablename
                if tablename == tname:
                    name = "sub_%s_%s" % (alias, rfield.fname)
                    renamed_field = self._rename_field(field,
                                                       name,
                                                       label = label,
                                                       widget = widget,
                                                       )
                    return alias, field.name, renamed_field

            raise SyntaxError("Invalid subtable: %s" % tname)

# =============================================================================
class S3SQLVirtualField(S3SQLFormElement):
    """
        A form element to embed values of field methods (virtual fields),
        always read-only
    """

    # -------------------------------------------------------------------------
    def resolve(self, resource):
        """
            Method to resolve this form element against the calling resource.

            @param resource: the resource
            @return: a tuple
                        (
                            subtable alias (or None for main table),
                            original field name,
                            Field instance for the form renderer
                        )
        """

        table = resource.table
        selector = self.selector

        if not hasattr(table, selector):
            raise SyntaxError("Undefined virtual field: %s" % selector)

        label = self.options.label
        if not label:
            label = " ".join(s.capitalize() for s in selector.split("_"))

        field = Field(selector,
                      label = label,
                      widget = self,
                      )

        return None, selector, field

    # -------------------------------------------------------------------------
    def __call__(self, field, value, **attributes):
        """
            Widget renderer for field method values, renders a simple
            read-only DIV with the value
        """

        widget = DIV(value, **attributes)
        widget.add_class("s3-virtual-field")

        return widget

# =============================================================================
class S3SQLDummyField(S3SQLFormElement):
    """
        A Dummy Field

        A simple DIV which can then be acted upon with JavaScript
        - used by dc_question Grids
    """

    # -------------------------------------------------------------------------
    def resolve(self, resource):
        """
            Method to resolve this form element against the calling resource.

            @param resource: the resource
            @return: a tuple
                        (
                            subtable alias (or None for main table),
                            original field name,
                            Field instance for the form renderer
                        )
        """

        selector = self.selector

        field = Field(selector,
                      default = "",
                      label = "",
                      widget = self,
                      )

        return None, selector, field

    # -------------------------------------------------------------------------
    def __call__(self, field, value, **attributes):
        """
            Widget renderer for the input field. To be implemented in
            subclass (if required) and to be set as widget=self for the
            field returned by the resolve()-method of this form element.

            @param field: the input field
            @param value: the value to populate the widget
            @param attributes: attributes for the widget
            @return: the widget for this form element as HTML helper
        """

        return DIV(_class="s3-dummy-field",
                   )

# =============================================================================
class S3SQLSectionBreak(S3SQLFormElement):
    """
        A Section Break

        A simple DIV which can then be acted upon with JavaScript &/or Styled
        - used by dc_template.layout
    """

    # -------------------------------------------------------------------------
    def __init__(self):
        """
            Constructor to define the form element, to be extended
            in subclass.
        """

        super(S3SQLSectionBreak, self).__init__(None)

    # -------------------------------------------------------------------------
    def resolve(self, resource):
        """
            Method to resolve this form element against the calling resource.

            @param resource: the resource
            @return: a tuple
                        (
                            subtable alias (or None for main table),
                            original field name,
                            Field instance for the form renderer
                        )
        """

        selector = ""

        field = Field(selector,
                      default = "",
                      label = "",
                      widget = self,
                      )

        return None, selector, field

    # -------------------------------------------------------------------------
    def __call__(self, field, value, **attributes):
        """
            Widget renderer for the input field. To be implemented in
            subclass (if required) and to be set as widget=self for the
            field returned by the resolve()-method of this form element.

            @param field: the input field
            @param value: the value to populate the widget
            @param attributes: attributes for the widget
            @return: the widget for this form element as HTML helper
        """

        return DIV(_class="s3-section-break",
                   )

# =============================================================================
class S3SQLInlineInstruction(S3SQLFormElement):
    """
        Inline Instructions

        A simple DIV which can then be acted upon with JavaScript &/or Styled
        - used by dc_template.layout
    """

    # -------------------------------------------------------------------------
    def __init__(self, do, say, **options):
        """
            Constructor to define the form element, to be extended
            in subclass.

            @param do: What to Do
            @param say: What to Say
        """

        super(S3SQLInlineInstruction, self).__init__(None)

        self.do = do
        self.say = say

    # -------------------------------------------------------------------------
    def resolve(self, resource):
        """
            Method to resolve this form element against the calling resource.

            @param resource: the resource
            @return: a tuple
                        (
                            subtable alias (or None for main table),
                            original field name,
                            Field instance for the form renderer
                        )
        """

        selector = ""

        field = Field(selector,
                      default = "",
                      label = "",
                      widget = self,
                      )

        return None, selector, field

    # -------------------------------------------------------------------------
    def __call__(self, field, value, **attributes):
        """
            Widget renderer for the input field. To be implemented in
            subclass (if required) and to be set as widget=self for the
            field returned by the resolve()-method of this form element.

            @param field: the input field
            @param value: the value to populate the widget
            @param attributes: attributes for the widget
            @return: the widget for this form element as HTML helper
        """

        element = DIV(_class="s3-inline-instructions",
                      )
        element["data-do"] = self.do
        element["data-say"] = self.say
        return element

# =============================================================================
class S3SQLSubForm(S3SQLFormElement):
    """
        Base class for subforms

        A subform is a form element to be processed after the main
        form. Subforms render a single (usually hidden) input field
        and a client-side controlled widget to manipulate its contents.
    """

    # -------------------------------------------------------------------------
    def extract(self, resource, record_id):
        """
            Initialize this form element for a particular record. This
            method will be called by the form renderer to populate the
            form for an existing record. To be implemented in subclass.

            @param resource: the resource the record belongs to
            @param record_id: the record ID

            @return: the value for the input field that corresponds
                      to the specified record.
        """

        return None

    # -------------------------------------------------------------------------
    def parse(self, value):
        """
            Validator method for the input field, used to extract the
            data from the input field and prepare them for further
            processing by the accept()-method. To be implemented in
            subclass and set as requires=self.parse for the input field
            in the resolve()-method of this form element.

            @param value: the value returned from the input field
            @return: tuple of (value, error) where value is the
                      pre-processed field value and error an error
                      message in case of invalid data, or None.
        """

        return (value, None)

    # -------------------------------------------------------------------------
    def __call__(self, field, value, **attributes):
        """
            Widget renderer for the input field. To be implemented in
            subclass (if required) and to be set as widget=self for the
            field returned by the resolve()-method of this form element.

            @param field: the input field
            @param value: the value to populate the widget
            @param attributes: attributes for the widget
            @return: the widget for this form element as HTML helper
        """

        raise NotImplementedError

    # -------------------------------------------------------------------------
    def represent(self, value):
        """
            Read-only representation of this form element. This will be
            used instead of the __call__() method when the form element
            is to be rendered read-only.

            @param value: the value as returned from extract()
            @return: the read-only representation of this element as
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

            @param form: the form
            @param master_id: the master record ID
            @param format: the data format extension
            @return: True on success, False on error
        """

        return True

# =============================================================================
class SKIP_POST_VALIDATION(Validator):
    """
        Pseudo-validator that allows introspection of field options
        during GET, but does nothing during POST. Used for Ajax-validated
        inline-components to prevent them from throwing validation errors
        when the outer form gets submitted.
    """

    def __init__(self, other=None):
        """
            Constructor, used like:
            field.requires = SKIP_POST_VALIDATION(field.requires)

            @param other: the actual field validator
        """

        if other and isinstance(other, (list, tuple)):
            other = other[0]
        self.other = other
        if other:
            if hasattr(other, "multiple"):
                self.multiple = other.multiple
            if hasattr(other, "options"):
                self.options = other.options
            if hasattr(other, "formatter"):
                self.formatter = other.formatter

    def __call__(self, value):
        """
            Validation

            @param value: the value
        """

        other = self.other
        if current.request.env.request_method == "POST" or not other:
            return value, None
        if not isinstance(other, (list, tuple)):
            other = [other]
        for r in other:
            value, error = r(value)
            if error:
                return value, error
        return value, None

# =============================================================================
class S3SQLSubFormLayout(object):
    """ Layout for S3SQLInlineComponent (Base Class) """

    # Layout-specific CSS class for the inline component
    layout_class = "subform-default"

    def __init__(self):
        """ Constructor """

        self.inject_script()
        self.columns = None
        self.row_actions = True

    # -------------------------------------------------------------------------
    def set_columns(self, columns, row_actions=True):
        """
            Set column widths for inline-widgets, can be used by subclasses
            to render CSS classes for grid-width

            @param columns: iterable of column widths
            @param actions: whether the subform contains an action column
        """

        self.columns = columns
        self.row_actions = row_actions

    # -------------------------------------------------------------------------
    def subform(self,
                data,
                item_rows,
                action_rows,
                empty=False,
                readonly=False):
        """
            Outer container for the subform

            @param data: the data dict (as returned from extract())
            @param item_rows: the item rows
            @param action_rows: the (hidden) action rows
            @param empty: no data in this component
            @param readonly: render read-only
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

            @param resource: the S3Resource
            @param data: the data dict (as returned from extract())
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

            @param resource: the S3Resource
            @param data: the data dict (as returned from extract())
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
                   _class="embeddedComponent",
                   )

    # -------------------------------------------------------------------------
    def headers(self, data, readonly=False):
        """
            Render the header row with field labels

            @param data: the input field data as Python object
            @param readonly: whether the form is read-only
        """

        fields = data["fields"]

        # Don't render a header row if there are no labels
        render_header = False
        header_row = TR(_class="label-row static")
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
            return THEAD(_class="hide")

    # -------------------------------------------------------------------------
    @staticmethod
    def actions(subform,
                formname,
                index,
                item = None,
                readonly=True,
                editable=True,
                deletable=True):
        """
            Render subform row actions into the row

            @param subform: the subform row
            @param formname: the form name
            @param index: the row index
            @param item: the row data
            @param readonly: this is a read-row
            @param editable: this row is editable
            @param deletable: this row is deletable
        """

        T = current.T
        action_id = "%s-%s" % (formname, index)

        # Action button helper
        def action(title, name, throbber=False):
            btn = DIV(_id="%s-%s" % (name, action_id),
                      _class="inline-%s" % name)
            if throbber:
                return DIV(btn,
                        DIV(_class="inline-throbber hide",
                            _id="throbber-%s" % action_id))
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
class S3SQLVerticalSubFormLayout(S3SQLSubFormLayout):
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

        headers = super(S3SQLVerticalSubFormLayout, self).headers

        header_row = headers(data, readonly = readonly)
        element = header_row.element('tr')
        if hasattr(element, "remove_class"):
            element.remove_class("static")
        return header_row

    # -------------------------------------------------------------------------
    def rowstyle_read(self, form, fields, *args, **kwargs):
        """
            Formstyle for subform read-rows, same as standard
            horizontal layout.
        """

        rowstyle = super(S3SQLVerticalSubFormLayout, self).rowstyle
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
class S3SQLInlineComponent(S3SQLSubForm):
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

        @ToDo: Support filtering of field options
               Usecase is inline project_organisation for IFRC
               PartnerNS needs to be filtered differently from Partners/Donors,
               so can't just set a global requires for the field in the controller
               - needs to be inside the widget.
               See private/templates/IFRC/config.py
    """

    prefix = "sub"

    # -------------------------------------------------------------------------
    def resolve(self, resource):
        """
            Method to resolve this form element against the calling resource.

            @param resource: the resource
            @return: a tuple (self, None, Field instance)
        """

        selector = self.selector

        # Check selector
        try:
            component = resource.components[selector]
        except KeyError:
            raise SyntaxError("Undefined component: %s" % selector)

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
            Initialize this form element for a particular record. Retrieves
            the component data for this record from the database and
            converts them into a JSON string to populate the input field with.

            @param resource: the resource the record belongs to
            @param record_id: the record ID

            @return: the JSON for the input field.
        """

        self.resource = resource

        component_name = self.selector
        try:
            component = resource.components[component_name]
        except KeyError:
            raise AttributeError("Undefined component")

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
                if isinstance(widget, S3Selector):
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

        return json.dumps(data, separators=SEPARATORS)

    # -------------------------------------------------------------------------
    def parse(self, value):
        """
            Validator method, converts the JSON returned from the input
            field into a Python object.

            @param value: the JSON from the input field.
            @return: tuple of (value, error), where value is the converted
                      JSON, and error the error message if the decoding
                      fails, otherwise None
        """

        # @todo: catch uploads during validation errors
        if isinstance(value, basestring):
            try:
                value = json.loads(value)
            except:
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

            @param field: the Field for this form element
            @param value: the current value for this field
            @param attributes: keyword attributes for this widget
        """

        T = current.T
        settings = current.deployment_settings

        options = self.options
        if options.readonly is True:
            # Render read-only
            return self.represent(value)

        if value is None:
            value = field.default
        if isinstance(value, basestring):
            data = json.loads(value)
        else:
            data = value
            value = json.dumps(value, separators=SEPARATORS)
        if data is None:
            raise SyntaxError("No resource structure information")

        self.upload = Storage()

        if options.multiple is False:
            multiple = False
        else:
            multiple = True

        required = options.get("required", False)

        # Get the table
        resource = self.resource
        component_name = data["component"]
        component = resource.components[component_name]
        table = component.table

        # @ToDo: Hide completely if the user is not permitted to read this
        # component

        formname = self._formname()

        fields = data["fields"]
        items = data["data"]

        # Flag whether there are any rows (at least an add-row) in the widget
        has_rows = False

        # Add the item rows
        item_rows = []
        prefix = component.prefix
        name = component.name
        audit = current.audit
        has_permission = current.auth.s3_has_permission
        tablename = component.tablename

        # Configure the layout
        layout = self._layout()
        columns = self.options.get("columns")
        if columns:
            layout.set_columns(columns, row_actions = multiple)

        get_config = current.s3db.get_config
        _editable = get_config(tablename, "editable")
        if _editable is None:
            _editable = True
        _deletable = get_config(tablename, "deletable")
        if _deletable is None:
            _deletable = True
        _class = "read-row inline-form"
        if not multiple:
            # Mark to client-side JS that we should open Edit Row
            _class = "%s single" % _class
        item = None
        for i in xrange(len(items)):
            has_rows = True
            item = items[i]
            # Get the item record ID
            if "_delete" in item and item["_delete"]:
                continue
            elif "_id" in item:
                record_id = item["_id"]
                # Check permissions to edit this item
                if _editable:
                    editable = has_permission("update", tablename, record_id)
                else:
                    editable = False
                if _deletable:
                    deletable = has_permission("delete", tablename, record_id)
                else:
                    deletable = False
            else:
                record_id = None
                if _editable:
                    editable = True
                else:
                    editable = False
                if _deletable:
                    deletable = True
                else:
                    deletable = False

            # Render read-row accordingly
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
            if record_id:
                audit("read", prefix, name,
                      record = record_id,
                      representation = "html",
                      )
            item_rows.append(read_row)

        # Add the action rows
        action_rows = []

        # Edit-row
        _class = "edit-row inline-form hide"
        if required and has_rows:
            _class = "%s required" % _class
        if not multiple:
            _class = "%s single" % _class
        edit_row = self._render_item(table, item, fields,
                                     editable = _editable,
                                     deletable = _deletable,
                                     readonly = False,
                                     multiple = multiple,
                                     index = 0,
                                     layout = layout,
                                     _id = "edit-row-%s" % formname,
                                     _class = _class,
                                     )
        action_rows.append(edit_row)

        # Add-row
        inline_open_add = ""
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
                if has_rows:
                    # Add Rows not relevant
                    _class = "%s hide" % _class
                else:
                    # Mark to client-side JS that we should always validate
                    _class = "%s single" % _class
            if required and not has_rows:
                explicit_add = False
                _class = "%s required" % _class
            # Explicit open-action for add-row (optional)
            if explicit_add:
                # Hide add-row for explicit open-action
                _class = "%s hide" % _class
                if explicit_add is True:
                    label = T("Add another")
                else:
                    label = explicit_add
                inline_open_add = A(label,
                                    _class="inline-open-add action-lnk",
                                    )
            has_rows = True
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
                                      editable = _editable,
                                      deletable = _deletable,
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
                                      editable = _editable,
                                      deletable = _deletable,
                                      readonly = True,
                                      multiple = multiple,
                                      index = "none",
                                      layout = layout,
                                      _id = "empty-read-row-%s" % formname,
                                      _class = "empty-row inline-form hide",
                                      )
        action_rows.append(empty_row)

        # Real input: a hidden text field to store the JSON data
        real_input = "%s_%s" % (resource.tablename, field.name)
        default = {"_type": "hidden",
                   "_value": value,
                   "requires": lambda v: (v, None),
                   }
        attr = StringWidget._attributes(field, default, **attributes)
        attr["_class"] = "%s hide" % attr["_class"]
        attr["_id"] = real_input

        widget = layout.subform(data,
                                item_rows,
                                action_rows,
                                empty = not has_rows,
                                )

        if self.upload:
            hidden = DIV(_class="hidden", _style="display:none")
            for k, v in self.upload.items():
                hidden.append(INPUT(_type = "text",
                                    _id = k,
                                    _name = k,
                                    _value = v,
                                    _style = "display:none",
                                    ))
        else:
            hidden = ""

        # Render output HTML
        output = DIV(INPUT(**attr),
                     hidden,
                     widget,
                     inline_open_add,
                     _id = self._formname(separator="-"),
                     _field = real_input,
                     _class = "inline-component",
                     )

        # Reset the layout
        layout.set_columns(None)

        # Script options
        js_opts = {"implicitCancelEdit": settings.get_ui_inline_cancel_edit(),
                   "confirmCancelEdit": s3_str(T("Discard changes?")),
                   }
        script = '''S3.inlineComponentsOpts=%s''' % json.dumps(js_opts)
        js_global = current.response.s3.js_global
        if script not in js_global:
            js_global.append(script)

        return output

    # -------------------------------------------------------------------------
    def represent(self, value):
        """
            Read-only representation of this sub-form

            @param value: the value returned from extract()
        """

        if isinstance(value, basestring):
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
            Post-processes this form element against the POST data of the
            request, and create/update/delete any related records.

            @param form: the form
            @param master_id: the ID of the master record in the form
            @param format: the data format extension (for audit)
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
                return
            component_name = data.get("component", None)
            if not component_name:
                return
            data = data.get("data", None)
            if not data:
                return

            # Get the component
            resource = self.resource
            component = resource.components.get(component_name)
            if not component:
                return

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
                            elif field.type == "upload":
                                # Find, rename and store the uploaded file
                                rowindex = item.get("_index", None)
                                if rowindex is not None:
                                    filename = self._store_file(table, f, rowindex)
                                    if filename:
                                        values[f] = filename
                            elif isinstance(widget, S3Selector):
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

                    elif not component.multiple or not multiple:
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
                                                  limitby=(0, 1)).first()
                        if not master:
                            return
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
                                                          limitby=(0, 1)
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
                                                               limitby=(0, 1)
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
            Generate a string representing the formname

            @param separator: separator to prepend a prefix
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
        """ Get the current layout """

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
                     readonly=True,
                     editable=False,
                     deletable=False,
                     multiple=True,
                     index="none",
                     layout=None,
                     **attributes):
        """
            Render a read- or edit-row.

            @param table: the database table
            @param item: the data
            @param fields: the fields to render (list of strings)
            @param readonly: render a read-row (otherwise edit-row)
            @param editable: whether the record can be edited
            @param deletable: whether the record can be deleted
            @param multiple: whether multiple records can be added
            @param index: the row index
            @param layout: the subform layout (S3SQLSubFormLayout)
            @param attributes: HTML attributes for the row
        """

        s3 = current.response.s3

        rowtype = readonly and "read" or "edit"
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
                                           skip_post_validation = True,
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
                    formfield.requires = SKIP_POST_VALIDATION(requires)

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
                    if type(value) is unicodeT:
                        value = s3_str(value)
                    widget = formfield.widget
                    if isinstance(widget, S3Selector):
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
                                  record=data,
                                  showid=False,
                                  formstyle=rowstyle,
                                  upload = s3.download_url,
                                  readonly=readonly,
                                  table_name=subform_name,
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
            Render the filterby-options as Query to apply when retrieving
            the existing rows in this inline-component
        """

        filterby = self.options["filterby"]
        if not filterby:
            return
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
            Render the defaults for this inline-component as a dict
            for the real-input JSON
        """

        filterby = self.options.get("filterby")
        if filterby is None:
            return None

        if not isinstance(filterby, (list, tuple)):
            filterby = [filterby]

        component = self.resource.components[self.selector]
        table = component.table

        defaults = dict()
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
                    else:
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
            Re-render the options list for a field if there is a
            filterby-restriction.

            @param fieldname: the name of the field
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
            Find, rename and store an uploaded file and return it's
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

            elif isinstance(f, basestring):
                # Previously uploaded file
                return f

        return None

# =============================================================================
class S3SQLInlineLink(S3SQLInlineComponent):
    """
        Subform to edit link table entries for the master record

        Constructor options:

            ** Common options:

            readonly..........True|False......render read-only always
            multiple..........True|False......allow selection of multiple
                                              options (default True)
            widget............string..........which widget to use, one of:
                                              - multiselect (default)
                                              - groupedopts (default when cols is specified)
                                              - hierarchy   (requires hierarchical lookup-table)
                                              - cascade     (requires hierarchical lookup-table)
            render_list.......True|False......in read-only mode, render HTML
                                              list rather than comma-separated
                                              strings (default False)

            ** Options for groupedopts widget:

            cols..............integer.........number of columns for grouped
                                              options (default: None)
            orientation.......string..........orientation for grouped options
                                              order, one of:
                                                  - cols
                                                  - rows
            size..............integer.........maximum number of items per group
                                              in grouped options, None to disable
                                              grouping
            sort..............True|False......sort grouped options (always True
                                              when grouping, i.e. size!=None)
            help_field........string..........additional field in the look-up
                                              table to render as tooltip for
                                              grouped options
            table.............True|False......render grouped options as HTML
                                              TABLE rather than nested DIVs
                                              (default True)

            ** Options for multi-select widget:

            header............True|False......multi-select to show a header with
                                              bulk-select options and optional
                                              search-field
            search............True|False......show the search-field in the header
            selectedList......integer.........how many items to show on multi-select
                                              button before collapsing into number
            noneSelectedText..string..........placeholder text on multi-select button
            columns...........integer.........Foundation column-width for the
                                              widget (for custom forms)
            create............dict............Options to create a new record {"c": "controller",
                                                                              "f": "function",
                                                                              "label": "label",
                                                                              "parent": "parent", (optional: which function to lookup options from)
                                                                              "child": "child", (optional: which field to lookup options for)
                                                                              }

            ** Options-filtering:
               - multiselect and groupedopts only
               - for hierarchy and cascade widgets, use the "filter" option

            requires..........Validator.......validator to determine the
                                              selectable options (defaults to
                                              field validator)
            filterby..........field selector..filter look-up options by this field
                                              (can be a field in the look-up table
                                              itself or in another table linked to it)
            options...........value|list......filter for these values, or:
            match.............field selector..lookup the filter value from this
                                              field (can be a field in the master
                                              table, or in linked table)

            ** Options for hierarchy and cascade widgets:

            levels............list............ordered list of labels for hierarchy
                                              levels (top-down order), to override
                                              the lookup-table's "hierarchy_levels"
                                              setting, cascade-widget only
            represent.........callback........representation method for hierarchy
                                              nodes (defaults to field represent)
            leafonly..........True|False......only leaf nodes can be selected
            cascade...........True|False......automatically select the entire branch
                                              when a parent node is newly selected;
                                              with multiple=False, this will
                                              auto-select single child options
                                              (default True when leafonly=True)
            filter............resource query..filter expression to filter the
                                              selectable options
    """

    prefix = "link"

    # -------------------------------------------------------------------------
    def extract(self, resource, record_id):
        """
            Get all existing links for record_id.

            @param resource: the resource the record belongs to
            @param record_id: the record ID

            @return: list of component record IDs this record is
                     linked to via the link table
        """

        self.resource = resource
        component, link = self.get_link()

        # Customise resources
        from .s3rest import S3Request
        r = S3Request(resource.prefix,
                      resource.name,
                      # Current request args/vars could be in a different
                      # resource context, so must override them here:
                      args = [],
                      get_vars = {},
                      )
        customise_resource = current.deployment_settings.customise_resource
        for tablename in (component.tablename, link.tablename):
            customise = customise_resource(tablename)
            if customise:
                customise(r, tablename)

        self.initialized = True
        if record_id:
            rkey = component.rkey
            rows = link.select([rkey], as_rows=True)
            if rows:
                rkey = str(link.table[rkey])
                values = [row[rkey] for row in rows]
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

            @param field: the input field
            @param value: the value to populate the widget
            @param attributes: attributes for the widget

            @return: the widget
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
                zero = None if multiple else options.get("zero", XML("&nbsp"))
                opts = self.get_options()
                if zero is None:
                    # Remove the empty option
                    opts = {k: v for k, v in opts.items() if k != ""}
                requires = IS_IN_SET(opts,
                                     multiple=multiple,
                                     zero=zero,
                                     sort=options.get("sort", True))
                if zero is not None:
                    requires = IS_EMPTY_OR(requires)
            dummy_field.requires = requires

        # Helper to extract widget options
        widget_opts = lambda keys: {k: v for k, v in options.items() if k in keys}

        # Instantiate the widget
        if widget == "groupedopts" or not widget and "cols" in options:
            from .s3widgets import S3GroupedOptionsWidget
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
            from .s3widgets import S3HierarchyWidget
            w_opts = widget_opts(("multiple",
                                  "filter",
                                  "leafonly",
                                  "cascade",
                                  "represent",
                                  ))
            w_opts["lookup"] = component.tablename
            w = S3HierarchyWidget(**w_opts)
        elif widget == "cascade":
            from .s3widgets import S3CascadeSelectWidget
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
            from .s3widgets import S3MultiSelectWidget
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

            @param form: the form
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

            @param form: the master form
            @param master_id: the ID of the master record in the form
            @param format: the data format extension (for audit)

            @todo: implement audit
        """

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

                # Delete links which are no longer used
                # @todo: apply filterby to only delete within the subset?
                if delete:
                    query &= FS(component.rkey).belongs(delete)
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

            @param value: the value as returned from extract()
            @return: the read-only representation
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
            from .s3fields import S3Represent
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
    def get_options(self):
        """
            Get the options for the widget

            @return: dict {value: representation} of options
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
            except:
                pass

        # Filter these options?
        widget_opts = self.options
        filterby = widget_opts.get("filterby")
        filteropts = widget_opts.get("options")
        filterexpr = widget_opts.get("match")

        if filterby and \
           (filteropts is not None or filterexpr and resource._rows):

            # filterby is a field selector for the component
            # that shall match certain conditions
            filter_selector = FS(filterby)
            filter_query = None

            if filteropts is not None:
                # filterby-field shall match one of the given filteropts
                if isinstance(filteropts, (list, tuple, set)):
                    filter_query = (filter_selector.belongs(list(filteropts)))
                else:
                    filter_query = (filter_selector == filteropts)

            elif filterexpr:
                # filterby-field shall match one of the values for the
                # filterexpr-field of the master record
                rfield = resource.resolve_selector(filterexpr)
                colname = rfield.colname

                rows = resource.select([filterexpr], as_rows=True)
                values = set(row[colname] for row in rows)
                values.discard(None)

                if values:
                    filter_query = (filter_selector.belongs(values)) | \
                                   (filter_selector == None)

            # Select the filtered component rows
            filter_resource = current.s3db.resource(component.tablename,
                                                    filter = filter_query)
            rows = filter_resource.select(["id"], as_rows=True)

            filtered_opts = []
            values = set(str(row[component.table._id]) for row in rows)
            for opt in opts:
                if str(opt[0]) in values:
                    filtered_opts.append(opt)
            opts = filtered_opts

        return dict(opts)

    # -------------------------------------------------------------------------
    def get_link(self):
        """
            Find the target component and its linktable

            @return: tuple of S3Resource instances (component, link)
        """

        selector = self.selector
        try:
            component = self.resource.components[selector]
        except KeyError:
            raise SyntaxError("Undefined component: %s" % selector)

        link = component.link
        if not link:
            # @todo: better error message
            raise SyntaxError("No linktable for %s" % selector)

        return (component, link)

# END =========================================================================
