# -*- coding: utf-8 -*-

""" S3 SQL Forms

    @copyright: 2012-14 (c) Sahana Software Foundation
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
           "S3SQLSubFormLayout",
           "S3SQLInlineComponent",
           "S3SQLInlineComponentCheckbox",
           "S3SQLInlineComponentMultiSelectWidget",
           "S3SQLInlineLink",
           )

from itertools import chain

try:
    import json # try stdlib (Python 2.6+)
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
from gluon.sqlhtml import StringWidget
from gluon.tools import callback
from gluon.validators import Validator

from s3query import FS
from s3utils import s3_mark_required, s3_represent_value, s3_store_last_record_id, s3_strip_markup, s3_unicode, s3_validate

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

        for element in elements:
            if isinstance(element, S3SQLFormElement):
                append(element)
            elif isinstance(element, str):
                append(S3SQLField(element))
            else:
                raise SyntaxError("Invalid form element: %s" % str(element))

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
    def _insert_subheadings(form, tablename, subheadings):
        """
            Insert subheadings into forms

            @param form: the form
            @param tablename: the tablename
            @param subheadings: a dict of {"Headline": Fieldnames}, where
                Fieldname can be either a single field name or a list/tuple
                of field names belonging under that headline
        """

        if subheadings:
            if tablename in subheadings:
                subheadings = subheadings.get(tablename)
            form_rows = iter(form[0])
            tr = form_rows.next()
            i = 0
            done = []
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
                    for k in subheadings.keys():
                        if k in done:
                            continue
                        fields = subheadings[k]
                        if not isinstance(fields, (list, tuple)):
                            fields = [fields]
                        if f in fields:
                            done.append(k)
                            if isinstance(k, int):
                                # Don't display a section title
                                represent = ""
                            else:
                                represent = k
                            form[0].insert(i, TR(TD(represent, _colspan=3,
                                                    _class="subheading"),
                                                 _class = "subheading",
                                                 _id = "%s_%s__subheading" %
                                                       (tablename, f)))
                            tr.attributes.update(_class="after_subheading")
                            tr = form_rows.next()
                            i += 1
                try:
                    tr = form_rows.next()
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

            # Pre-populate create-form?
            if record_id is None:
                data = options.get("data", None)
                from_table = options.get("from_table", None)
                from_record = options.get("from_record", None)
                map_fields = options.get("map_fields", None)
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
            self._insert_subheadings(form, tablename, subheadings)

        # Process the form
        logged = False
        if not readonly:
            _get = options.get
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
                _lkey = post_vars[lkey]
                _rkey = post_vars[rkey]
                query = (table[lkey] == _lkey) & (table[rkey] == _rkey)
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

            # Audit
            prefix = self.prefix
            name = self.name
            if record_id is None:
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
                if record_id is None:
                    # Create hierarchy link
                    if hierarchy:
                        from s3hierarchy import S3Hierarchy
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
                error = "onaccept failed: %s" % onaccept
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
        fields = []
        subtables = []
        components = []
        for element in self.elements:
            alias, name, field = element.resolve(resource)
            if field is not None:
                fields.append((alias, name, field))
            if isinstance(alias, str):
                if alias not in subtables:
                    subtables.append(alias)
            elif isinstance(alias, S3SQLFormElement):
                components.append(alias)
        self.subtables = subtables
        self.components = components

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

        rcomponents = resource.components

        if record is not None:

            # Retrieve the subrows
            subrows = self.subrows
            for alias in subtables:

                # Get the join for this subtable
                component = rcomponents[alias]
                if component.multiple:
                    continue
                join = component.get_join()
                q = query & join

                # Retrieve the row
                # @todo: Should not need .ALL here
                row = db(q).select(component.table.ALL,
                                   limitby=(0, 1)).first()

                # Check permission for this subrow
                ctname = component.tablename
                if not row:
                    component = rcomponents[alias]
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
                    if name in record:
                        data[field.name] = record[name]
                elif alias in subtables:
                    if alias in subrows and \
                       subrows[alias] is not None and \
                       name in subrows[alias]:
                        data[field.name] = subrows[alias][name]
                elif hasattr(alias, "extract"):
                    data[field.name] = alias.extract(resource, record_id)

        else:
            # Record does not exist
            self.record_id = record_id = None

            # Check create-permission for subtables
            for alias in subtables:
                if alias in rcomponents:
                    component = rcomponents[alias]
                else:
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
                if alias in rcomponents:
                    component = rcomponents[alias]
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
        form = SQLFORM.factory(*formfields,
                               record = data,
                               showid = False,
                               labels = labels,
                               formstyle = formstyle,
                               table_name = tablename,
                               upload = s3.download_url,
                               readonly = readonly,
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
            self._insert_subheadings(form, tablename, subheadings)

        # Process the form
        formname = "%s/%s" % (tablename, record_id)
        if form.accepts(request.post_vars,
                        current.session,
                        onvalidation=self.validate,
                        formname=formname,
                        keepvalues=False,
                        hideerror=False):

            link = options.get("link")
            hierarchy = options.get("hierarchy")
            self.accept(form, format=format, link=link, hierarchy=hierarchy)
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
                error = "onvalidation failed: %s" % onvalidation
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
                #subid = rows[alias][subtable._id]
                subonvalidation = get_config(subtable._tablename,
                                             "update_onvalidation",
                                  get_config(subtable._tablename,
                                             "onvalidation", None))
            else:
                #subid = None
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
                    error = "onvalidation failed: %s" % subonvalidation
                    current.log.error(error)
                    raise
                for fn in subform.errors:
                    dummy = "sub_%s_%s" % (alias, fn)
                    form.errors[dummy] = subform.errors[fn]

        return

    # -------------------------------------------------------------------------
    def accept(self, form, format=None, link=None, hierarchy=None):
        """
            Create/update all records from the form.

            @param form: the form
            @param format: data format extension (for audit)
            @param link: resource.link for linktable components
            @param hierarchy: the data for the hierarchy link to create
        """

        db = current.db
        table = self.table

        # Create/update the main record
        main_data = self._extract(form)
        master_id, master_form_vars = self._accept(self.record_id,
                                                   main_data,
                                                   format=format,
                                                   link=link,
                                                   hierarchy=hierarchy,
                                                   )
        if not master_id:
            return
        else:
            main_data[table._id.name] = master_id

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
            subdata[component.fkey] = main_data[pkey]

            # Do we already have a record for this component?
            # If yes, then get the subrecord ID
            rows = self.subrows
            if alias in rows and rows[alias] is not None:
                subid = rows[alias][subtable._id]
            else:
                subid = None

            # Accept the subrecord
            self._accept(subid,
                         subdata,
                         alias=alias,
                         format=format)

        # Accept components (e.g. Inline-Forms)
        for item in self.components:
            if hasattr(item, "accept"):
                item.accept(form,
                            master_id=master_id,
                            format=format)

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
                   form_vars[k] != None and \
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
                link=None):
        """
            Create or update a record

            @param record_id: the record ID
            @param data: the data
            @param alias: the component alias
            @param format: the request format (for audit)
            @param hierarchy: the data for the hierarchy link to create
            @param link: resource.link for linktable components
        """

        if not data:
            if alias is None:
                return None, Storage()
            else:
                return None

        s3db = current.s3db

        if alias is None:
            component = self.resource
        else:
            component = self.resource.components[alias]
        table = component.table
        tablename = component.tablename

        get_config = s3db.get_config

        oldrecord = None
        if record_id:
            accept_id = record_id
            db = current.db
            onaccept = get_config(tablename, "update_onaccept",
                       get_config(tablename, "onaccept", None))
            if onaccept:
                # Get oldrecord to save in form
                oldrecord = db(table._id == record_id).select(limitby=(0, 1)
                                                              ).first()
            db(table._id == record_id).update(**data)
        else:
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
        if record_id is None:
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
            if record_id is None:
                # Create hierarchy link
                if hierarchy:
                    from s3hierarchy import S3Hierarchy
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
                                                  force_update=True)

            # Store session vars
            component.lastid = str(accept_id)
            s3_store_last_record_id(tablename, accept_id)

            # Execute onaccept
            try:
                callback(onaccept, form, tablename=tablename)
            except:
                error = "onaccept failed: %s" % onaccept
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
            @param popup: only if comments=False, additional vars for comment
                          navigation items (e.g. AddResourceLink), None prevents
                          rendering of navigation items
            @param skip_post_validation: skip field validation during POST,
                                         useful for client-side processed
                                         dummy fields.
            @param widget: override option for the original field widget
        """

        if not hasattr(field, "type"):
            # Virtual Field
            field = Storage(comment=None,
                            type="string",
                            length=255,
                            unique=False,
                            uploadfolder=None,
                            autodelete=False,
                            label="", # @ToDo?
                            writable=False,
                            readable=True,
                            default=None,
                            update=None,
                            compute=None,
                            represent=lambda v: v or "",
                            )
            requires = None
            if widget is DEFAULT:
                widget = None
            required = False
            notnull = False
        elif skip_post_validation and \
             current.request.env.request_method == "POST":
            requires = SKIP_POST_VALIDATION(field.requires)
            # Some widgets may need disabling here
            if widget is DEFAULT:
                widget = field.widget
            required = False
            notnull = False
        else:
            requires = field.requires
            if widget is DEFAULT:
                widget = field.widget
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

                  widget = widget,
                  label = field.label,
                  comment = comment,

                  writable = field.writable,
                  readable = field.readable,

                  default = field.default,
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
        from s3query import S3ResourceField

        rfield = S3ResourceField(resource, self.selector)

        if resource.components:
            subtables = Storage([(c.tablename, c.alias)
                                 for c in resource.components.values()
                                 if not c.multiple])
        else:
            subtables = Storage()

        tname = rfield.tname
        if rfield.field is not None:

            # Field in the main table
            if tname == resource.tablename:
                return None, rfield.field.name, rfield.field

            # Field in a subtable (= single-record-component)
            elif tname in subtables:
                alias = subtables[tname]
                field = rfield.field
                name = "sub_%s_%s" % (alias, rfield.fname)
                f = self._rename_field(field, name)
                return alias, rfield.field.name, f

            else:
                raise SyntaxError("Invalid subtable: %s" % tname)
        else:
            raise SyntaxError("Invalid selector: %s" % self.selector)

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
                            _class="embeddedComponent",
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
            @param attributes: HTML attributes for the header row
        """

        fields = data["fields"]

        # Don't render a header row if there are no labels
        render_header = False
        header_row = TR(_class="label-row")
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

        # Render the action icons for this row
        append = subform.append
        if readonly:
            if editable:
                append(action(T("Edit this entry"), "edt"))
            else:
                append(TD())

            if deletable:
                append(action(T("Remove this entry"), "rmv"))
            else:
                append(TD())
        else:
            if index != "none" or item:
                append(action(T("Update this entry"), "rdy", throbber=True))
                append(action(T("Cancel editing"), "cnc"))
            else:
                append(TD())
                append(action(T("Add this entry"), "add", throbber=True))

    # -------------------------------------------------------------------------
    def rowstyle(self, form, fields, *args, **kwargs):
        """
            Formstyle for subform rows
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

        #script = "/%s/static/themes/CRMT2/js/inlinecomponent.layout.js" % appname
        #if script not in scripts:
            #scripts.append(script)

        # No custom JS in the default layout
        return

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
        if selector not in resource.components:
            hook = current.s3db.get_component(resource.tablename, selector)
            if hook:
                resource._attach(selector, hook)
            else:
                raise SyntaxError("Undefined component: %s" % selector)
        component = resource.components[selector]

        # Check permission
        permitted = current.auth.s3_has_permission("read",
                                                   component.tablename)
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
        if component_name in resource.components:

            component = resource.components[component_name]
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
            widgets = {}
            if fields_opt:
                fields = []
                for f in fields_opt:
                    if isinstance(f, tuple):
                        if len(f) > 2:
                            label, f, w = f
                            widgets[f] = w
                        else:
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
                if "filterby" in self.options:
                    # Filter
                    f = self._filterby_query()
                    if f is not None:
                        component.build_query(filter=f)

                if "extra_fields" in options:
                    extra_fields = options["extra_fields"]
                else:
                    extra_fields = []
                all_fields = fields + virtual_fields + extra_fields
                data = component.select(all_fields,
                                        limit=None,
                                        represent=True,
                                        raw_data=True,
                                        show_links=False,
                                        orderby=orderby)

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
                        "label": s3_unicode(rfield.label)}
                        for rfield in rfields if rfield.fname != pkey]

            self.widgets = widgets

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
                    if hasattr(rfield.field, "formatter"):
                        value = rfield.field.formatter(row[colname])
                    else:
                        # Virtual Field
                        value = row[colname]
                    text = s3_unicode(record[colname])
                    if "<" in text:
                        text = s3_strip_markup(text)

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
        else:
            raise AttributeError("Undefined component")

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
        layout = current.deployment_settings.get_ui_inline_component_layout()
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
                                         editable=editable,
                                         deletable=deletable,
                                         readonly=True,
                                         multiple=multiple,
                                         index=i,
                                         layout=layout,
                                         _id="read-row-%s" % rowname,
                                         _class=_class)
            if record_id:
                audit("read", prefix, name,
                      record=record_id, representation="html")
            item_rows.append(read_row)

        # Add the action rows
        action_rows = []

        # Edit-row
        _class = "edit-row inline-form hide"
        if required and has_rows:
            _class = "%s required" % _class
        edit_row = self._render_item(table, item, fields,
                                     editable=_editable,
                                     deletable=_deletable,
                                     readonly=False,
                                     multiple=multiple,
                                     index=0,
                                     layout=layout,
                                     _id="edit-row-%s" % formname,
                                     _class=_class)
        action_rows.append(edit_row)

        # Add-row
        insertable = get_config(tablename, "insertable")
        if insertable is None:
            insertable = True
        if insertable:
            insertable = has_permission("create", tablename)
        if insertable:
            _class = "add-row inline-form"
            if not multiple:
                if has_rows:
                    # Add Rows not relevant
                    _class = "%s hide" % _class
                else:
                    # Mark to client-side JS that we should always validate
                    _class = "%s single" % _class
            if required and not has_rows:
                _class = "%s required" % _class
            has_rows = True
            add_row = self._render_item(table, None, fields,
                                        editable=True,
                                        deletable=True,
                                        readonly=False,
                                        multiple=multiple,
                                        layout=layout,
                                        _id="add-row-%s" % formname,
                                        _class=_class
                                        )
            action_rows.append(add_row)

        # Empty edit row
        empty_row = self._render_item(table, None, fields,
                                      editable=_editable,
                                      deletable=_deletable,
                                      readonly=False,
                                      multiple=multiple,
                                      index="default",
                                      layout=layout,
                                      _id="empty-edit-row-%s" % formname,
                                      _class="empty-row inline-form hide")
        action_rows.append(empty_row)

        # Empty read row
        empty_row = self._render_item(table, None, fields,
                                      editable=_editable,
                                      deletable=_deletable,
                                      readonly=True,
                                      multiple=multiple,
                                      index="none",
                                      layout=layout,
                                      _id="empty-read-row-%s" % formname,
                                      _class="empty-row inline-form hide")
        action_rows.append(empty_row)

        # Real input: a hidden text field to store the JSON data
        real_input = "%s_%s" % (resource.tablename, field.name)
        default = dict(_type = "text",
                       _value = value,
                       requires=lambda v: (v, None))
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
                hidden.append(INPUT(_type="text",
                                    _id=k,
                                    _name=k,
                                    _value=v,
                                    _style="display:none"))
        else:
            hidden = ""

        # Render output HTML
        output = DIV(INPUT(**attr),
                     hidden,
                     widget,
                     _id = self._formname(separator="-"),
                     _field = real_input,
                     _class = "inline-component",
                     )

        # Reset the layout
        layout.set_columns(None)

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

        layout = current.deployment_settings.get_ui_inline_component_layout()
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

        return output

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

        defaults = self.options.get("default", {})

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
            if component_name in resource.components:
                component = resource.components[component_name]
            else:
                return

            # Link table handling
            link = component.link
            if link and self.options.get("link", True):
                # data are for the link table
                actuate_link = False
                component = link
            else:
                # data are for the component
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
            has_permission = current.auth.s3_has_permission
            audit = current.audit
            onaccept = s3db.onaccept
            for item in data:

                if not "_changed" in item and not "_delete" in item:
                    # No changes made to this item - skip
                    continue

                # Get the values
                values = Storage()
                for f, d in item.iteritems():
                    if f[0] != "_" and d and isinstance(d, dict):

                        field = table[f]
                        if not hasattr(field, "type"):
                            # Virtual Field
                            continue
                        elif table[f].type == "upload":
                            # Find, rename and store the uploaded file
                            rowindex = item.get("_index", None)
                            if rowindex is not None:
                                filename = self._store_file(table, f, rowindex)
                                if filename:
                                    values[f] = filename
                            continue
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

                if "_id" in item:
                    record_id = item["_id"]

                    # Delete..?
                    if "_delete" in item and item["_delete"]:
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
                        values[table._id.name] = record_id
                        query = (table._id == record_id)
                        success = db(query).update(**values)

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
                    if "_delete" in item and item["_delete"]:
                        # Row has been added and then removed again, so just
                        # ignore it
                        continue
                    # Create a new record
                    authorized = has_permission("create", tablename)
                    if not authorized:
                        continue

                    # Get master record ID
                    pkey = component.pkey
                    mastertable = resource.table
                    if pkey != mastertable._id.name:
                        query = (mastertable._id == master_id)
                        master = db(query).select(mastertable[pkey],
                                                  limitby=(0, 1)).first()
                        if not master:
                            return
                    else:
                        master = Storage({pkey: master_id})

                    if not actuate_link or not link:
                        # Add master record ID as linked directly
                        values[component.fkey] = master[pkey]
                    else:
                        # Check whether the component is a link table and we're linking to that via something like pr_person from hrm_human_resource
                        fkey = component.fkey
                        if fkey != "id" and fkey in component.fields and fkey not in values:
                            values[fkey] = master[pkey]

                    # Apply defaults
                    for f, v in defaults.iteritems():
                        if f not in item:
                            values[f] = v

                    # Create the new record
                    # use _table in case we are using an alias
                    record_id = component._table.insert(**values)

                    # Post-process create
                    if record_id:
                        # Ensure we're using the real table, not an alias
                        table = db[tablename]
                        # Audit
                        audit("create", prefix, name,
                              record=record_id, representation=format)
                        # Add record_id
                        values[table._id.name] = record_id
                        # Update super entity link
                        s3db.update_super(table, values)
                        # Update link table
                        if link and actuate_link:
                            link.update_link(master, values)
                        # Set record owner
                        auth.s3_set_record_owner(table, record_id)
                        # onaccept
                        onaccept(table, Storage(vars=values), method="create")

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
            @param attributes: HTML attributes for the row
        """

        s3 = current.response.s3

        rowtype = readonly and "read" or "edit"
        pkey = table._id.name

        data = dict()
        formfields = []
        formname = self._formname()
        widgets = self.widgets
        for f in fields:
            fname = f["name"]
            idxname = "%s_i_%s_%s_%s" % (formname, fname, rowtype, index)
            if not readonly:
                parent = table._tablename.split("_", 1)[1]
                caller = "sub_%s_%s" % (formname, idxname)
                popup = Storage(parent=parent, caller=caller)
            else:
                popup = None

            formfield = self._rename_field(table[fname], 
                                           idxname,
                                           comments=False,
                                           popup=popup,
                                           skip_post_validation=True,
                                           widget=widgets.get(fname, DEFAULT),
                                           )

            if "filterby" in self.options:
                # Get reduced options set
                options = self._filterby_options(fname)
                if options:
                    if len(options) < 2:
                        requires = IS_IN_SET(options, zero=None)
                    else:
                        requires = IS_IN_SET(options)
                    formfield.requires = SKIP_POST_VALIDATION(requires)

            # Get filterby-default
            defaults = self._filterby_defaults()
            if defaults and fname in defaults:
                default = defaults[fname]["value"]
                formfield.default = default

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
        subform = SQLFORM.factory(*formfields,
                                  record=data,
                                  showid=False,
                                  formstyle=layout.rowstyle,
                                  upload = s3.download_url,
                                  readonly=readonly,
                                  table_name=subform_name,
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

        if "filterby" in self.options:
            filterby = self.options["filterby"]
        else:
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
            Widget renderer, currently supports multiselect (default), hierarchy
            and groupedopts widgets.

            @param field: the input field
            @param value: the value to populate the widget
            @param attributes: attributes for the widget

            @return: the widget
        """

        options = self.options
        component, link = self.get_link()

        multiple = options.get("multiple", True)
        options["multiple"] = multiple

        # Field dummy
        dummy_field = Storage(name = field.name,
                              type = link.table[component.rkey].type)

        # Widget type
        widget = options.get("widget")
        if widget != "hierarchy":
            # Get the selectable entries for the widget and construct
            # a validator from it
            zero = None if multiple else options.get("zero", XML("&nbsp"))
            opts = self.get_options()
            requires = IS_IN_SET(opts,
                                 multiple=multiple,
                                 zero=zero,
                                 sort=options.get("sort", True))
            if zero is not None:
                requires = IS_EMPTY_OR(requires)
            dummy_field.requires = requires

        # Helper to extract widget options
        widget_opts = lambda keys: dict((k, v)
                                        for k, v in options.items()
                                        if k in keys)

        # Instantiate the widget
        if widget == "groupedopts" or not widget and "cols" in options:
            from s3widgets import S3GroupedOptionsWidget
            w_opts = widget_opts(("cols",
                                  "size",
                                  "help_field",
                                  "multiple",
                                  ))
            w = S3GroupedOptionsWidget(**w_opts)
        elif widget == "hierarchy":
            from s3widgets import S3HierarchyWidget
            w_opts = widget_opts(("represent",
                                  "multiple",
                                  "leafonly",
                                  "columns",
                                  ))
            w_opts["lookup"] = component.tablename
            w = S3HierarchyWidget(**w_opts)
        else:
            # Default to multiselect
            from s3widgets import S3MultiSelectWidget
            w_opts = widget_opts(("filter",
                                  "header",
                                  "selectedList",
                                  "noneSelectedText",
                                  "multiple",
                                  "columns",
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
            widget.add_class("inline-component")

        # Append the attached script to jquery_ready
        script = options.get("script")
        if script:
            current.response.s3.jquery_ready.append(script)

        return widget

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
                    query = FS(component.rkey).belongs(delete)
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
            represent = S3Represent(lookup = component.tablename,
                                    field = lookup_field)

        # Represent all values
        if isinstance(value, (list, tuple, set)):
            result = represent.bulk(list(value))
            if None not in value:
                result.pop(None, None)
        else:
            result = represent.bulk([value])

        # Sort them
        labels = result.values()
        labels.sort()

        # Render as TAG to support HTML output
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

        resource = self.resource

        selector = self.selector
        if selector in resource.components:
            component = resource.components[selector]
        else:
            raise SyntaxError("Undefined component: %s" % selector)
        if not component.link:
            # @todo: better error message
            raise SyntaxError("No linktable for %s" % selector)
        link = component.link

        return (component, link)

# =============================================================================
class S3SQLInlineComponentCheckbox(S3SQLInlineComponent):
    """
        Form element for an inline-component-form

        This form element allows CRUD of multi-record-components within
        the main record form. It renders a single hidden text field with a
        JSON representation of the component records, and a widget which
        facilitates client-side manipulation of this JSON.
        This widget is a checkbox per available option, so is suitable for
        simple many<>many link tables ('tagging'). It does NOT support link
        tables with additional fields.

        The widget uses the s3.inline_component.js script for
        client-side manipulation of the JSON data.
        During accept(), the component gets updated according to the JSON
        returned.

        @todo: deprecate, replace by S3SQLInlineLink
    """

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
        if component_name in resource.components:

            component = resource.components[component_name]
            # For link-table components, embed the link table
            # rather than the component
            if component.link:
                component = component.link

            table = component.table
            tablename = component.tablename

            pkey = table._id.name

            fieldname = self.options["field"]
            field = table[fieldname]

            if pkey == fieldname:
                qfields = [field]
            else:
                qfields = [field, table[pkey]]

            items = []
            if record_id:
                # Build the query
                query = (resource.table._id == record_id) & \
                        component.get_join()

                if "filterby" in self.options:
                    # Filter
                    f = self._filterby_query()
                    if f is not None:
                        query &= f

                # Get the rows:
                rows = current.db(query).select(*qfields)

                iappend = items.append
                has_permission = current.auth.s3_has_permission
                for row in rows:
                    row_id = row[pkey]
                    item = {"_id": row_id}

                    #cid = row[component.table._id]
                    permitted = has_permission("read", tablename, row_id)
                    if not permitted:
                        continue
                    permitted = has_permission("update", tablename, row_id)
                    if not permitted:
                        item["_readonly"] = True

                    if fieldname in row:
                        value = row[fieldname]
                        try:
                            text = s3_represent_value(field,
                                                      value = value,
                                                      strip_markup = True,
                                                      xml_escape = True)
                        except:
                            text = s3_unicode(value)
                    else:
                        value = None
                        text = ""
                    value = field.formatter(value)
                    item[fieldname] = {"value": value, "text": text}
                    iappend(item)

            data = {"component": component_name,
                    "field": fieldname,
                    "data": items}
        else:
            raise AttributeError("Undefined component")

        return json.dumps(data, separators=SEPARATORS)

    # -------------------------------------------------------------------------
    def __call__(self, field, value, **attributes):
        """
            Widget method for this form element. Renders a table with
            checkboxes for all available options.
            This widget uses s3.inline_component.js to facilitate
            manipulation of the entries.

            @param field: the Field for this form element
            @param value: the current value for this field
            @param attributes: keyword attributes for this widget

            @ToDo: Add ability to add new options to the list
            @ToDo: Option for Grouped Checkboxes (e.g. for Activity Types)
        """

        if value is None:
            value = field.default
        if isinstance(value, basestring):
            data = json.loads(value)
        else:
            data = value
            value = json.dumps(value, separators=SEPARATORS)
        if data is None:
            raise SyntaxError("No resource structure information")

        T = current.T
        opts = self.options

        script = opts.get("script", None)
        if script:
            current.response.s3.jquery_ready.append(script)

        # @ToDo: Render read-only if self.readonly

        # @ToDo: Hide completely if the user is not permitted to read this
        # component

        # Get the list of available options
        options = self._options(data)

        formname = self._formname()
        fieldname = data["field"]
        field_name = "%s-%s" % (formname, fieldname)

        if not options:
            widget = T("No options currently available")
        else:
            # Translate the Options?
            translate = opts.get("translate", None)
            if translate is None:
                # Try to lookup presence of reusable field
                # - how do we know the module though?
                s3db = current.s3db
                if hasattr(s3db, fieldname):
                    reusable_field = s3db.get(fieldname)
                    if reusable_field:
                        represent = reusable_field.attr.represent
                        if hasattr(represent, "translate"):
                            translate = represent.translate

            # Render the options
            cols = opts.get("cols", 1)
            count = len(options)
            num_of_rows = count / cols
            if count % cols:
                num_of_rows += 1

            table = [[] for row in range(num_of_rows)]

            row_index = 0
            col_index = 0

            for _id in options:
                input_id = "id-%s-%s-%s" % (field_name, row_index, col_index)
                option = options[_id]
                v = option["name"]
                if translate:
                    v = T(v)
                label = LABEL(v, _for=input_id)
                title = option.get("help", None)
                if title:
                    # Add help tooltip
                    label["_title"] = title
                widget = TD(INPUT(_disabled = not option["editable"],
                                  _id=input_id,
                                  _name=field_name,
                                  _type="checkbox",
                                  _value=_id,
                                  hideerror=True,
                                  value=option["selected"],
                                  ),
                            label,
                            )
                table[row_index].append(widget)
                row_index += 1
                if row_index >= num_of_rows:
                    row_index = 0
                    col_index += 1

            widget = TABLE(table,
                           _class="checkboxes-widget-s3",
                           )

        # Real input: a hidden text field to store the JSON data
        real_input = "%s_%s" % (self.resource.tablename, field_name)
        default = dict(_type = "text",
                       _value = value,
                       requires=lambda v: (v, None))
        attr = StringWidget._attributes(field, default, **attributes)
        attr["_class"] = attr["_class"] + " hide"
        attr["_id"] = real_input

        # Render output HTML
        output = DIV(INPUT(**attr),
                     widget,
                     _id=self._formname(separator="-"),
                     _field=real_input,
                     _class="inline-checkbox inline-component",
                     _name="%s_widget" % field_name,
                     )

        return output

    # -------------------------------------------------------------------------
    def _options(self, data):
        """
            Build the Options
        """

        s3db = current.s3db
        opts = self.options

        # Get the component resource
        resource = self.resource
        component_name = data["component"]
        component = resource.components[component_name]
        table = component.table

        # @ToDo: Support lookups to tables which don't use 'name' (e.g. 'tag')
        option_help = opts.get("option_help", None)
        if option_help:
            fields = ["id", "name", option_help]
        else:
            fields = ["id", "name"]

        opt_filter = opts.get("filter", None)
        if opt_filter:
            linktable = s3db[opt_filter["linktable"]]
            lkey = opt_filter["lkey"]
            rkey = opt_filter["rkey"]
            if "values" in opt_filter:
                # Option A - from AJAX request
                values = opt_filter["values"]
            else:
                # Option B - from record
                lookuptable = opt_filter.get("lookuptable", None)
                if lookuptable:
                    # e.g. Project Community Activity Types filtered by Sector of parent Project
                    lookupkey = opt_filter.get("lookupkey", None)
                    if not lookupkey:
                        raise
                    if resource._rows:
                        _id = resource._rows[0][lookupkey]
                        _resource = s3db.resource(lookuptable, id=_id)
                    else:
                        _id = None
                else:
                    # e.g. Project Themes filtered by Sector
                    if resource._ids:
                        _id = resource._ids[0]
                        _resource = resource
                    else:
                        _id = None
                if _id:
                    _table = _resource.table
                    if rkey in _table.fields:
                        values = [_table[rkey]]
                    else:
                        found = False
                        if lookuptable:
                            # Need to load component
                            hooks = s3db.get_components(_table)
                            for alias in hooks:
                                if hooks[alias].rkey == rkey:
                                    found = True
                                    _resource._attach(alias, hooks[alias])
                                    _component = _resource.components[alias]
                                    break
                        else:
                            # Components are already loaded
                            components = _resource.components
                            for c in components:
                                if components[c].rkey == rkey:
                                    found = True
                                    _component = components[c]
                                    break
                        if found:
                            _rows = _component.select(["id"],
                                                      limit=None,
                                                      as_rows=True)
                            values = [r.id for r in _rows]
                        else:
                            #raise SyntaxError
                            values = []
                else:
                    # New record
                    values = []
            rows = []
            rappend = rows.append
            # All rows, whether or not in the link table
            fields = [table[f] for f in fields]
            fields.append(linktable[rkey])
            query = (table.deleted == False) & \
                    current.auth.s3_accessible_query("read", table)
            srows = current.db(query).select(left=linktable.on(linktable[lkey] == table.id),
                                             orderby=table.name,
                                             *fields)
            for r in srows:
                v = r[linktable][rkey]
                # We want all all rows which have no entry in the linktable (no restrictions)
                # or else match this restriction
                if not v or v in values:
                    _r = r[table]
                    record = Storage(id = _r.id,
                                     name = _r.name)
                    if option_help:
                        record[option_help] = _r[option_help]
                    rappend(record)
        else:
            _resource = s3db.resource(component.tablename)

            # Currently we only support filterby or filter, not both
            filterby = opts.get("filterby", None)
            if filterby:
                options = filterby["options"]
                filter_field = filterby["field"]
                if isinstance(options, list):
                    _resource.add_filter(FS(filter_field).belongs(options))
                else:
                    _resource.add_filter(FS(filter_field) == options)

            rows = _resource.select(fields=fields,
                                    limit=None,
                                    orderby=table.name,
                                    as_rows=True)

        if not rows:
            return None

        if component.link:
            # For link-table components, check the link table permissions
            # rather than the component
            component = component.link
        creatable = current.auth.s3_has_permission("create", component.tablename)
        options = OrderedDict()
        for r in rows:
            options[r.id] = dict(name=r.name,
                                 selected=False,
                                 editable=creatable)
            if option_help:
                options[r.id]["help"] = r[option_help]

        # Which ones are currently selected?
        fieldname = data["field"]
        items = data["data"]
        prefix = component.prefix
        name = component.name
        audit = current.audit
        for i in xrange(len(items)):
            item = items[i]
            if fieldname in item:
                if "_delete" in item:
                    continue
                _id = item[fieldname]["value"]
                if "_id" in item:
                    record_id = item["_id"]
                    # Check permissions to edit this item
                    editable = not "_readonly" in item
                    # Audit
                    audit("read", prefix, name,
                          record=record_id, representation="html")
                elif "_changed" in item:
                    # Form had errors
                    editable = True
                    _id = int(_id)
                try:
                    options[_id].update(selected=True,
                                        editable=editable)
                except:
                    # e.g. Theme filtered by Sector
                    current.session.error = \
                        current.T("Invalid data: record %(id)s not accessible in table %(table)s") % \
                            dict(id=_id, table=table)
                    redirect(URL(args=None, vars=None))

        return options

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

        if isinstance(value, basestring):
            data = json.loads(value)
        else:
            data = value

        if data["data"] == []:
            # Don't render a subform for NONE
            return current.messages["NONE"]

        fieldname = data["field"]
        items = data["data"]

        component = self.resource.components[data["component"]]

        audit = current.audit
        prefix, name = component.prefix, component.name

        xml_decode = current.xml.xml_decode
        vals = []
        for item in items:
            if "_id" in item:
                record_id = item["_id"]
            else:
                continue
            audit("read", prefix, name,
                  record=record_id, representation="html")
            vals.append(XML(xml_decode(item[fieldname]["text"])))

        vals.sort()
        represent = TAG[""](list(chain.from_iterable(
                                [[v, ", "] for v in vals]))[:-1])
        return TABLE(TBODY(TR(TD(represent),
                              #_class="read-row"
                              )),
                     #_class="embeddedComponent"
                     )

# =============================================================================
class S3SQLInlineComponentMultiSelectWidget(S3SQLInlineComponentCheckbox):
    """
        Form element for an inline-component-form

        This form element allows CRUD of multi-record-components within
        the main record form. It renders a single hidden text field with a
        JSON representation of the component records, and a widget which
        facilitates client-side manipulation of this JSON.
        This widget is a SELECT MULTIPLE, so is suitable for
        simple many<>many link tables ('tagging'). It does NOT support link
        tables with additional fields.

        The widget uses the s3.inline_component.js script for
        client-side manipulation of the JSON data.
        During accept(), the component gets updated according to the JSON
        returned.

        @todo: deprecate, replace by S3SQLInlineLink
    """

    # -------------------------------------------------------------------------
    def __call__(self, field, value, **attributes):
        """
            Widget method for this form element.
            Renders a SELECT MULTIPLE with all available options.
            This widget uses s3.inline_component.js to facilitate
            manipulation of the entries.

            @param field: the Field for this form element
            @param value: the current value for this field
            @param attributes: keyword attributes for this widget

            @ToDo: Add ability to add new options to the list
            @ToDo: Wrap S3MultiSelectWidget (or at least bring options up to date)
            @ToDo: support Multiple=False
        """

        if value is None:
            value = field.default
        if isinstance(value, basestring):
            data = json.loads(value)
        else:
            data = value
            value = json.dumps(value, separators=SEPARATORS)
        if data is None:
            raise SyntaxError("No resource structure information")

        T = current.T

        opts = self.options

        jquery_ready = current.response.s3.jquery_ready

        script = opts.get("script", None)
        if script and script not in jquery_ready:
            jquery_ready.append(script)

        # @ToDo: Render read-only if self.readonly

        # @ToDo: Hide completely if the user is not permitted to read this
        # component

        # Get the list of available options
        options = self._options(data)

        formname = self._formname()
        fieldname = data["field"]
        field_name = "%s-%s" % (formname, fieldname)

        if not options:
            widget = T("No options currently available")
        else:
            # Translate the Options?
            translate = opts.get("translate", None)
            if translate is None:
                # Try to lookup presence of reusable field
                # - how do we know the module though?
                s3db = current.s3db
                if hasattr(s3db, fieldname):
                    reusable_field = s3db.get(fieldname)
                    if reusable_field:
                        represent = reusable_field.attr.represent
                        if hasattr(represent, "translate"):
                            translate = represent.translate

            # Render the options
            _opts = []
            vals = []
            oappend = _opts.append
            for _id in options:
                option = options[_id]
                v = option["name"]
                if translate:
                    v = T(v)
                oappend(OPTION(v,
                               _value=_id,
                               _disabled = not option["editable"]))
                if option["selected"]:
                    vals.append(_id)

            widget = SELECT(*_opts,
                            value=vals,
                            _id=field_name,
                            _name=field_name,
                            _multiple=True,
                            _class="inline-multiselect-widget",
                            _size=5 # @ToDo: Make this configurable?
                            )
            # jQueryUI widget
            # (this section could be made optional)
            opt_filter = opts.get("filter", False)
            header = opts.get("header", False)
            selectedList = opts.get("selectedList", 3)
            noneSelectedText = "Select"
            if header is True:
                header = '''checkAllText:'%s',uncheckAllText:"%s"''' % \
                    (T("Check all"),
                     T("Uncheck all"))
            elif header is False:
                header = '''header:false'''
            else:
                header = '''header:"%s"''' % self.header
            script = '''$('#%s').multiselect({selectedText:'%s',%s,height:300,minWidth:0,selectedList:%s,noneSelectedText:'%s'})''' % \
                (field_name,
                 T("# selected"),
                 header,
                 selectedList,
                 T(noneSelectedText))
            if opt_filter:
                script = '''%s.multiselectfilter()''' % script
            if script not in jquery_ready: # Prevents loading twice when form has errors
                jquery_ready.append(script)

        # Real input: a hidden text field to store the JSON data
        real_input = "%s_%s" % (self.resource.tablename, field_name)
        default = dict(_type = "text",
                       _value = value,
                       requires=lambda v: (v, None))
        attr = StringWidget._attributes(field, default, **attributes)
        attr["_class"] = attr["_class"] + " hide"
        attr["_id"] = real_input

        # Render output HTML
        output = DIV(INPUT(**attr),
                     widget,
                     _id=self._formname(separator="-"),
                     _field=real_input,
                     _class="inline-multiselect inline-component",
                     _name="%s_widget" % field_name,
                     )
        columns = opts.get("columns")
        if columns:
            output.add_class("small-%s columns" % columns)

        return output

# END =========================================================================
