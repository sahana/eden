# -*- coding: utf-8 -*-

"""
    S3 RESTful CRUD Methods

    @see: U{B{I{S3XRC}} <http://eden.sahanafoundation.org/wiki/S3XRC>}

    @requires: U{B{I{gluon}} <http://web2py.com>}
    @requires: U{B{I{lxml}} <http://codespeak.net/lxml>}

    @author: Dominic König <dominic[at]aidiq.com>

    @copyright: 2009-2012 (c) Sahana Software Foundation
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

__all__ = ["S3CRUD"]

from gluon.storage import Storage
from gluon.dal import Row
from gluon import *
from gluon.serializers import json
from gluon.tools import callback

from s3method import S3Method
from s3export import S3Exporter
#from s3gis import S3MAP
from s3pdf import S3PDF
from s3utils import s3_mark_required
from s3widgets import S3EmbedComponentWidget

try:
    from lxml import etree
except ImportError:
    import sys
    print >> sys.stderr, "ERROR: lxml module needed for XML handling"
    raise

# =============================================================================

class S3CRUD(S3Method):
    """
        Interactive CRUD Method Handler

    """

    # -------------------------------------------------------------------------
    def apply_method(self, r, **attr):
        """
            Apply CRUD methods

            @param r: the S3Request
            @param attr: dictionary of parameters for the method handler

            @returns: output object to send to the view
        """

        manager = current.manager
        self.settings = manager.s3.crud

        # Pre-populate create-form?
        self.data = None
        if r.http == "GET" and not self.record:
            populate = attr.pop("populate", None)
            if callable(populate):
                try:
                    self.data = populate(r, **attr)
                except TypeError:
                    self.data = None
                except:
                    raise
            elif isinstance(populate, dict):
                self.data = populate

        if r.http == "DELETE" or self.method == "delete":
            output = self.delete(r, **attr)
        elif self.method == "create":
            output = self.create(r, **attr)
        elif self.method == "read":
            output = self.read(r, **attr)
        elif self.method == "update":
            output = self.update(r, **attr)
        elif self.method == "list":
            output = self.select(r, **attr)
        else:
            r.error(405, manager.ERROR.BAD_METHOD)

        return output

    # -------------------------------------------------------------------------
    def create(self, r, **attr):
        """
            Create new records

            @param r: the S3Request
            @param attr: dictionary of parameters for the method handler
        """

        manager = current.manager
        session = current.session
        request = self.request
        response = current.response
        T = current.T

        resource = self.resource
        table = resource.table
        tablename = resource.tablename

        representation = r.representation

        output = dict()

        # Get table configuration
        _config = self._config
        insertable = _config("insertable", True)
        if not insertable:
            if r.method is not None:
                r.error(405, self.resource.ERROR.BAD_METHOD)
            else:
                return dict(form=None)

        authorised = self._permitted(method="create")
        if not authorised:
            if r.method is not None:
                r.unauthorised()
            else:
                return dict(form=None)

        # Get callbacks
        onvalidation = _config("create_onvalidation") or \
                       _config("onvalidation")
        onaccept = _config("create_onaccept") or \
                   _config("onaccept")

        if r.interactive:

            # Configure the HTML Form

            # Set view
            if representation in ("popup", "iframe"):
                response.view = self._view(r, "popup.html")
                output["caller"] = request.vars.caller
            else:
                response.view = self._view(r, "create.html")

            # Title and subtitle
            crud_string = self.crud_string
            if r.component:
                title = crud_string(r.tablename, "title_display")
                subtitle = crud_string(tablename, "subtitle_create")
                output["title"] = title
                output["subtitle"] = subtitle
            else:
                title = crud_string(tablename, "title_create")
                output["title"] = title

            # Component join
            link = None
            if r.component:
                if resource.link is None:
                    link = self._embed_component(resource, record=r.id)
                    pkey = resource.pkey
                    fkey = resource.fkey
                    field = table[fkey]
                    value = r.record[pkey]
                    field.comment = None
                    field.default = value
                    field.update = value
                    if r.http=="POST":
                        r.post_vars.update({fkey: value})
                    field.readable = False
                    field.writable = False
                else:
                    link = Storage(resource=resource.link, master=r.record)

            # Copy record
            from_table = None
            from_record = r.get_vars.get("from_record", None)
            map_fields = r.get_vars.get("from_fields", None)

            if from_record:
                del r.get_vars["from_record"] # forget it
                if from_record.find(".") != -1:
                    from_table, from_record = from_record.split(".", 1)
                    from_table = current.db.get(from_table, None)
                    if not from_table:
                        r.error(404, self.resource.ERROR.BAD_RESOURCE)
                else:
                    from_table = table
                try:
                    from_record = long(from_record)
                except:
                    r.error(404, self.resource.ERROR.BAD_RECORD)
                authorised = self.permit("read",
                                         from_table._tablename,
                                         from_record)
                if not authorised:
                    r.unauthorised()
                if map_fields:
                    del r.get_vars["from_fields"]
                    if map_fields.find("$") != -1:
                        mf = map_fields.split(",")
                        mf = [f.find("$") != -1 and f.split("$") or \
                             [f, f] for f in mf]
                        map_fields = Storage(mf)
                    else:
                        map_fields = map_fields.split(",")

            # Success message
            message = crud_string(self.tablename, "msg_record_created")

            # Copy formkey if un-deleting a duplicate
            if "id" in request.post_vars:
                original = str(request.post_vars.id)
                formkey = session.get("_formkey[%s/None]" % tablename)
                formname = "%s/%s" % (tablename, original)
                session["_formkey[%s]" % formname] = formkey
                if "deleted" in table:
                    table.deleted.writable = True
                    request.post_vars.update(deleted=False)
                request.post_vars.update(_formname=formname, id=original)
                request.vars.update(**request.post_vars)
            else:
                original = None

            # Get the form
            form = self.sqlform(record_id=original,
                                from_table=from_table,
                                from_record=from_record,
                                map_fields=map_fields,
                                onvalidation=onvalidation,
                                onaccept=onaccept,
                                link=link,
                                message=message,
                                format=representation)

            # Insert subheadings
            subheadings = _config("subheadings")
            if subheadings:
                self.insert_subheadings(form, tablename, subheadings)

            # Cancel button?
            if response.s3.cancel:
                form[0][-1][0].append(A(T("Cancel"),
                                      _href=response.s3.cancel,
                                      _class="action-lnk"))

            # Navigate-away confirmation
            if self.settings.navigate_away_confirm:
                form.append(SCRIPT("S3EnableNavigateAwayConfirm();"))

            # Put the form into output
            output["form"] = form

            # Buttons
            buttons = self.insert_buttons(r, "list")
            if buttons:
                output["buttons"] = buttons

            # Redirection
            create_next = _config("create_next")
            if session.s3.rapid_data_entry and not r.component:
                create_next = r.url()

            if representation in ("popup", "iframe"):
                self.next = None
            elif not create_next:
                self.next = r.url(method="")
            else:
                try:
                    self.next = create_next(self)
                except TypeError:
                    self.next = create_next

        elif representation == "url":
            results = self.import_url(r)
            return results

        elif representation == "csv":
            import cgi
            import csv
            csv.field_size_limit(1000000000)
            infile = request.vars.filename
            if isinstance(infile, cgi.FieldStorage) and infile.filename:
                infile = infile.file
            else:
                try:
                    infile = open(infile, "rb")
                except:
                    session.error = T("Cannot read from file: %s" % infile)
                    redirect(r.url(method="", representation="html"))
            try:
                self.import_csv(infile, table=table)
            except:
                session.error = T("Unable to parse CSV file or file contains invalid data")
            else:
                session.confirmation = T("Data uploaded")

        elif representation == "pdf":
            exporter = S3PDF()
            return exporter(r, **attr)

        else:
            r.error(501, manager.ERROR.BAD_FORMAT)

        return output

    # -------------------------------------------------------------------------
    def read(self, r, **attr):
        """
            Read a single record

            @param r: the S3Request
            @param attr: dictionary of parameters for the method handler
        """

        manager = current.manager
        session = current.session
        request = self.request
        response = current.response

        resource = self.resource
        table = resource.table
        tablename = resource.tablename

        T = current.T

        representation = r.representation

        output = dict()

        _config = self._config
        editable = _config("editable", True)
        deletable = _config("deletable", True)
        list_fields = _config("list_fields")

        # List fields
        if not list_fields:
            fields = resource.readable_fields()
        else:
            fields = [table[f] for f in list_fields if f in table.fields]
        if not fields:
            fields = []
        if fields[0].name != table.fields[0]:
            fields.insert(0, table[table.fields[0]])

        # Get the target record ID
        record_id = self._record_id(r)

        # Check authorization to read the record
        authorised = self._permitted()
        if not authorised:
            r.unauthorised()

        if r.interactive:

            # If this is a single-component and no record exists,
            # try to create one if the user is permitted
            if not record_id and r.component and not r.multiple:
                authorised = self._permitted(method="create")
                if authorised:
                    return self.create(r, **attr)
                else:
                    return self.select(r, **attr)

            # Redirect to update if user has permission unless
            # a method has been specified in the URL
            if not r.method:
                authorised = self._permitted("update")
                if authorised and representation == "html" and editable:
                    return self.update(r, **attr)

            # Form configuration
            subheadings = _config("subheadings")

            # Title and subtitle
            crud_string = self.crud_string
            title = crud_string(r.tablename, "title_display")
            output["title"] = title
            if r.component:
                subtitle = crud_string(tablename, "title_display")
                output["subtitle"] = subtitle

            # Item
            if record_id:
                item = self.sqlform(record_id=record_id,
                                    readonly=True,
                                    format=representation)
                if subheadings:
                    self.insert_subheadings(item, self.tablename, subheadings)
            else:
                item = crud_string(tablename, "msg_list_empty")

            # View
            if representation == "html":
                response.view = self._view(r, "display.html")
                output["item"] = item
            elif representation in ("popup", "iframe"):
                response.view = self._view(r, "popup.html")
                caller = attr.get("caller", None)
                output["form"] = item
                output["caller"] = caller

            # Buttons
            buttons = self.insert_buttons(r, "edit", "delete", "list",
                                          record_id=record_id)
            if buttons:
                output["buttons"] = buttons

            # Last update
            last_update = self.last_update()
            if last_update:
                output["modified_on"] = last_update["modified_on"]
                output["modified_by"] = last_update["modified_by"]

        elif representation == "plain":
            # Hide empty fields from popups on map
            for field in table:
                if field.readable:
                    value = resource._rows.records[0][tablename][field.name]
                    if value is None or value == "" or value == []:
                        field.readable = False

            # Form
            item = self.sqlform(record_id=record_id,
                                readonly=True,
                                format=representation)
            output["item"] = item

            # Details Link
            authorised = self._permitted(method="read")
            if authorised:
                popup_url = _config("popup_url", None)
                if not popup_url:
                    popup_url = r.url(method="read", representation="html")
                if popup_url:
                    details_btn = A(T("Show Details"), _href=popup_url,
                                    _id="details-btn", _target="_blank")
                    output["details_btn"] = details_btn

            # Title and subtitle
            title = self.crud_string(r.tablename, "title_display")
            output["title"] = title

            response.view = "plain.html"

        elif representation == "csv":
            exporter = resource.exporter.csv
            return exporter(resource)

        #elif representation == "map":
        #    exporter = S3MAP()
        #    return exporter(r, **attr)

        elif representation == "pdf":
            exporter = S3PDF()
            return exporter(r, **attr)

        elif representation == "xls":
            list_fields = _config("list_fields")
            exporter = resource.exporter.xls
            return exporter(resource, list_fields=list_fields)

        elif representation == "json":
            exporter = S3Exporter()
            return exporter.json(resource)

        else:
            r.error(501, manager.ERROR.BAD_FORMAT)

        return output

    # -------------------------------------------------------------------------
    def update(self, r, **attr):
        """
            Update a record

            @param r: the S3Request
            @param attr: dictionary of parameters for the method handler
        """

        manager = current.manager
        session = current.session
        request = self.request
        response = current.response
        T = current.T

        resource = self.resource
        table = resource.table
        tablename = resource.tablename

        representation = r.representation

        output = dict()

        # Get table configuration
        _config = self._config
        editable = _config("editable", True)
        deletable = _config("deletable", True)

        # Get callbacks
        onvalidation = _config("update_onvalidation") or \
                       _config("onvalidation")
        onaccept = _config("update_onaccept") or \
                   _config("onaccept")

        # Get the target record ID
        record_id = self._record_id(r)
        if r.interactive and not record_id:
            r.error(404, self.resource.ERROR.BAD_RECORD)

        # Check if editable
        if not editable:
            if r.interactive:
                return self.read(r, **attr)
            else:
                r.error(405, self.resource.ERROR.BAD_METHOD)

        # Check permission for update
        authorised = self._permitted(method="update")
        if not authorised:
            r.unauthorised()

        if r.interactive:

            # Form configuration
            subheadings = _config("subheadings")

            # Set view
            if representation == "html":
                response.view = self._view(r, "update.html")
            elif representation in ("popup", "iframe"):
                response.view = self._view(r, "popup.html")
            elif representation == "plain":
                response.view = self._view(r, "plain.html")

            # Title and subtitle
            crud_string = self.crud_string
            if r.component:
                title = crud_string(r.tablename, "title_display")
                subtitle = crud_string(self.tablename, "title_update")
                output["title"] = title
                output["subtitle"] = subtitle
            else:
                title = crud_string(self.tablename, "title_update")
                output["title"] = title

            # Component join
            link = None
            if r.component:
                if resource.link is None:
                    link = self._embed_component(resource, record=r.id)
                    pkey = resource.pkey
                    fkey = resource.fkey
                    field = table[fkey]
                    value = r.record[pkey]
                    field.comment = None
                    field.default = value
                    field.update = value
                    if r.http=="POST":
                        r.post_vars.update({fkey: value})
                    field.readable = False
                    field.writable = False
                else:
                    link = Storage(resource=resource.link, master=r.record)

            # Success message
            message = crud_string(self.tablename, "msg_record_modified")

            # Get the form
            form = self.sqlform(record_id=record_id,
                                onvalidation=onvalidation,
                                onaccept=onaccept,
                                message=message,
                                link=link,
                                format=representation)

            # Insert subheadings
            if subheadings:
                self.insert_subheadings(form, tablename, subheadings)

            # Cancel button?
            if response.s3.cancel:
                form[0][-1][0].append(A(T("Cancel"),
                                        _href=response.s3.cancel,
                                        _class="action-lnk"))

            # Navigate-away confirmation
            if self.settings.navigate_away_confirm:
                form.append(SCRIPT("S3EnableNavigateAwayConfirm();"))

            # Put form into output
            output["form"] = form

            # Add delete and list buttons
            buttons = self.insert_buttons(r, "delete",
                                          record_id=record_id)
            if buttons:
                output["buttons"] = buttons

            # Last update
            last_update = self.last_update()
            if last_update:
                output["modified_on"] = last_update["modified_on"]
                try:
                    output["modified_by"] = last_update["modified_by"]
                except:
                    # Field not in table - e.g. auth_user
                    pass

            # Redirection
            update_next = _config("update_next")
            if representation in ("popup", "iframe"):
                self.next = None
            elif not update_next:
                self.next = r.url(method="")
            else:
                try:
                    self.next = update_next(self)
                except TypeError:
                    self.next = update_next

        elif representation == "url":
            return self.import_url(r)

        else:
            r.error(501, manager.ERROR.BAD_FORMAT)

        return output

    # -------------------------------------------------------------------------
    def delete(self, r, **attr):
        """
            Delete record(s)

            @param r: the S3Request
            @param attr: dictionary of parameters for the method handler

            @todo: update for link table components
        """

        session = current.session
        request = self.request
        response = current.response
        manager = current.manager
        T = current.T

        table = self.table
        tablename = self.tablename

        representation = r.representation

        output = dict()

        # Get callback
        ondelete = self._config("ondelete")

        # Get table-specific parameters
        deletable = self._config("deletable", True)
        delete_next = self._config("delete_next", None)

        # Get the target record ID
        record_id = self._record_id(r)

        # Check if deletable
        if not deletable:
            r.error(403, manager.ERROR.NOT_PERMITTED,
                    next=r.url(method=""))

        # Check permission to delete
        authorised = self._permitted()
        if not authorised:
            r.unauthorised()

        elif r.interactive and r.http == "GET" and not record_id:
            # Provide a confirmation form and a record list
            form = FORM(TABLE(TR(
                        TD(self.settings.confirm_delete,
                           _style="color: red;"),
                        TD(INPUT(_type="submit", _value=T("Delete"),
                           _style="margin-left: 10px;")))))
            items = self.select(r, **attr).get("items", None)
            if isinstance(items, DIV):
                output.update(form=form)
            output.update(items=items)
            response.view = self._view(r, "delete.html")

        elif r.interactive and (r.http == "POST" or
                                r.http == "GET" and record_id):
            # Delete the records, notify success and redirect to the next view
            numrows = self.resource.delete(ondelete=ondelete,
                                           format=representation)
            if numrows > 1:
                message = "%s %s" % (numrows, T("records deleted"))
            elif numrows == 1:
                message = self.crud_string(self.tablename,
                                           "msg_record_deleted")
            else:
                r.error(404, manager.error, next=r.url(method=""))
            response.confirmation = message
            r.http = "DELETE" # must be set for immediate redirect
            self.next = delete_next or r.url(method="")

        elif r.http == "DELETE":
            # Delete the records and return a JSON message
            numrows = self.resource.delete(ondelete=ondelete,
                                           format=representation)
            if numrows > 1:
                message = "%s %s" % (numrows, T("records deleted"))
            elif numrows == 1:
                message = self.crud_string(self.tablename,
                                           "msg_record_deleted")
            else:
                r.error(404, manager.error, next=r.url(method=""))
            item = manager.xml.json_message(message=message)
            response.view = "xml.html"
            output.update(item=item)

        else:
            r.error(405, manager.ERROR.BAD_METHOD)

        return output

    # -------------------------------------------------------------------------
    def select(self, r, **attr):
        """
            Get a list view of the requested resource

            @param r: the S3Request
            @param attr: dictionary of parameters for the method handler
        """

        session = current.session
        request = self.request
        response = current.response
        manager = current.manager
        s3 = response.s3

        resource = self.resource
        table = self.table
        tablename = self.tablename

        representation = r.representation

        output = dict()

        # Get table-specific parameters
        _config = self._config
        orderby = _config("orderby", None)
        sortby = _config("sortby", [[1, 'asc']])
        linkto = _config("linkto", None)
        insertable = _config("insertable", True)
        listadd = _config("listadd", True)
        addbtn = _config("addbtn", False)
        list_fields = _config("list_fields")
        report_groupby = _config("report_groupby")
        report_hide_comments = _config("report_hide_comments")

        # Check permission to read in this table
        authorised = self._permitted()
        if not authorised:
            r.unauthorised()

        # Pagination
        vars = request.get_vars
        if representation == "aadata":
            start = vars.get("iDisplayStart", None)
            limit = vars.get("iDisplayLength", None)
        else:
            start = vars.get("start", None)
            limit = vars.get("limit", None)
        if limit is not None:
            try:
                start = int(start)
                limit = int(limit)
            except ValueError:
                start = None
                limit = None # use default
        else:
            start = None # use default

        # Linkto
        if not linkto:
            linkto = self._linkto(r)

        # List fields
        if not list_fields:
            fields = resource.readable_fields()
            list_fields = [f.name for f in fields]
        else:
            fields = [table[f] for f in list_fields if f in table.fields]
        if not fields:
            fields = []

        if fields[0].name != table.fields[0]:
            fields.insert(0, table[table.fields[0]])
        if list_fields[0] != table.fields[0]:
            list_fields.insert(0, table.fields[0])

        # Truncate long texts
        if r.interactive or r.representation == "aadata":
            for f in self.table:
                if str(f.type) == "text" and not f.represent:
                    f.represent = self.truncate

        # Filter
        if s3.filter is not None:
            resource.add_filter(s3.filter)

        if r.interactive:

            left = []

            # SSPag?
            if not s3.no_sspag:
                limit = 1
                session.s3.filter = request.get_vars
                if orderby is None:
                    # Default initial sorting
                    scol = len(list_fields) > 1 and "1" or "0"
                    vars.update(iSortingCols="1",
                                iSortCol_0=scol,
                                sSortDir_0="asc")
                    orderby = self.ssp_orderby(resource, list_fields, left=left)
                    del vars["iSortingCols"]
                    del vars["iSortCol_0"]
                    del vars["sSortDir_0"]
                if r.method == "search" and not orderby:
                    orderby = fields[0]

            # Custom view
            response.view = self._view(r, "list.html")

            crud_string = self.crud_string
            if insertable:
                if listadd:
                    # Add a hidden add-form and a button to activate it
                    form = self.create(r, **attr).get("form", None)
                    if form is not None:
                        output["form"] = form
                        addtitle = crud_string(tablename, "subtitle_create")
                        output["addtitle"] = addtitle
                        showadd_btn = self.crud_button(
                                            None,
                                            tablename=tablename,
                                            name="label_create_button",
                                            _id="show-add-btn")
                        output["showadd_btn"] = showadd_btn
                        # Switch to list_create view
                        response.view = self._view(r, "list_create.html")

                elif addbtn:
                    # Add an action-button linked to the create view
                    buttons = self.insert_buttons(r, "add")
                    if buttons:
                        output["buttons"] = buttons

            # Get the list
            items = resource.sqltable(fields=list_fields,
                                      left=left,
                                      start=start,
                                      limit=limit,
                                      orderby=orderby,
                                      linkto=linkto,
                                      download_url=self.download_url,
                                      format=representation)

            # In SSPag, send the first 20 records together with the initial
            # response (avoids the dataTables Ajax request unless the user
            # tries nagivating around)
            if not s3.no_sspag and items:
                totalrows = resource.count()
                if totalrows:
                    if s3.dataTable_iDisplayLength:
                        limit = 2 * s3.dataTable_iDisplayLength
                    else:
                        limit = 50
                    sqltable =  resource.sqltable(left=left,
                                                  fields=list_fields,
                                                  start=0,
                                                  limit=limit,
                                                  orderby=orderby,
                                                  linkto=linkto,
                                                  download_url=self.download_url,
                                                  as_page=True,
                                                  format=representation)
                    aadata = dict(aaData = sqltable or [])
                    aadata.update(iTotalRecords=totalrows,
                                  iTotalDisplayRecords=totalrows)
                    response.aadata = json(aadata)
                    s3.start = 0
                    s3.limit = limit

            # Title and subtitle
            if r.component:
                title = crud_string(r.tablename, "title_display")
            else:
                title = crud_string(self.tablename, "title_list")
            subtitle = crud_string(self.tablename, "subtitle_list")
            output["title"] = title
            output["subtitle"] = subtitle

            # Empty table - or just no match?
            if not items:
                if "deleted" in self.table:
                    available_records = current.db(self.table.deleted == False)
                else:
                    available_records = current.db(self.table.id > 0)
                #if available_records.count():
                # This is faster:
                if available_records.select(self.table.id,
                                            limitby=(0, 1)).first():
                    items = crud_string(self.tablename, "msg_no_match")
                else:
                    items = crud_string(self.tablename, "msg_list_empty")
                if r.component and "showadd_btn" in output:
                    # Hide the list and show the form by default
                    del output["showadd_btn"]
                    del output["subtitle"]
                    items = ""
                    s3.no_formats = True

            # Update output
            output["items"] = items
            output["sortby"] = sortby

        elif representation == "aadata":

            left = []
            distinct = r.method == "search"

            # Get the master query for SSPag
            if session.s3.filter is not None:
                resource.build_query(filter=s3.filter,
                                     vars=session.s3.filter)

            displayrows = totalrows = resource.count(distinct=distinct)

            # SSPag dynamic filter?
            if vars.sSearch:
                squery = self.ssp_filter(table,
                                         fields=list_fields,
                                         left=left)
                if squery is not None:
                    resource.add_filter(squery)
                    displayrows = resource.count(left=left,
                                                 distinct=distinct)

            # SSPag sorting
            if vars.iSortingCols:
                orderby = self.ssp_orderby(resource, list_fields, left=left)
            if r.method == "search" and not orderby:
                orderby = fields[0]
            if orderby is None:
                orderby = _config("orderby", None)

            # Echo
            sEcho = int(vars.sEcho or 0)

            # Get the list
            items = resource.sqltable(fields=list_fields,
                                      left=left,
                                      distinct=distinct,
                                      start=start,
                                      limit=limit,
                                      orderby=orderby,
                                      linkto=linkto,
                                      download_url=self.download_url,
                                      as_page=True,
                                      format=representation) or []

            result = dict(sEcho = sEcho,
                          iTotalRecords = totalrows,
                          iTotalDisplayRecords = displayrows,
                          aaData = items)

            output = json(result)

        elif representation == "plain":
            items = resource.sqltable(fields=list_fields,
                                      as_list=True)
            response.view = "plain.html"
            return dict(item=items)

        elif representation == "csv":
            exporter = S3Exporter()
            return exporter.csv(resource)

        #elif representation == "map":
        #    exporter = S3MAP()
        #    return exporter(r, **attr)

        elif representation == "pdf":
            exporter = S3PDF()
            return exporter(r, **attr)

        elif representation == "xls":
            exporter = S3Exporter()
            return exporter.xls(resource,
                                list_fields=list_fields,
                                report_groupby=report_groupby,
                                **attr)

        elif representation == "json":
            exporter = S3Exporter()
            return exporter.json(resource,
                                 start=start,
                                 limit=limit,
                                 fields=fields,
                                 orderby=orderby)

        else:
            r.error(501, manager.ERROR.BAD_FORMAT)

        return output

    # -------------------------------------------------------------------------
    # Utility functions
    # -------------------------------------------------------------------------
    def sqlform(self,
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
        """
            DRY helper function for SQLFORMs in CRUD

            @todo: parameter docstring?
        """

        manager = current.manager
        session = current.session
        request = self.request
        response = current.response

        # Get the CRUD settings
        audit = manager.audit
        s3 = manager.s3
        settings = s3.crud

        # Table and model
        prefix = self.prefix
        name = self.name
        resource = self.resource
        tablename = self.tablename
        table = self.table
        model = manager.model

        record = None
        labels = None

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
            elif record_id is None and isinstance(self.data, dict):
                record = Storage([(f, self.data[f])
                                  for f in self.data
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
            if request.env.request_method == "POST" and \
            resource.linked is not None:
                pkey = table._id.name
                if not request.post_vars[pkey]:
                    linked = resource.linked
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
            mark_required = self._config("mark_required")
            labels, required = s3_mark_required(table, mark_required)
            if required:
                # Show the key if there are any required fields.
                response.s3.has_required = True
            else:
                response.s3.has_required = False

        if record is None:
            record = record_id

        if format == "plain":
            # Default formstyle works best when we have no formatting
            formstyle = "table3cols"
        else:
            formstyle = settings.formstyle

        # Get the form
        form = SQLFORM(table,
                       record = record,
                       record_id = record_id,
                       readonly = readonly,
                       comments = not readonly,
                       deletable = False,
                       showid = False,
                       upload = self.download_url,
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

        # Process the form
        logged = False
        if not readonly:
            # Set form name
            formname = "%s/%s" % (self.tablename, form.record_id)

            # Get the proper onvalidation routine
            if isinstance(onvalidation, dict):
                onvalidation = onvalidation.get(self.tablename, [])

            if link and link.postprocess:
                postprocess = link.postprocess
                if isinstance(onvalidation, list):
                    onvalidation.append(postprocess)
                elif onvalidation is not None:
                    onvalidation = [onvalidation, postprocess]
                else:
                    onvalidation = [postprocess]

            if form.accepts(request.post_vars,
                            session,
                            formname=formname,
                            onvalidation=onvalidation,
                            keepvalues=False,
                            hideerror=False):

                # Message
                response.confirmation = message

                # Audit
                if record_id is None:
                    audit("create", prefix, name, form=form,
                          representation=format)
                else:
                    audit("update", prefix, name, form=form,
                          record=record_id, representation=format)
                logged = True

                vars = form.vars
                # Update super entity links
                model.update_super(table, vars)

                # Update component link
                if link and link.postprocess is None:
                    resource = link.resource
                    master = link.master
                    resource.update_link(master, vars)

                if vars.id:
                    if record_id is None:
                        auth = current.auth
                        # Set record ownership properly
                        auth.s3_set_record_owner(table,
                                                 vars.id)
                        auth.s3_make_session_owner(table,
                                                   vars.id)
                    # Store session vars
                    self.resource.lastid = str(vars.id)
                    manager.store_session(prefix, name, vars.id)

                # Execute onaccept
                callback(onaccept, form, tablename=tablename)

            elif form.errors:
                table = self.table
                if not response.error:
                    response.error = ""
                for fieldname in form.errors:
                    if fieldname in table and \
                       isinstance(table[fieldname].requires, IS_LIST_OF):
                        # IS_LIST_OF validation errors need special handling
                        response.error = "%s\n%s: %s" % \
                            (response.error, fieldname, form.errors[fieldname])

        if not logged and not form.errors:
            audit("read", prefix, name,
                  record=record_id, representation=format)

        return form

    # -------------------------------------------------------------------------
    @staticmethod
    def crud_button(label,
                    tablename=None,
                    name=None,
                    _href=None,
                    _id=None,
                    _class="action-btn"):
        """
            Generate a CRUD action button

            @param label: the link label (None if using CRUD string)
            @param tablename: the name of table for CRUD string selection
            @param name: name of CRUD string for the button label
            @param _href: the target URL
            @param _id: the HTML-ID of the link
            @param _class: the HTML-class of the link
        """

        if name:
            labelstr = S3CRUD.crud_string(tablename, name)
        else:
            labelstr = str(label)
        if not _href:
            button = A(labelstr, _id=_id, _class=_class)
        else:
            button = A(labelstr, _href=_href, _id=_id, _class=_class)
        return button

    # -------------------------------------------------------------------------
    @staticmethod
    def crud_string(tablename, name):
        """
        Get a CRUD info string for interactive pages

        @param tablename: the table name
        @param name: the name of the CRUD string

        """

        crud_strings = current.manager.s3.crud_strings

        not_found = crud_strings.get(name, None)
        crud_strings = crud_strings.get(tablename, crud_strings)

        return crud_strings.get(name, not_found)

    # -------------------------------------------------------------------------
    def last_update(self):
        """
            Get the last update meta-data
        """

        db = current.db
        table = self.table
        record_id = self.record

        T = current.T

        output = dict()

        if record_id:
            fields = []
            if "modified_on" in table.fields:
                fields.append(table.modified_on)
            if "modified_by" in table.fields:
                fields.append(table.modified_by)

            query = table._id == record_id
            record = db(query).select(limitby=(0, 1), *fields).first()

            try:
                represent = table.modified_by.represent
            except:
                # Table doesn't have a modified_by field
                represent = ""

            # @todo: "on" and "by" particles are problematic in translations
            if "modified_by" in record and represent:
                if not record.modified_by:
                    modified_by = T("anonymous user")
                else:
                    modified_by = represent(record.modified_by)
                output["modified_by"] = T("by %(person)s") % \
                                           dict(person = modified_by)
            if "modified_on" in record:
                output["modified_on"] = T("on %(date)s") % \
                              dict(date = record.modified_on)

        return output

    # -------------------------------------------------------------------------
    @staticmethod
    def truncate(text, length=48, nice=True):
        """
            Nice truncating of text

            @param text: the text
            @param length: the desired maximum length of the output
            @param nice: don't truncate in the middle of a word
        """

        if text is None:
            return ""

        if len(text) > length:
            l = length - 3
            if nice:
                return "%s..." % text[:l].rsplit(" ", 1)[0][:l]
            else:
                return "%s..." % text[:l]
        else:
            return text

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

    # -------------------------------------------------------------------------
    def insert_buttons(self, r, *buttons, **attr):
        """
            Insert resource action buttons

            @param r: the S3Request
            @param buttons: button names ("add", "edit", "delete", "list")
            @keyword record_id: the record ID
        """

        output = dict()

        T = current.T

        tablename = self.tablename
        representation = r.representation

        record_id = attr.get("record_id", None)

        # Button labels
        ADD = self.crud_string(tablename, "label_create_button")
        EDIT = T("Edit")
        DELETE = self.crud_string(tablename, "label_delete_button")
        LIST = self.crud_string(tablename, "label_list_button")

        # Button URLs
        href_add = r.url(method="create", representation=representation)
        href_edit = r.url(method="update", representation=representation)
        href_delete = r.url(method="delete", representation=representation)
        href_list = r.url(method="")

        # Table CRUD configuration
        insertable = self._config("insertable", True)
        editable = self._config("editable", True)
        deletable = self._config("deletable", True)

        # Add button
        if "add" in buttons:
            authorised = self._permitted(method="create")
            if authorised and href_add and insertable:
                add_btn = self.crud_button(ADD, _href=href_add, _id="add-btn")
                output.update(add_btn=add_btn)

        # List button
        if "list" in buttons:
            if not r.component or r.multiple:
                list_btn = self.crud_button(LIST,
                                            _href=href_list, _id="list-btn")
                output.update(list_btn=list_btn)

        if not record_id:
            return output

        # Edit button
        if "edit" in buttons:
            authorised = self._permitted(method="update")
            if authorised and href_edit and editable and r.method != "update":
                edit_btn = self.crud_button(EDIT, _href=href_edit,
                                            _id="edit-btn")
                output.update(edit_btn=edit_btn)

        # Delete button
        if "delete" in buttons:
            authorised = self._permitted(method="delete")
            if authorised and href_delete and deletable:
                delete_btn = self.crud_button(DELETE, _href=href_delete,
                                              _id="delete-btn",
                                              _class="delete-btn")
                output.update(delete_btn=delete_btn)

        return output

    # -------------------------------------------------------------------------
    @staticmethod
    def action_button(label, url, **attr):
        """
            Add a link to response.s3.actions

            @param label: the link label
            @param url: the target URL
            @param attr: attributes for the link (default: {"_class":"action-btn"})
        """

        response = current.response

        link = dict(attr)
        link.update(label=str(label), url=url)
        if "_class" not in link:
            link.update(_class="action-btn")

        if response.s3.actions is None:
            response.s3.actions = [link]
        else:
            response.s3.actions.append(link)

    # -------------------------------------------------------------------------
    @staticmethod
    def action_buttons(r,
                       deletable=True,
                       editable=True,
                       copyable=False,
                       read_url=None,
                       delete_url=None,
                       update_url=None,
                       copy_url=None):
        """
            Provide the usual action buttons in list views.
            Allow customizing the urls, since this overwrites anything
            that would be inserted by CRUD/select via linkto. The resource
            id should be represented by "[id]".

            @param r: the S3Request
            @param deletable: records can be deleted
            @param editable: records can be modified
            @param copyable: record data can be copied into new record
            @param read_url: URL to read a record
            @param delete_url: URL to delete a record
            @param update_url: URL to update a record
            @param copy_url: URL to copy record data

            @note: If custom actions are already configured at this point,
                   they will appear AFTER the standard action buttons
        """

        s3crud = S3CRUD
        labels = current.manager.LABEL

        db = current.db
        s3 = current.response.s3
        custom_actions = s3.actions
        s3.actions = None

        auth = current.auth
        has_permission = auth.s3_has_permission
        ownership_required = auth.permission.ownership_required

        if r.component:
            table = r.component.table
            args = [r.id, r.component.alias, "[id]"]
        else:
            table = r.table
            args = ["[id]"]

        # Open-action (Update or Read)
        if editable and has_permission("update", table) and \
        not ownership_required(table, "update"):
            if not update_url:
                update_url = URL(args = args + ["update"])
            s3crud.action_button(labels.UPDATE, update_url)
        else:
            if not read_url:
                read_url = URL(args = args)
            s3crud.action_button(labels.READ, read_url)

        # Delete-action
        if deletable and has_permission("delete", table):
            if not delete_url:
                delete_url = URL(args = args + ["delete"])
            if ownership_required(table, "delete"):
                # Check which records can be deleted
                query = auth.s3_accessible_query("delete", table)
                rows = db(query).select(table._id)
                restrict = [str(row.id) for row in rows]
                s3crud.action_button(labels.DELETE, delete_url,
                                     _class="delete-btn", restrict=restrict)
            else:
                s3crud.action_button(labels.DELETE, delete_url,
                                     _class="delete-btn")

        # Copy-action
        if copyable and has_permission("create", table):
            if not copy_url:
                copy_url = URL(args = args + ["copy"])
            s3crud.action_button(labels.COPY, copy_url)

        # Append custom actions
        if custom_actions:
            s3.actions = s3.actions + custom_actions

        return

    # -------------------------------------------------------------------------
    def import_csv(self, file, table=None):
        """
            Import CSV file into database

            @param file: file handle
            @param table: the table to import to
        """

        if table:
            table.import_from_csv_file(file)
        else:
            db = current.db
            # This is the preferred method as it updates reference fields
            db.import_from_csv_file(file)
            db.commit()

    # -------------------------------------------------------------------------
    @staticmethod
    def import_url(r):
        """
            Import data from URL query

            @param r: the S3Request
            @note: can only update single records (no mass-update)

            @todo: update for link table components
            @todo: re-integrate into S3Importer
        """

        manager = current.manager
        xml = manager.xml

        prefix, name, table, tablename = r.target()

        record = r.record
        resource = r.resource

        # Handle components
        if record and r.component:
            resource = resource.components[r.component_name]
            resource.load()
            if len(resource) == 1:
                record = resource.records()[0]
            else:
                record = None
            r.vars.update({resource.fkey: r.record[resource.pkey]})
        elif not record and r.component:
            item = xml.json_message(False, 400, "Invalid Request!")
            return dict(item=item)

        # Check for update
        if record and xml.UID in table.fields:
            r.vars.update({xml.UID: xml.export_uid(record[xml.UID])})

        # Build tree
        element = etree.Element(xml.TAG.resource)
        element.set(xml.ATTRIBUTE.name, resource.tablename)
        for var in r.vars:
            if var.find(".") != -1:
                continue
            elif var in table.fields:
                field = table[var]
                value = str(r.vars[var]).decode("utf-8")
                if var in xml.FIELDS_TO_ATTRIBUTES:
                    element.set(var, value)
                else:
                    data = etree.Element(xml.TAG.data)
                    data.set(xml.ATTRIBUTE.field, var)
                    if field.type == "upload":
                        data.set(xml.ATTRIBUTE.filename, value)
                    else:
                        data.text = xml.xml_encode(value)
                    element.append(data)
        tree = xml.tree([element], domain=manager.domain)

        # Import data
        result = Storage(committed=False)
        manager.log = lambda job, result=result: result.update(job=job)
        try:
            success = resource.import_xml(tree)
        except SyntaxError:
            pass

        # Check result
        if result.job:
            result = result.job

        # Build response
        if success and result.committed:
            r.id = result.id
            method = result.method
            if method == result.METHOD.CREATE:
                item = xml.json_message(True, 201, "Created as %s?%s.id=%s" %
                        (str(r.url(method="",
                                   representation="html",
                                   vars=dict(),
                                  )
                            ),
                         r.name, result.id)
                        )
            else:
                item = xml.json_message(True, 200, "Record updated")
        else:
            item = xml.json_message(False, 403,
                        "Could not create/update record: %s" %
                            resource.error or xml.error,
                        tree=xml.tree2json(tree))

        return dict(item=item)


    # -------------------------------------------------------------------------
    def _embed_component(self, resource, record=None):
        """
            Renders the right key constraint in a link table as
            S3EmbedComponentWidget and stores the postprocess hook.

            @param resource: the link table resource
        """

        link = None

        component = resource.linked
        if component is not None and component.actuate == "embed":
            attr = Storage(link=resource.tablename,
                           component=component.tablename)
            autocomplete = component.autocomplete
            if autocomplete and autocomplete in component.table:
                attr.update(autocomplete=autocomplete)
            if record is not None:
                link_filter = "%s.%s.%s.%s.%s" % (
                                resource.tablename,
                                component.lkey,
                                record,
                                component.rkey,
                                component.fkey)
                attr.update(link_filter=link_filter)
            rkey = component.rkey
            if rkey in resource.table:
                field = resource.table[rkey]
                attr.update(widget=field.widget)
                # @todo: accept custom widgets
                field.widget = S3EmbedComponentWidget(**attr)
                field.comment = None
            postprocess = lambda form, key=rkey, component=attr.component: \
                                 self._postprocess_embedded(form,
                                    key=key, component=component)

            link = Storage(postprocess=postprocess)
        return link

    # -------------------------------------------------------------------------
    def _postprocess_embedded(self, form,
                              component=None,
                              key=None):
        """
            Post-processes a form with an S3EmbedComponentWidget and
            created/updates the component record.

            @param form: the form
            @param component: the component tablename
            @param key: the field name of the foreign key for the component
                        in the link table
        """

        db = current.db
        manager = current.manager
        request = current.request
        T = current.T

        error_message = T("Could not create record.")
        get_config = lambda key, tablename=component: \
                            manager.model.get_config(tablename, key, None)

        try:
            selected = form.vars[key]
        except:
            selected = None

        if request.env.request_method == "POST":
            table = db[component]
            _vars = request.post_vars
            _form = Storage(vars=Storage(table._filter_fields(_vars)),
                            errors=Storage())
            if _form.vars:
                if selected:
                    # Onvalidation
                    onvalidation = get_config("update_onvalidation") or \
                                   get_config("onvalidation")
                    callback(onvalidation, _form, tablename=component)
                    # Update the record if no errors
                    if not _form.errors:
                        db(table._id == selected).update(**_form.vars)
                    else:
                        form.errors.update(_form.errors)
                        return
                    # Super-entity update
                    manager.model.update_super(table, dict(id=selected))
                    # Onaccept
                    onaccept = get_config("update_onaccept") or \
                               get_config("onaccept")
                    callback(onaccept, _form, tablename=component)
                else:
                    # Onvalidation
                    onvalidation = get_config("create_onvalidation") or \
                                   get_config("onvalidation")
                    callback(onvalidation, _form, tablename=component)
                    # Insert the record if no errors
                    if not _form.errors:
                        selected = table.insert(**_form.vars)
                    else:
                        form.errors.update(_form.errors)
                        return
                    if selected:
                        # Update post_vars and form.vars
                        request.post_vars.update({key:str(selected)})
                        form.vars.update({key:selected})
                        # Super-entity update
                        manager.model.update_super(table, dict(id=selected))
                        # Onaccept
                        onaccept = get_config("create_onaccept") or \
                                   get_config("onaccept")
                        callback(onaccept, _form, tablename=component)
                    else:
                        form.errors[key] = error_message
        return

    # -------------------------------------------------------------------------
    def _linkto(self, r, authorised=None, update=None, native=False):
        """
            Returns a linker function for the record ID column in list views

            @param r: the S3Request
            @param authorised: user authorised for update
                (override internal check)
            @param update: provide link to update rather than to read
            @param native: link to the native controller rather than to
                component controller
        """

        c = None
        f = None

        manager = current.manager
        response = current.response

        prefix, name, table, tablename = r.target()
        permit = current.auth.s3_has_permission
        model = manager.model

        if authorised is None:
            authorised = permit("update", tablename)

        if authorised and update:
            linkto = model.get_config(tablename, "linkto_update", None)
        else:
            linkto = model.get_config(tablename, "linkto", None)

        if r.component and native:
            # link to native component controller (be sure that you have one)
            c = prefix
            f = name

        def list_linkto(record_id, r=r, c=c, f=f,
                        linkto=linkto,
                        update=authorised and update):

            if linkto:
                try:
                    url = str(linkto(record_id))
                except TypeError:
                    url = linkto % record_id
                return url
            else:
                if r.component:
                    if r.link and not r.actuate_link():
                        # We're rendering a link table here, but must
                        # however link to the component record IDs
                        if str(record_id).isdigit():
                            # dataTables uses the value in the ID column
                            # to render action buttons, so we replace that
                            # value by the component record ID using .represent
                            _id = r.link.table._id
                            _id.represent = lambda opt, \
                                                   link=r.link, master=r.id: \
                                                   link.component_id(master, opt)
                            # The native link behind the action buttons uses
                            # record_id, so we replace that too just in case
                            # the action button cannot be displayed
                            record_id = r.link.component_id(r.id, record_id)
                    if c and f:
                        args = [record_id]
                    else:
                        c = r.controller
                        f = r.function
                        args = [r.id, r.component_name, record_id]
                    if update:
                        return str(URL(r=r, c=c, f=f,
                                       args=args + ["update"],
                                       vars=r.vars))
                    else:
                        return str(URL(r=r, c=c, f=f,
                                       args=args,
                                       vars=r.vars))
                else:
                    args = [record_id]
                    if update:
                        return str(URL(r=r, c=c, f=f,
                                       args=args + ["update"]))
                    else:
                        return str(URL(r=r, c=c, f=f,
                                       args=args))
        return list_linkto

    # -------------------------------------------------------------------------
    def ssp_filter(self, table, fields, left=[]):
        """
            Convert the SSPag GET vars into a filter query

            @param table: the table
            @param fields: list of field names as displayed in the
                           list view (same order!)
            @param left: list of left joins
        """

        db = current.db
        vars = self.request.get_vars
        resource = self.resource

        context = str(vars.sSearch).lower()
        columns = int(vars.iColumns)

        wildcard = "%%%s%%" % context

        # Retrieve the list of search fields
        lfields, joins, ljoins, distinct = resource.resolve_selectors(fields)
        flist = []
        for i in xrange(0, columns):
            field = lfields[i].field
            if not field:
                continue
            fieldtype = str(field.type)
            if fieldtype.startswith("reference") and \
               hasattr(field, "sortby") and field.sortby:
                tn = fieldtype[10:]
                try:
                    join = [j for j in left if j.first._tablename == tn]
                except:
                    # Old DAL version?
                    join = [j for j in left if j.table._tablename == tn]
                if not join:
                    left.append(db[tn].on(field == db[tn].id))
                else:
                    try:
                        join[0].second = (join[0].second) | (field == db[tn].id)
                    except:
                        join[0].query = (join[0].query) | (field == db[tn].id)
                if isinstance(field.sortby, (list, tuple)):
                    flist.extend([db[tn][f] for f in field.sortby])
                else:
                    if field.sortby in db[tn]:
                        flist.append(db[tn][field.sortby])
            else:
                flist.append(field)

        # Build search query
        searchq = None
        for field in flist:
            query = None
            ftype = str(field.type)
            if ftype in ("integer", "list:integer", "list:string") or \
               ftype.startswith("list:reference") or \
               ftype.startswith("reference"):
                requires = field.requires
                if not isinstance(requires, (list, tuple)):
                    requires = [requires]
                if requires:
                    r = requires[0]
                    if isinstance(r, IS_EMPTY_OR):
                        r = r.other
                    try:
                        options = r.options()
                    except:
                        continue
                    vlist = []
                    for (value, text) in options:
                        if str(text).lower().find(context) != -1:
                            vlist.append(value)
                    if vlist:
                        query = field.belongs(vlist)
                else:
                    continue
            elif str(field.type) in ("string", "text"):
                query = field.lower().like(wildcard)
            if searchq is None and query:
                searchq = query
            elif query:
                searchq = searchq | query

        for j in joins.values():
            for q in j:
                if searchq is None:
                    searchq = q
                elif str(q) not in str(searchq):
                    searchq &= q

        return searchq

    # -------------------------------------------------------------------------
    def ssp_orderby(self, resource, fields, left=[]):
        """
            Convert the SSPag GET vars into a sorting query

            @param table: the table
            @param fields: list of field names as displayed
                           in the list view (same order!)
            @param left: list of left joins
        """

        db = current.db
        vars = self.request.get_vars
        table = resource.table
        tablename = table._tablename

        if resource.linked is not None:
            skip = [resource.linked.tablename]
        else:
            skip = []

        iSortingCols = int(vars["iSortingCols"])

        def direction(i):
            dir = vars["sSortDir_%s" % str(i)]
            return dir and " %s" % dir or ""

        orderby = []

        lfields, joins, ljoins, distinct = resource.resolve_selectors(fields)
        columns = [lfields[int(vars["iSortCol_%s" % str(i)])].field
                   for i in xrange(iSortingCols)]
        for i in xrange(len(columns)):
            c = columns[i]
            if not c:
                continue
            fieldtype = str(c.type)
            if fieldtype.startswith("reference") and \
               hasattr(c, "sortby") and c.sortby:
                tn = fieldtype[10:]
                if tn not in skip:
                    try:
                        join = [j for j in left if j.first._tablename == tn]
                    except:
                        # Old DAL version?
                        join = [j for j in left if j.table._tablename == tn]
                    if not join:
                        left.append(db[tn].on(c == db[tn].id))
                    else:
                        try:
                            join[0].query = (join[0].second) | \
                                            (c == db[tn].id)
                        except:
                            # Old DAL version?
                            join[0].query = (join[0].query) | \
                                            (c == db[tn].id)
                if not isinstance(c.sortby, (list, tuple)):
                    orderby.append("%s.%s%s" % (tn, c.sortby, direction(i)))
                else:
                    orderby.append(", ".join(["%s.%s%s" %
                                              (tn, fn, direction(i))
                                              for fn in c.sortby]))
            else:
                orderby.append("%s%s" % (c, direction(i)))

        return ", ".join(orderby)

# END =========================================================================

