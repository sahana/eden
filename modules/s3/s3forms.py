# -*- coding: utf-8 -*-

""" S3 Form Builders

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
from s3utils import s3_mark_required

# =============================================================================
class S3SQLForm(object):
    """ Standard CRUD form """

    # -------------------------------------------------------------------------
    def __init__(self, resource):
        """
            Constructor

            @param resource: the S3Resource
        """

        self.resource = resource

        if resource is not None:
            self.prefix = resource.prefix
            self.name = resource.name

            self.tablename = resource.tablename
            self.table = resource.table

    # -------------------------------------------------------------------------
    # Rendering
    # -------------------------------------------------------------------------
    def __call__(self,
                 request=None,
                 data=None,
                 record_id=None,
                 readonly=False,
                 from_table=None,
                 from_record=None,
                 map_fields=None,
                 link=None,
                 onvalidation=None,
                 onaccept=None,
                 message="Record created/updated",
                 subheadings=None,
                 format=None):
        """
            Generate the form
        """

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

            # Pre-populate create-form
            if record_id is None:
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
            formstyle = settings.formstyle

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
    # Processing
    # -------------------------------------------------------------------------
    def process(self, form, vars,
                onvalidation = None,
                onaccept = None,
                link = None,
                http = "POST"):
        """
            Process the form
        """

        manager = current.manager
        audit = manager.audit
        table = self.table
        record_id = self.record_id
        response = current.response

        # Get the proper onvalidation routine
        if isinstance(onvalidation, dict):
            onvalidation = onvalidation.get(self.tablename, [])

        # Append link.postprocess to onvalidation
        if link and link.postprocess:
            postprocess = link.postprocess
            if isinstance(onvalidation, list):
                onvalidation.append(postprocess)
            elif onvalidation is not None:
                onvalidation = [onvalidation, postprocess]
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
            current.s3db.update_super(table, vars)

            # Update component link
            if link and link.postprocess is None:
                resource = link.resource
                master = link.master
                resource.update_link(master, vars)

            if vars.id:
                if record_id is None:
                    # Set record ownership
                    auth = current.auth
                    auth.s3_set_record_owner(table, vars.id)
                    auth.s3_make_session_owner(table, vars.id)
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

# END =========================================================================
