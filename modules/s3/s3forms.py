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
from gluon.tools import callback
from s3utils import s3_mark_required

# =============================================================================
class S3Form(object):
    """ Form Base Class """

    # -------------------------------------------------------------------------
    def __init__(self):

        self.form = None

    # -------------------------------------------------------------------------
    def __call__(self):
        pass

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
class S3FormElement(object):
    """ Form Element Base Class """

    # -------------------------------------------------------------------------
    def __init__(self):
        pass

    # -------------------------------------------------------------------------
    def __call__(self):
        pass

# =============================================================================
class S3CRUDForm(S3Form):
    """ Standard CRUD form """

    # -------------------------------------------------------------------------
    def __init__(self, resource):
        """
            Constructor

            @param resource: the S3Resource
        """

        S3Form.__init__(self)

        self.resource = resource

        if resource is not None:
            self.prefix = resource.prefix
            self.name = resource.name

            self.tablename = resource.tablename
            self.table = resource.table

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
                 format=None):

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

            # Pre-populate from a previous record?
            if record_id is None and from_table is not None:
                # Field mapping
                if map_fields:
                    if isinstance(map_fields, dict):
                        fields = [from_table[map_fields[f]]
                                for f in map_fields
                                    if f in table.fields and
                                    map_fields[f] in from_table.fields and
                                    table[f].writable]
                    elif isinstance(map_fields, (list, tuple)):
                        fields = [from_table[f]
                                for f in map_fields
                                    if f in table.fields and
                                    f in from_table.fields and
                                    table[f].writable]
                    else:
                        raise TypeError
                else:
                    fields = [from_table[f]
                              for f in table.fields
                              if f in from_table.fields and table[f].writable]
                # Audit read => this is a read method, finally
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
            elif record_id is None and isinstance(data, dict):
                record = Storage([(f, data[f])
                                  for f in data
                                  if f in table.fields and table[f].writable])

            # Add missing fields to pre-populated record
            if record:
                missing_fields = Storage()
                for f in table.fields:
                    if f not in record and table[f].writable:
                        missing_fields[f] = table[f].default
                record.update(missing_fields)
                record.update(id=None)

            # Switch to update method if this request attempts to
            # create a duplicate entry in a link table:
            linked = self.resource.linked
            if request.env.request_method == "POST" and \
            linked is not None:
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

            # Add asterisk to labels of required fields
            mark_required = self._config("mark_required", default = [])
            labels, required = s3_mark_required(table, mark_required)
            if required:
                # Show the key if there are any required fields.
                s3.has_required = True
            else:
                s3.has_required = False

        if record is None:
            record = record_id

        if format == "plain":
            # Default formstyle works best when we have no formatting
            formstyle = "table3cols"
        else:
            formstyle = settings.formstyle

        # Generate the form
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

        logged = False

        # Process the form
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
    def preprocess(self):
        pass

    # -------------------------------------------------------------------------
    def postprocess(self):
        pass

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

# END =========================================================================
