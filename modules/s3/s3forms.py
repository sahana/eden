# -*- coding: utf-8 -*-

""" S3 SQL Forms

    @copyright: 2012 (c) Sahana Software Foundation
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

from gluon import *
from gluon.storage import Storage
from gluon.tools import callback
from gluon.sqlhtml import StringWidget
from s3utils import s3_mark_required, s3_unicode

try:
    import json # try stdlib (Python 2.6)
except ImportError:
    try:
        import simplejson as json # try external module
    except:
        import gluon.contrib.simplejson as json # fallback to pure-Python module

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

        opts = []
        attr = []
        for k in attributes:
            value = attributes[k]
            if k[:1] == "_":
                self.attr[k] = value
            else:
                self.opts[k] = value

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

            @returns: a FORM instance
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

            @returns: a FORM instance
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

        session = current.session
        response = current.response
        s3 = response.s3
        settings = s3.crud

        manager = current.manager
        audit = manager.audit

        prefix = self.prefix
        name = self.name
        tablename = self.tablename
        table = self.table

        record = None
        labels = None

        download_url = manager.s3.download_url

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
            record_id = self.deduplicate_link(request, record_id)

            # Add asterisk to labels of required fields
            mark_required = self._config("mark_required", default = [])
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
            formstyle = lambda a, b, c, d: settings.formstyle(a, b, c, d)

        # Generate the form
        if record is None:
            record = record_id
        form = SQLFORM(table,
                       record = record,
                       record_id = record_id,
                       readonly = readonly,
                       comments = not readonly,
                       deletable = False,
                       showid = False,
                       upload = download_url,
                       labels = labels,
                       formstyle = formstyle,
                       separator = "",
                       submit_button = settings.submit_button)

        # Style the Submit button, if-requested
        if settings.submit_style:
            try:
                form[0][-1][0][0]["_class"] = settings.submit_style
            except TypeError:
                # Submit button has been removed
                pass

        # Subheadings
        subheadings = options.get("subheadings", None)
        if subheadings:
            self.insert_subheadings(form, tablename, subheadings)

        # Cancel button
        if not readonly and response.s3.cancel:
            form[0][-1][0].append(A(current.T("Cancel"),
                                    _href=response.s3.cancel,
                                    _class="action-lnk"))

        # Process the form
        logged = False
        if not readonly:
            link = options.get("link", None)
            onvalidation = options.get("onvalidation", None)
            onaccept = options.get("onaccept", None)
            success, error = self.process(form,
                                          request.post_vars,
                                          onvalidation = onvalidation,
                                          onaccept = onaccept,
                                          link = link,
                                          http = request.http)
            if success:
                response.confirmation = message
                logged = True
            elif error:
                response.error = error

        # Audit read
        if not logged and not form.errors:
            audit("read", prefix, name,
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

        audit = current.manager.audit

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
            audit("read", prefix, name,
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
            if not request.post_vars[pkey]:
                lkey = linked.lkey
                rkey = linked.rkey
                _lkey = request.post_vars[lkey]
                _rkey = request.post_vars[rkey]
                query = (table[lkey] == _lkey) & (table[rkey] == _rkey)
                row = current.db(query).select(table._id, limitby=(0, 1)).first()
                if row is not None:
                    record_id = row[pkey]
                    formkey = session.get("_formkey[%s/None]" % tablename)
                    formname = "%s/%s" % (tablename, record_id)
                    session["_formkey[%s]" % formname] = formkey
                    request.post_vars["_formname"] = formname
                    request.post_vars[pkey] = record_id

        return record_id

    # -------------------------------------------------------------------------
    def process(self, form, vars,
                onvalidation = None,
                onaccept = None,
                link = None,
                http = "POST"):
        """
            Process the form

            @todo: describe arguments
        """

        manager = current.manager
        audit = manager.audit
        table = self.table
        record_id = self.record_id

        # Get the proper onvalidation routine
        if isinstance(onvalidation, dict):
            onvalidation = onvalidation.get(self.tablename, [])

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

        formname = "%s/%s" % (self.tablename,
                              self.record_id)
        if form.accepts(vars,
                        current.session,
                        formname=formname,
                        onvalidation=onvalidation,
                        keepvalues=False,
                        hideerror=False):

            # Audit
            prefix = self.prefix
            name = self.name
            if self.record_id is None:
                audit("create", prefix, name, form=form,
                      representation=format)
            else:
                audit("update", prefix, name, form=form,
                      record=record_id, representation=format)

            vars = form.vars

            # Update super entity links
            s3db = current.s3db
            s3db.update_super(table, vars)

            # Update component link
            if link and link.postprocess is None:
                resource = link.resource
                master = link.master
                resource.update_link(master, vars)

            if vars.id:
                if record_id is None:
                    # Set record owner
                    auth = current.auth
                    auth.s3_set_record_owner(table, vars.id)
                    auth.s3_make_session_owner(table, vars.id)
                else:
                    # Update realm
                    update_realm = s3db.get_config(table, "update_realm")
                    if update_realm:
                        current.auth.set_realm_entity(table, vars,
                                                      force_update=True)
                # Store session vars
                self.resource.lastid = str(vars.id)
                manager.store_session(prefix, name, vars.id)

            # Execute onaccept
            callback(onaccept, form, tablename=self.tablename)

        else:
            success = False

            if form.errors:

                # IS_LIST_OF validation errors need special handling
                errors = []
                table = self.table
                for fieldname in form.errors:
                    if fieldname in table and \
                       isinstance(table[fieldname].requires, IS_LIST_OF):
                        errors.append("%s: %s" % (fieldname,
                                                  form.errors[fieldname]))
                if errors:
                    error = "\n".join(errors)

            elif http == "POST":

                # Invalid form
                error = current.T("Invalid form (re-opened in another window?)")

        return success, error

    # -------------------------------------------------------------------------
    # Utility functions
    # -------------------------------------------------------------------------
    @staticmethod
    def insert_subheadings(form, tablename, subheadings):
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
                f = tr.attributes.get("_id", None)
                if f.startswith(tablename):
                    f = f[len(tablename)+1:-6]
                    for k in subheadings.keys():
                        if k in done:
                            continue
                        fields = subheadings[k]
                        if not isinstance(fields, (list, tuple)):
                            fields = [fields]
                        if f in fields:
                            done.append(k)
                            form[0].insert(i, TR(TD(k, _colspan=3,
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

            @returns: a FORM instance
        """

        db = current.db
        s3 = current.response.s3

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
            mark_required = self._config("mark_required", default = [])
            labels, required = s3_mark_required(self.table, mark_required)
            if required:
                # Show the key if there are any required fields.
                s3.has_required = True
            else:
                s3.has_required = False
        else:
            labels = None

        # Choose formstyle
        if format == "plain":
            # Default formstyle works best when we have no formatting
            formstyle = "table3cols"
        else:
            formstyle = lambda a, b, c, d: s3.crud.formstyle(a, b, c, d)

        # Retrieve the record
        record = None
        if record_id is not None:
            query = (self.table._id==record_id)
            record = db(query).select(limitby=(0, 1)).first()
        self.record_id = record_id
        self.subrows = Storage()

        # Populate the form
        data = None
        noupdate = []
        forbidden = []
        permit = resource.permit

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
                    permitted = permit("create", ctname)
                    if not permitted:
                        forbidden.append(alias)
                    continue
                else:
                    cid = row[component.table._id]
                    permitted = permit("read", ctname, cid)
                    if not permitted:
                        forbidden.append(alias)
                        continue
                    permitted = permit("update", ctname, cid)
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
                permitted = permit("create", component.tablename)
                if not permitted:
                    forbidden.append(alias)

        # Apply permissions for subtables
        fields = [f for f in fields if f[0] not in forbidden]
        for a, n, f in fields:
            if a and a in noupdate:
                f.writable = False
        self.subtables = [s for s in self.subtables if s not in forbidden]

        # Aggregate the form fields
        formfields = [f[-1] for f in fields]

        # Render the form
        form = SQLFORM.factory(*formfields,
                               record=data,
                               showid=False,
                               labels = labels,
                               formstyle = formstyle,
                               table_name = self.tablename,
                               upload = "default/download",
                               readonly = readonly,
                               separator = "")

        # Process the form
        formname = "%s/%s" % (self.tablename, record_id)
        if form.accepts(request.post_vars,
                        current.session,
                        onvalidation=self.validate,
                        formname=formname,
                        keepvalues=False,
                        hideerror=False):

            self.accept(form, format=format)

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
            callback(onvalidation, form, tablename=self.tablename)

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
                subid = rows[alias][subtable._id]
                subonvalidation = get_config(subtable._tablename,
                                             "update_onvalidation",
                                  get_config(subtable._tablename,
                                             "onvalidation", None))
            else:
                subid = None
                subonvalidation = get_config(subtable._tablename,
                                             "create_onvalidation",
                                  get_config(subtable._tablename,
                                             "onvalidation", None))

            # Validate against the subtable, store errors in form
            if subonvalidation is not None:
                callback(subonvalidation, subform,
                            tablename = subtable._tablename)
                for fn in subform.errors:
                    dummy = "sub_%s_%s" % (alias, fn)
                    form.errors[dummy] = subform.errors[fn]

        return

    # -------------------------------------------------------------------------
    def accept(self, form, format=None):
        """
            Create/update all records from the form.

            @param form: the form
            @param format: data format extension (for audit)
        """

        db = current.db
        table = self.table

        # Create/update the main record
        main_data = self._extract(form)
        master_id = self._accept(self.record_id,
                                 main_data,
                                 format=format)
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
            accept_subid = self._accept(subid,
                                        subdata,
                                        alias=alias,
                                        format=format)

        # Accept components (e.g. Inline-Forms)
        for item in self.components:
            if hasattr(item, "accept"):
                item.accept(form,
                            master_id=master_id,
                            format=format)

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
            for k in form.vars:
                if k[:4] == "sub_" and \
                   form.vars[k] != None and \
                   k[4:4+len(alias)+1] == "%s_" % alias:
                    fn = k[4+len(alias)+1:]
                    subform[fn] = form.vars[k]
            return subform

    # -------------------------------------------------------------------------
    def _accept(self, record_id, data, alias=None, format=None):
        """
            Create or update a record

            @param record_id: the record ID
            @param data: the data
            @param alias: the component alias
            @param format: the request format (for audit)
        """

        if not data:
            return

        s3db = current.s3db
        manager = current.manager
        audit = manager.audit

        if alias is None:
            component = self.resource
        else:
            component = self.resource.components[alias]
        table = component.table
        tablename = component.tablename

        get_config = s3db.get_config

        record = None
        if record_id:
            accept_id = record_id
            db = current.db
            db(table._id == record_id).update(**data)
            onaccept = get_config(tablename, "update_onaccept",
                       get_config(tablename, "onaccept", None))
            if onaccept:
                record = db(table._id == record_id).select(limitby=(0, 1)
                                                           ).first()
        else:
            accept_id = table.insert(**data)
            if not accept_id:
                raise RuntimeError("Could not create record")
            onaccept = get_config(tablename, "create_onaccept",
                       get_config(tablename, "onaccept", None))

        data[table._id.name] = accept_id
        prefix, name = tablename.split("_", 1)
        form = Storage(vars=Storage(data), record=record)

        # Audit
        if record_id is None:
            audit("create", prefix, name, form=form,
                  representation=format)
        else:
            audit("update", prefix, name, form=form,
                  record=accept_id, representation=format)

        # Update super entity links
        s3db.update_super(table, data)

        if accept_id:
            if record_id is None:
                # Set record owner
                auth = current.auth
                auth.s3_set_record_owner(table, accept_id)
                auth.s3_make_session_owner(table, accept_id)
            else:
                # Update realm
                update_realm = s3db.get_config(table, "update_realm")
                if update_realm:
                    current.auth.set_realm_entity(table, Storage(data),
                                                  force_update=True)

            # Store session vars
            component.lastid = str(accept_id)
            manager.store_session(prefix, name, accept_id)

            # Execute onaccept
            callback(onaccept, form, tablename=tablename)

        return accept_id

# =============================================================================
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
            @returns: a tuple
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
    def _rename_field(field, name, skip_post_validation=False):
        """
            Rename a field (actually: create a new Field instance with the
            same attributes as the given Field, but a different field name).

            @param field: the original Field instance
            @param name: the new name
            @param skip_post_validation: skip field validation during POST,
                                         useful for client-side processed
                                         dummy fields.
        """

        if skip_post_validation and \
           current.request.env.request_method == "POST":
            requires = lambda value: (value, None)
            required = False
            notnull = False
        else:
            requires = field.requires
            required = field.required
            notnull = field.notnull

        f = Field(str(name),
                  type=field.type,
                  length=field.length,

                  required=required,
                  notnull=notnull,
                  unique=field.unique,

                  uploadfolder=field.uploadfolder,
                  autodelete = field.autodelete,

                  widget=field.widget,
                  label=field.label,
                  comment=field.comment,

                  writable=field.writable,
                  readable=field.readable,

                  default=field.default,
                  update=field.update,
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
            @returns: a tuple
                        (
                            subtable alias (or None for main table),
                            original field name,
                            Field instance for the form renderer
                        )
        """

        # Import S3ResourceField only here, to avoid circular dependency
        from s3resource import S3ResourceField

        rfield = S3ResourceField(resource, self.selector)

        subtables = Storage([(c.tablename, c.alias)
                             for c in resource.components.values()
                             if not c.multiple])

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
            @returns: the value for the input field that corresponds
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
            @returns: tuple of (value, error) where value is the
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
            @returns: the widget for this form element as HTML helper
        """

        raise NotImplementedError

    # -------------------------------------------------------------------------
    def represent(self, value):
        """
            Read-only representation of this form element. This will be
            used instead of the __call__() method when the form element
            is to be rendered read-only.

            @param value: the value as returned from extract()
            @returns: the read-only representation of this element as
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
            @returns: True on success, False on error
        """

        return True

# =============================================================================
class S3SQLInlineComponent(S3SQLSubForm):
    """
        Form element for an inline-component-form

        This form element allows CRUD of multi-record-components within
        the main record form. It renders a single hidden text field with a
        JSON representation of the component records, and a widget which
        facilitates client-side manipulation of this JSON. During accept(),
        the component gets updated according to the JSON returned.

        The widget uses the s3.inline_component.js script for client-side
        manipulation of the JSON data. Changes made by the script will be
        validated through Ajax-calls to the CRUD.validate() method.
    """

    prefix = "sub"

    # -------------------------------------------------------------------------
    def resolve(self, resource):
        """
            Method to resolve this form element against the calling resource.

            @param resource: the resource
            @returns: a tuple (self, None, Field instance)
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
        permitted = component.permit("read", component.tablename)
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
                      label = label,
                      widget = self,
                      default = self.extract(resource, None),
                      represent = self.represent,
                      requires = self.parse)

        return (self, None, field)

    # -------------------------------------------------------------------------
    def extract(self, resource, record_id):
        """
            Initialize this form element for a particular record. Retrieves
            the component data for this record from the database and
            converts them into a JSON string to populate the input field with.

            @param resource: the resource the record belongs to
            @param record_id: the record ID
            @returns: the JSON for the input field.
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

            if "fields" in self.options:
                fields = [f for f in self.options["fields"] if f in table.fields]
            else:
                # Really?
                fields = [f.name for f in table if f.readable or f.writable]

            headers = [{"name":f, "label": s3_unicode(table[f].label)} for f in fields]

            qfields = [f for f in fields if f in table.fields]
            if pkey not in qfields:
                qfields.insert(0, pkey)
            qfields = [table[f] for f in qfields]

            if record_id:
                # Build the query
                query = (resource.table._id == record_id) & component.get_join()

                # Filter
                f = self._filterby_query()
                if f is not None:
                    query &= f

                # Get the rows:
                rows = current.db(query).select(*qfields)

                items = []
                permit = resource.permit
                represent = current.manager.represent
                for row in rows:
                    row_id = row[pkey]
                    item = {"_id": row_id}

                    cid = row[component.table._id]
                    permitted = permit("read", tablename, row_id)
                    if not permitted:
                        continue
                    permitted = permit("update", tablename, row_id)
                    if not permitted:
                        item["_readonly"] = True

                    for f in headers:
                        fname = f["name"]
                        field = table[fname]
                        if fname in row:
                            value = row[fname]
                            try:
                                text = represent(field,
                                                 value = value,
                                                 strip_markup = True,
                                                 xml_escape = True)
                            except:
                                text = s3_unicode(value)
                        else:
                            value = None
                            text = ""
                        value = field.formatter(value)
                        item[fname] = {"value": value, "text": text}
                    items.append(item)
            else:
                items = []

            validate = self.options.get("validate", None)
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
                    "data": items}
        else:
            raise AttributeError("undefined component")

        return json.dumps(data)

    # -------------------------------------------------------------------------
    def parse(self, value):
        """
            Validator method, converts the JSON returned from the input
            field into a Python object.

            @param value: the JSON from the input field.
            @returns: tuple of (value, error), where value is the converted
                      JSON, and error the error message if the decoding
                      fails, otherwise None
        """

        if isinstance(value, basestring):
            try:
                value = json.loads(value)
            except:
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

        s3 = current.response.s3
        appname = current.request.application

        if value is None:
            value = field.default
        if isinstance(value, basestring):
            data = json.loads(value)
        else:
            data = value
            value = json.dumps(value)
        if data is None:
            raise SyntaxError("no resource structure information")

        # Get the table
        resource = self.resource
        component_name = data["component"]
        component = resource.components[component_name]
        table = component.table

        # Render read-only if self.readonly

        # Hide completely if the user is not permitted to read this
        # component

        formname = self._formname()

        # Add the header row
        labels = self._render_headers(data,
                                      _class="label-row")

        fields = data["fields"]
        items = data["data"]

        # Flag whether there are any rows (at least an add-row) in the widget
        has_rows = False

        # Add the item rows
        item_rows = []
        prefix = component.prefix
        name = component.name
        audit = component.audit
        permit = component.permit
        tablename = component.tablename
        for i in xrange(len(items)):
            has_rows = True
            item = items[i]
            # Get the item record ID
            if "_id" in item:
                record_id = item["_id"]
            else:
                continue
            # Check permissions to edit this item
            editable = permit("update", tablename, record_id)
            deletable = permit("delete", tablename, record_id)
            # Render read-row accordingly
            rowname = "%s-%s" % (formname, i)
            read_row = self._render_item(table, item, fields,
                                         editable=editable,
                                         deletable=deletable,
                                         readonly=True,
                                         index=i,
                                         _id="read-row-%s" % rowname,
                                         _class="read-row")
            audit("read", prefix, name,
                  record=record_id, representation="html")
            item_rows.append(read_row)

        # Add the action rows
        action_rows = []

        # Edit-row
        edit_row = self._render_item(table, None, fields,
                                     editable=True,
                                     deletable=True,
                                     readonly=False,
                                     index=0,
                                     _id="edit-row-%s" % formname,
                                     _class="edit-row hide")
        action_rows.append(edit_row)

        # Add-row
        permitted = component.permit("create", component.tablename)
        if permitted:
            has_rows = True
            add_row = self._render_item(table, None, fields,
                                        editable=True,
                                        deletable=True,
                                        readonly=False,
                                        _id="add-row-%s" % formname,
                                        _class="add-row")
            action_rows.append(add_row)

        # Empty edit row
        empty_row = self._render_item(table, None, fields,
                                      editable=True,
                                      deletable=True,
                                      readonly=False,
                                      index="default",
                                      _id="empty-edit-row-%s" % formname,
                                      _class="empty-row hide")
        action_rows.append(empty_row)

        # Empty read row
        empty_row = self._render_item(table, None, fields,
                                      editable=True,
                                      deletable=True,
                                      readonly=True,
                                      index="none",
                                      _id="empty-read-row-%s" % formname,
                                      _class="empty-row hide")
        action_rows.append(empty_row)

        # Real input: a hidden text field to store the JSON data
        real_input = "%s_%s" % (self.resource.tablename, field.name)
        default = dict(_type = "text", value = value)
        attr = StringWidget._attributes(field, default, **attributes)
        attr["_class"] = attr["_class"] + " hide"
        attr["_id"] = real_input

        if has_rows:
            widget = TABLE(
                        THEAD(labels),
                        TBODY(item_rows),
                        TFOOT(action_rows),
                        _class="embeddedComponent",
                     )
        else:
            widget = current.T("No entries currently available")


        # Render output HTML
        output = DIV(
                    INPUT(**attr),
                    widget,
                    _id=self._formname(separator="-"),
                    _field=real_input
                )

        # JavaScript
        if s3.debug:
            script = "s3.inline_component.js"
        else:
            script = "s3.inline_component.min.js"

        s3.scripts.append("/%s/static/scripts/S3/%s" % (appname, script))

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

        labels = self._render_headers(data,
                                      _class="label-row")

        trs = []

        fields = data["fields"]
        items = data["data"]

        component = self.resource.components[data["component"]]

        audit = component.audit
        prefix, name = component.prefix, component.name

        for item in items:
            if "_id" in item:
                record_id = item["_id"]
            else:
                continue
            audit("read", prefix, name,
                  record=record_id, representation="html")
            columns = [TD(item[f["name"]]["text"]) for f in fields]
            trs.append(TR(columns, _class="read-row"))

        return TABLE(THEAD(labels),
                     TBODY(trs),
                     TFOOT(),
                     _class="embeddedComponent")

    # -------------------------------------------------------------------------
    def accept(self, form, master_id=None, format=None):
        """
            Post-processes this form element against the POST data of the
            request, and create/update/delete any related records.

            @param form: the form
            @param master_id: the ID of the master record in the form
            @param format: the data format extension (for audit)
        """

        db = current.db
        s3db = current.s3db
        auth = current.auth
        manager = current.manager

        resource = self.resource

        # Name of the real input field
        fname = self._formname(separator="_")

        if fname in form.vars:

            # Retrieve the data
            data = form.vars[fname]
            if "component" not in data:
                return

            # Get the component
            component_name = data["component"]
            if component_name in resource.components:
                component = resource.components[component_name]
            else:
                return

            # Check the data
            if "data" not in data:
                return

            # Table, tablename, prefix and name of the component
            prefix = component.prefix
            name = component.name
            tablename = component.tablename
            table = component.table

            # Process each item
            permit = component.permit
            audit = component.audit
            validate = manager.validate
            onaccept = manager.onaccept
            for item in data["data"]:

                if not "_changed" in item and not "_delete" in item:
                    # No changes made to this item - skip
                    continue

                # Get the values
                values = Storage()
                for f, d in item.iteritems():
                    if f[0] != "_" and d and isinstance(d, dict):
                        # Must run through validator again (despite pre-validation)
                        # in order to post-process widget output properly (e.g. UTC
                        # offset subtraction)
                        try:
                            value, error = validate(table, None, f, d["value"])
                        except AttributeError:
                            continue
                        if not error:
                            values[f] = value

                if "_id" in item:
                    record_id = item["_id"]

                    # Delete..?
                    if "_delete" in item:
                        authorized = permit("delete", tablename, record_id)
                        if not authorized:
                            continue
                        c = s3db.resource(tablename, id=record_id)
                        ondelete = s3db.get_config(tablename, "ondelete")
                        # Audit happens inside .delete()
                        success = c.delete(ondelete=ondelete,
                                           cascade=True, format="html")

                    # ...or update?
                    else:
                        authorized = permit("update", tablename, record_id)
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
                                auth.set_realm_entity(table, vars,
                                                      force_update=True)
                            # Onaccept
                            onaccept(table, Storage(vars=values), method="update")
                else:
                    # Create a new record
                    authorized = permit("create", tablename)
                    if not authorized:
                        continue
                    # Update the master table foreign key
                    pkey = component.pkey
                    fkey = component.fkey
                    mastertable = resource.table
                    if pkey != mastertable._id.name:
                        query = (mastertable._id == master_id)
                        row = db(query).select(mastertable[pkey],
                                               limitby=(0, 1)).first()
                        if not row:
                            return
                        values[fkey] = row[mastertable[pkey]]
                    else:
                        values[fkey] = master_id

                    # Create the new record
                    record_id = component.table.insert(**values)

                    # Post-process create
                    if record_id:
                        audit("create", prefix, name,
                              record=record_id, representation=format)
                        values[table._id.name] = record_id
                        # Update super entity link
                        s3db.update_super(table, values)
                        # Set record owner
                        auth.s3_set_record_owner(table, record_id)
                        # onaccept
                        onaccept(table, Storage(vars=values), method="create")
        else:
            return False

        # Success
        return True

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
    def _render_headers(self, data, extra_columns=0, **attributes):
        """
            Render the header row with field labels

            @param data: the input field data as Python object
            @param extra_columns: number of (empty) extra columns to add
            @param attributes: HTML attributes for the header row
        """

        fields = data["fields"]
        labels = [TD(LABEL(f["label"])) for f in fields]
        # @ToDo: Is this required? Header Row doesn't have to be the same number of columns
        for i in range(extra_columns):
            labels.append(TD())
        return TR(labels, **attributes)

    # -------------------------------------------------------------------------
    def _action_icon(self, title, image, name, index, throbber=False):
        """
            Render an action icon for one of the form actions

            @param title: title for the icon
            @param image: name of the image file in static/img/crud
            @param name: element name of the action icon
            @param index: the row index within the form
            @param throbber: True to render a hidden throbber (activity
                             indicator) for this icon
        """

        appname = current.request.application
        icon_path = "/%s/static/img/crud/%s" % (appname, image)
        throbber_path = "/%s/static/img/indicator.gif" % appname

        formname = self._formname()

        action = A(IMG(_src=icon_path, _title=title, _alt=title),
                   _href="#",
                   _id="%s-%s-%s" % (name, formname, index),
                   _class="inline-%s" % name)

        if throbber:
            return DIV(action,
                       IMG(_src=throbber_path,
                           _alt=current.T("Processing"),
                           _class="hide",
                           _id="throbber-%s-%s" % (formname, index)))
        else:
            return DIV(action)

    # -------------------------------------------------------------------------
    def _render_item(self, table, item, fields,
                     readonly=True,
                     editable=False,
                     deletable=False,
                     index="none",
                     **attributes):
        """
            Render a read- or edit-row.

            @param table: the database table
            @param item: the data
            @param fields: the fields to render (list of strings)
            @param readonly: render a read-row (otherwise edit-row)
            @param editable: whether the record can be edited
            @param deletable: whether the record can be deleted
            @param index: the row index
            @param attributes: HTML attributes for the row
        """

        T = current.T
        appname = current.request.application

        formname = self._formname()

        action = self._action_icon

        # Render the action icons for this item
        add = action(T("Add this entry"),
                     "add.png", "add", index, throbber=True)
        rmv = action(T("Remove this entry"),
                     "remove.png", "rmv", index)
        edt = action(T("Edit this entry"),
                     "edit.png", "edt", index)
        cnc = action(T("Cancel editing"),
                     "cancel.png", "cnc", index)
        rdy = action(T("Update this entry"),
                     "apply.png", "rdy", index, throbber=True)

        columns = []
        rowtype = readonly and "read" or "edit"
        pkey = table._id.name

        data = dict()
        formfields = []
        formname = self._formname()
        validate = current.manager.validate
        for f in fields:
            fname = f["name"]
            idxname = "%s_%s_%s_%s" % (formname, fname, rowtype, index)
            formfield = self._rename_field(table[fname], idxname,
                                           skip_post_validation=True)

            # Get reduced options set
            options = self._filterby_options(fname)
            if options:
                if len(options) < 2:
                    formfield.requires = IS_IN_SET(options, zero=None)
                else:
                    formfield.requires = IS_IN_SET(options)

            # Get filterby-default
            defaults = self._filterby_defaults()
            if defaults and fname in defaults:
                default = defaults[fname]["value"]
                formfield.default = default

            if index is not None and item and fname in item:
                value = item[fname]["value"]
                value, error = validate(table, None, fname, value)
                if error:
                    value = None
                data[idxname] = value
            formfields.append(formfield)
        if not data:
            data = None
        elif pkey not in data:
            data[pkey] = None

        subform_name = "sub_%s" % formname

        subform = SQLFORM.factory(*formfields,
                                  record=data,
                                  showid=False,
                                  formstyle=self._formstyle,
                                  upload = "default/download",
                                  readonly=readonly,
                                  table_name=subform_name)

        for tr in subform[0]:
            if not tr.attributes["_id"] == "submit_record__row":
                columns.append(tr[0])

        if readonly:
            if editable:
                columns.append(edt)
            else:
                columns.append(TD())
            if deletable:
                columns.append(rmv)
            else:
                columns.append(TD())
        else:
            if index != "none" or item:
                columns.append(rdy)
                columns.append(cnc)
            else:
                columns.append(TD())
                columns.append(add)

        return TR(columns, **attributes)

    # -------------------------------------------------------------------------
    def _filterby_query(self):
        """
            Render the filterby-options as Query to apply when retrieving
            the existing rows in this inline-component
        """

        if "filterby" in self.options:
            filterby = self.options["filterby"]
        else:
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
                defaults[fieldname] = {"value":default}

        return defaults

    # -------------------------------------------------------------------------
    def _filterby_options(self, fieldname):
        """
            Re-render the options list for a field if there is a
            filterby-restriction.

            @param fieldname: the name of the field
        """

        if "filterby" in self.options:
            filterby = self.options["filterby"]
        else:
            return None
        if not isinstance(filterby, (list, tuple)):
            filterby = [filterby]

        component = self.resource.components[self.selector]
        table = component.table

        if fieldname not in table.fields:
            return None
        field = table[fieldname]

        filter_fields = dict([(f["field"], f) for f in filterby])
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
                empty = True
                r = r.other
            # Currently only supporting IS_IN_SET
            if not isinstance(r, IS_IN_SET):
                return None
        else:
            return None
        r_opts = r.options()

        # Get the filter options
        options = f["options"]
        if not isinstance(options, (list, tuple)):
            options = [options]
        subset = []
        if "invert" in f:
            invert = f["invert"]
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
    @staticmethod
    def _formstyle(id, label, widget, comment):
        """
            Formstyle for the inline rows

            @param id: the HTML element id
            @param label: the field label
            @param widget: the widget
            @param comment: the comment
        """

        if id == "submit_record__row":
            return TR(_id=id)
        else:
            return TR(widget, _id=id)

# END =========================================================================
