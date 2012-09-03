# -*- coding: utf-8 -*-

""" S3 RESTful CRUD Methods

    @see: U{B{I{S3XRC}} <http://eden.sahanafoundation.org/wiki/S3XRC>}

    @requires: U{B{I{gluon}} <http://web2py.com>}
    @requires: U{B{I{lxml}} <http://codespeak.net/lxml>}

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

__all__ = ["S3CRUD", "S3ApproveRecords"]

from gluon import *
from gluon.dal import Row
from gluon.serializers import json as jsons
from gluon.storage import Storage
from gluon.tools import callback
try:
    import json # try stdlib (Python 2.6)
except ImportError:
    try:
        import simplejson as json # try external module
    except:
        import gluon.contrib.simplejson as json # fallback to pure-Python module

from s3method import S3Method
from s3export import S3Exporter
from s3forms import S3SQLDefaultForm
from s3widgets import S3EmbedComponentWidget
from s3utils import s3_unicode

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

        self.sqlform = self._config("crud_form",
                                    S3SQLDefaultForm())
        self.settings = current.response.s3.crud

        # Pre-populate create-form?
        self.data = None
        if r.http == "GET" and not self.record_id:
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
        elif self.method == "validate":
            output = self.validate(r, **attr)
        else:
            r.error(405, current.manager.ERROR.BAD_METHOD)

        return output

    # -------------------------------------------------------------------------
    def create(self, r, **attr):
        """
            Create new records

            @param r: the S3Request
            @param attr: dictionary of parameters for the method handler
        """

        session = current.session
        request = self.request
        response = current.response

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

            subheadings = _config("subheadings")

            # Get the form
            form = self.sqlform(request=request,
                                resource=self.resource,
                                data=self.data,
                                record_id=original,
                                from_table=from_table,
                                from_record=from_record,
                                map_fields=map_fields,
                                onvalidation=onvalidation,
                                onaccept=onaccept,
                                link=link,
                                message=message,
                                subheadings=subheadings,
                                format=representation)

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
                if r.component:
                    self.next = r.url(method="")
                else:
                    self.next = r.url(id="[id]", method="read")
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
                    session.error = current.T("Cannot read from file: %s" % infile)
                    redirect(r.url(method="", representation="html"))
            try:
                self.import_csv(infile, table=table)
            except:
                session.error = current.T("Unable to parse CSV file or file contains invalid data")
            else:
                session.confirmation = current.T("Data uploaded")

        elif representation == "pdf":
            from s3pdf import S3PDF
            exporter = S3PDF()
            return exporter(r, **attr)

        else:
            r.error(501, current.manager.ERROR.BAD_FORMAT)

        return output

    # -------------------------------------------------------------------------
    def read(self, r, **attr):
        """
            Read a single record

            @param r: the S3Request
            @param attr: dictionary of parameters for the method handler
        """

        # Check authorization to read the record
        authorised = self._permitted()
        if not authorised:
            r.unauthorised()

        session = current.session
        request = self.request
        response = current.response

        resource = self.resource
        table = resource.table
        tablename = resource.tablename

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
        record_id = self.record_id

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
                item = self.sqlform(request=request,
                                    resource=self.resource,
                                    record_id=record_id,
                                    readonly=True,
                                    subheadings=subheadings,
                                    format=representation)
            else:
                item = DIV(crud_string(tablename, "msg_list_empty"),
                           _class="empty")

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
                try:
                    output["modified_on"] = last_update["modified_on"]
                except:
                    # Field not in table
                    pass
                try:
                    output["modified_by"] = last_update["modified_by"]
                except:
                    # Field not in table, such as auth_user
                    pass

        elif representation == "plain":
            # Hide empty fields from popups on map
            for field in table:
                if field.readable:
                    value = resource._rows.records[0][tablename][field.name]
                    if value is None or value == "" or value == []:
                        field.readable = False

            # Form
            item = self.sqlform(request=request,
                                resource=self.resource,
                                record_id=record_id,
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
                    details_btn = A(current.T("Show Details"), _href=popup_url,
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
            exporter = resource.exporter.pdf
            return exporter(r, **attr)

        elif representation == "xls":
            list_fields = _config("list_fields")
            exporter = resource.exporter.xls
            return exporter(resource, list_fields=list_fields)

        elif representation == "json":
            exporter = S3Exporter()
            return exporter.json(resource)

        else:
            r.error(501, current.manager.ERROR.BAD_FORMAT)

        return output

    # -------------------------------------------------------------------------
    def update(self, r, **attr):
        """
            Update a record

            @param r: the S3Request
            @param attr: dictionary of parameters for the method handler
        """

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
        record_id = self.record_id
        if r.interactive and not record_id:
            r.error(404, resource.ERROR.BAD_RECORD)

        # Check if editable
        if not editable:
            if r.interactive:
                return self.read(r, **attr)
            else:
                r.error(405, resource.ERROR.BAD_METHOD)

        # Check permission for update
        authorised = self._permitted(method="update")
        if not authorised:
            r.unauthorised()

        if r.interactive or representation == "plain":

            response = current.response
            s3 = response.s3

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
                    if r.http == "POST":
                        r.post_vars.update({fkey: value})
                    field.readable = False
                    field.writable = False
                else:
                    link = Storage(resource=resource.link, master=r.record)

            # Success message
            message = crud_string(self.tablename, "msg_record_modified")

            # Get the form
            form = self.sqlform(request=self.request,
                                resource=self.resource,
                                record_id=record_id,
                                onvalidation=onvalidation,
                                onaccept=onaccept,
                                message=message,
                                link=link,
                                subheadings=subheadings,
                                format=representation)

            # Navigate-away confirmation
            if self.settings.navigate_away_confirm:
                s3.jquery_ready.append("S3EnableNavigateAwayConfirm()")

            # Put form into output
            output["form"] = form
            if representation == "plain":
                output["item"] = form
                output["title"] = ""

            # Add delete and list buttons
            buttons = self.insert_buttons(r, "delete",
                                          record_id=record_id)
            if buttons:
                output["buttons"] = buttons

            # Last update
            last_update = self.last_update()
            if last_update:
                try:
                    output["modified_on"] = last_update["modified_on"]
                except:
                    # Field not in table
                    pass
                try:
                    output["modified_by"] = last_update["modified_by"]
                except:
                    # Field not in table, such as auth_user
                    pass

            # Redirection
            update_next = _config("update_next")
            if representation in ("popup", "iframe", "plain"):
                self.next = None
            elif not update_next:
                if r.component:
                    self.next = r.url(method="")
                else:
                    self.next = r.url(id="[id]", method="read")
            else:
                try:
                    self.next = update_next(self)
                except TypeError:
                    self.next = update_next

        elif representation == "url":
            return self.import_url(r)

        else:
            r.error(501, current.manager.ERROR.BAD_FORMAT)

        return output

    # -------------------------------------------------------------------------
    def delete(self, r, **attr):
        """
            Delete record(s)

            @param r: the S3Request
            @param attr: dictionary of parameters for the method handler

            @todo: update for link table components
        """

        output = dict()

        # Get table-specific parameters
        config = self._config
        deletable = config("deletable", True)
        delete_next = config("delete_next", None)

        # Check if deletable
        if not deletable:
            r.error(403, current.manager.ERROR.NOT_PERMITTED,
                    next=r.url(method=""))

        # Get callback
        ondelete = config("ondelete")

        # Get the target record ID
        record_id = self.record_id

        # Check permission to delete
        authorised = self._permitted()
        if not authorised:
            r.unauthorised()

        elif r.interactive and r.http == "GET" and not record_id:
            # Provide a confirmation form and a record list
            form = FORM(TABLE(TR(
                        TD(self.settings.confirm_delete,
                           _style="color: red;"),
                        TD(INPUT(_type="submit", _value=current.T("Delete"),
                           _style="margin-left: 10px;")))))
            items = self.select(r, **attr).get("items", None)
            if isinstance(items, DIV):
                output.update(form=form)
            output.update(items=items)
            current.response.view = self._view(r, "delete.html")

        elif r.interactive and (r.http == "POST" or
                                r.http == "GET" and record_id):
            # Delete the records, notify success and redirect to the next view
            numrows = self.resource.delete(ondelete=ondelete,
                                           format=r.representation)
            if numrows > 1:
                message = "%s %s" % (numrows, current.T("records deleted"))
            elif numrows == 1:
                message = self.crud_string(self.tablename,
                                           "msg_record_deleted")
            else:
                r.error(404, current.manager.error, next=r.url(method=""))
            current.response.confirmation = message
            r.http = "DELETE" # must be set for immediate redirect
            self.next = delete_next or r.url(method="")

        elif r.http == "DELETE":
            # Delete the records and return a JSON message
            numrows = self.resource.delete(ondelete=ondelete,
                                           format=r.representation)
            if numrows > 1:
                message = "%s %s" % (numrows, current.T("records deleted"))
            elif numrows == 1:
                message = self.crud_string(self.tablename,
                                           "msg_record_deleted")
            else:
                r.error(404, current.manager.error, next=r.url(method=""))
            item = current.xml.json_message(message=message)
            current.response.view = "xml.html"
            output.update(item=item)

        else:
            r.error(405, current.manager.ERROR.BAD_METHOD)

        return output

    # -------------------------------------------------------------------------
    def select(self, r, **attr):
        """
            Get a list view of the requested resource

            @param r: the S3Request
            @param attr: dictionary of parameters for the method handler
        """

        from s3.s3utils import S3DataTable
        session = current.session
        response = current.response
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
        report_filename = _config("report_filename")
        report_formname = _config("report_formname")

        # Check permission to read in this table
        authorised = self._permitted()
        if not authorised:
            r.unauthorised()

        # Pagination
        vars = self.request.get_vars
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

        if not fields or \
           fields[0].name != table.fields[0]:
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
                session.s3.filter = vars
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
                    response.aadata = jsons(aadata)
                    s3.start = 0
                    s3.limit = limit

            # Title and subtitle
            if r.component:
                title = crud_string(r.tablename, "title_display")
            else:
                title = crud_string(self.tablename, "title_list")
            #subtitle = crud_string(self.tablename, "subtitle_list")
            output["title"] = title
            #output["subtitle"] = subtitle

            # Empty table - or just no match?
            if not items:
                if "deleted" in self.table:
                    available_records = current.db(self.table.deleted == False)
                else:
                    available_records = current.db(self.table._id > 0)
                #if available_records.count():
                # This is faster:
                if available_records.select(self.table._id,
                                            limitby=(0, 1)).first():
                    items = DIV(crud_string(self.tablename, "msg_no_match"),
                                _class="empty")
                else:
                    items = DIV(crud_string(self.tablename, "msg_list_empty"),
                                _class="empty")
                s3.no_formats = True
                if r.component and "showadd_btn" in output:
                    # Hide the list and show the form by default
                    del output["showadd_btn"]
                    #del output["subtitle"]
                    items = ""

            # Update output
            if not s3.datatable_ajax_source:
                s3.datatable_ajax_source = str(r.url(representation = "aaData"))
            attr = S3DataTable.getConfigData()
            items = S3DataTable.htmlConfig(items,
                                           "list",
                                           sortby, # order by
                                           "", # the filter string
                                           None, # the rfields
                                           **attr
                                           )
            output["items"] = items
            output["sortby"] = sortby

        elif representation == "aadata":

            left = []
            distinct = r.method == "search"

            # Get the master query for SSPag
            # FixMe: don't use session to store filters; also causes resource
            # filters to be discarded
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

            output = jsons(result)

        elif representation == "plain":
            if resource.count() == 1:
                # Provide the record
                # (used by Map's Layer Properties window)
                resource.load()
                r.record = resource.records().first()
                if r.record:
                    r.id = r.record.id
                    self.record_id = self._record_id(r)
                    if "update" in vars and \
                       self._permitted(method="update"):
                         items = self.update(r, **attr).get("form", None)
                    else:
                        items = self.sqlform(request=self.request,
                                             resource=self.resource,
                                             record_id=r.id,
                                             readonly=True,
                                             format=representation)
                else:
                    raise HTTP(404, body="Record not Found")
            else:
                items = resource.sqltable(fields=list_fields,
                                          as_list=True)
            items = S3DataTable.htmlConfig(items,
                                           "list",
                                           sortby,
                                           "", # the filter string
                                           None, # the rfields
                                           **S3DataTable.getConfigData()
                                           )
            response.view = "plain.html"
            return dict(item=items)

        elif representation == "csv":
            exporter = S3Exporter()
            return exporter.csv(resource)

        elif representation == "pdf":
            exporter = resource.exporter.pdf
            return exporter(r,
                            list_fields=list_fields,
                            report_hide_comments = report_hide_comments,
                            report_filename = report_filename,
                            report_formname = report_formname,
                            **attr)

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
            r.error(501, current.manager.ERROR.BAD_FORMAT)

        return output

    # -------------------------------------------------------------------------
    def validate(self, r, **attr):
        """
            Validate records (AJAX). This method reads a JSON object from
            the request body, validates it against the current resource,
            and returns a JSON object with either the validation errors or
            the text representations of the data.

            @param r: the S3Request
            @param attr: dictionary of parameters for the method handler

            Input JSON format:

            {"<fieldname>":"<value>", "<fieldname>":"<value>"}

            Output JSON format:

            {"<fieldname>": {"value":"<value>",
                             "text":"<representation>",
                             "_error":"<error message>"}}

            The input JSON can also be a list of multiple records. This
            will return a list of results accordingly. Note that "text"
            is not provided if there was a validation error, and vice
            versa.

            The record ID should always be present in the JSON to
            avoid false duplicate errors.

            Non-existent fields will return "invalid field" as _error.

            Representations will be URL-escaped and any markup stripped.

            The ?component=<alias> URL query can be used to specify a
            component of the current resource rather than the main table.

            This method does only accept .json format.
        """

        if r.representation != "json":
            r.error(501, current.manager.ERROR.BAD_FORMAT)

        output = Storage()
        resource = self.resource

        if "component" in r.get_vars:
            alias = r.get_vars["component"]
            if alias in resource.components:
                component = resource.components[alias]
            else:
                r.error(404, current.manager.ERROR.BAD_RESOURCE)
        else:
            component = resource

        source = r.body
        source.seek(0)

        try:
            data = json.load(source)
        except ValueError:
            r.error(501, current.manager.ERROR.BAD_SOURCE)

        if not isinstance(data, list):
            single = True
            data = [data]
        else:
            single = False

        table = component.table
        pkey = table._id.name

        manager = current.manager
        validate = manager.validate
        represent = manager.represent

        get_config = current.s3db.get_config
        tablename = component.tablename
        onvalidation = get_config(tablename, "onvalidation")
        update_onvalidation = get_config(tablename, "update_onvalidation",
                                         onvalidation)
        create_onvalidation = get_config(tablename, "create_onvalidation",
                                         onvalidation)

        output = []
        for record in data:

            has_errors = False

            # Retrieve the record ID
            if pkey in record:
                original = {pkey: record[pkey]}
            elif "_id" in record:
                original = {pkey: record["_id"]}
            else:
                original = None

            # Field validation
            fields = Storage()
            for fname in record:
                if fname in (pkey, "_id"):
                    continue
                error = None
                value = record[fname]
                validated = fields[fname] = Storage(value = value)
                if fname not in table.fields:
                    validated._error = "invalid field"
                    continue
                field = table[fname]
                try:
                    value, error = validate(table, original, fname, value)
                except AttributeError:
                    error = "invalid field"
                if error:
                    has_errors = True
                    validated._error = s3_unicode(error)
                else:
                    try:
                        text = represent(field,
                                         value = value,
                                         strip_markup = True,
                                         xml_escape = True)
                    except:
                        text = s3_unicode(value)
                    validated.text = text

            # Form validation (=onvalidation)
            if not has_errors:
                if original is not None:
                    onvalidation = update_onvalidation
                else:
                    onvalidation = create_onvalidation
                form = Storage(vars=Storage(record), errors=Storage())
                if onvalidation is not None:
                    callback(onvalidation, form, tablename=tablename)
                for fn in form.errors:
                    msg = s3_unicode(form.errors[fn])
                    if fn in fields:
                        validated = fields[fn]
                        has_errors = True
                        validated._error = msg
                        if "text" in validated:
                            del validated["text"]
                    else:
                        msg = "%s: %s" % (fn, msg)
                        if "_error" in fields:
                            fields["_error"] = "\n".join([msg,
                                                          fields["_error"]])
                        else:
                            fields["_error"] = msg

            output.append(fields)

        if single and len(output) == 1:
            output = output[0]

        return json.dumps(output)

    # -------------------------------------------------------------------------
    # Utility functions
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

        crud_strings = current.response.s3.crud_strings
        # CRUD strings for this table
        _crud_strings = crud_strings.get(tablename, crud_strings)
        return _crud_strings.get(name,
                                 # Default fallback
                                 crud_strings.get(name, None))

    # -------------------------------------------------------------------------
    def last_update(self):
        """
            Get the last update meta-data
        """

        output = dict()
        record_id = self.record_id
        if record_id:
            T = current.T
            table = self.table
            fields = []
            if "modified_on" in table.fields:
                fields.append(table.modified_on)
            if "modified_by" in table.fields:
                fields.append(table.modified_by)

            if fields:
                query = (table._id == record_id)
                record = current.db(query).select(limitby=(0, 1), *fields).first()

                # @todo: "on" and "by" particles are problematic in translations
                if "modified_by" in record:
                    if not record.modified_by:
                        modified_by = T("anonymous user")
                    else:
                        modified_by = table.modified_by.represent(record.modified_by)
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
    def insert_buttons(self, r, *buttons, **attr):
        """
            Insert resource action buttons

            @param r: the S3Request
            @param buttons: button names ("add", "edit", "delete", "list")
            @keyword record_id: the record ID
        """

        output = dict()

        tablename = self.tablename
        representation = r.representation

        record_id = attr.get("record_id", None)

        # Button labels
        crud_string = self.crud_string
        ADD = crud_string(tablename, "label_create_button")
        #EDIT = current.T("Edit")
        EDIT = current.messages.UPDATE
        DELETE = crud_string(tablename, "label_delete_button")
        LIST = crud_string(tablename, "label_list_button")

        # Button URLs
        url = r.url
        href_add = url(method="create", representation=representation)
        href_edit = url(method="update", representation=representation)
        href_delete = url(method="delete", representation=representation)
        href_list = url(method="")

        # Table CRUD configuration
        config = self._config
        insertable = config("insertable", True)
        editable = config("editable", True)
        deletable = config("deletable", True)

        # Add button
        if "add" in buttons:
            authorised = self._permitted(method="create")
            if authorised and href_add and insertable:
                add_btn = self.crud_button(ADD, _href=href_add, _id="add-btn")
                output["add_btn"] = add_btn

        # List button
        if "list" in buttons:
            if not r.component or r.multiple:
                list_btn = self.crud_button(LIST,
                                            _href=href_list, _id="list-btn")
                output["list_btn"] = list_btn

        if not record_id:
            return output

        # Edit button
        if "edit" in buttons:
            authorised = self._permitted(method="update")
            if authorised and href_edit and editable and r.method != "update":
                edit_btn = self.crud_button(EDIT, _href=href_edit,
                                            _id="edit-btn")
                output["edit_btn"] = edit_btn

        # Delete button
        if "delete" in buttons:
            authorised = self._permitted(method="delete")
            if authorised and href_delete and deletable:
                delete_btn = self.crud_button(DELETE, _href=href_delete,
                                              _id="delete-btn",
                                              _class="delete-btn")
                output["delete_btn"] = delete_btn

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

        link = dict(attr)
        link.update(label=str(label), url=url)
        if "_class" not in link:
            link.update(_class="action-btn")

        s3 = current.response.s3
        if s3.actions is None:
            s3.actions = [link]
        else:
            s3.actions.append(link)

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
           not ownership_required("update", table):
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
            if ownership_required("delete", table):
                # Check which records can be deleted
                query = auth.s3_accessible_query("delete", table)
                rows = current.db(query).select(table._id)
                restrict = []
                for row in rows:
                    row_id = row.get("id", None)
                    if row_id:
                        restrict.append(str(row_id))
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
        xml = current.xml

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
        s3db = current.s3db
        request = current.request
        T = current.T

        error_message = T("Could not create record.")
        get_config = lambda key, tablename=component: \
                            s3db.get_config(tablename, key, None)

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
                    s3db.update_super(table, dict(id=selected))
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
                        s3db.update_super(table, dict(id=selected))
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

        s3db = current.s3db

        prefix, name, table, tablename = r.target()
        permit = current.auth.s3_has_permission

        if authorised is None:
            authorised = permit("update", tablename)

        if authorised and update:
            linkto = s3db.get_config(tablename, "linkto_update", None)
        else:
            linkto = s3db.get_config(tablename, "linkto", None)

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

        if resource.linked is not None:
            skip = [resource.linked.tablename]
        else:
            skip = []
        parent = resource.parent
        fkey = resource.fkey

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
                if parent is not None and \
                   parent.tablename == tn and field.name != fkey:
                    alias = "%s_%s_%s" % (parent.prefix, "linked", parent.name)
                    ktable = db[tn].with_alias(alias)
                    ktable._id = ktable[ktable._id.name]
                    tn = alias
                else:
                    ktable = db[tn]
                if tn not in skip:
                    q = (field == ktable._id)
                    join = [j for j in left if j.first._tablename == tn]
                    if not join:
                        left.append(ktable.on(q))
                if isinstance(field.sortby, (list, tuple)):
                    flist.extend([ktable[f] for f in field.sortby
                                            if f in ktable.fields])
                else:
                    if field.sortby in ktable.fields:
                        flist.append(ktable[field.sortby])
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
        parent = resource.parent
        fkey = resource.fkey

        iSortingCols = int(vars["iSortingCols"])

        def direction(i):
            dir = vars["sSortDir_%s" % str(i)]
            return dir and " %s" % dir or ""

        orderby = []

        lfields, joins, ljoins, distinct = resource.resolve_selectors(fields)
        columns = [lfields[int(vars["iSortCol_%s" % str(i)])].field
                   for i in xrange(iSortingCols)]
        for i in xrange(len(columns)):
            field = columns[i]
            if not field:
                continue
            fieldtype = str(field.type)
            if fieldtype.startswith("reference") and \
               hasattr(field, "sortby") and field.sortby:
                tn = fieldtype[10:]
                if parent is not None and \
                   parent.tablename == tn and field.name != fkey:
                    alias = "%s_%s_%s" % (parent.prefix, "linked", parent.name)
                    ktable = db[tn].with_alias(alias)
                    ktable._id = ktable[ktable._id.name]
                    tn = alias
                else:
                    ktable = db[tn]
                if tn not in skip:
                    q = (field == ktable._id)
                    join = [j for j in left if j.first._tablename == tn]
                    if not join:
                        left.append(ktable.on(q))
                if not isinstance(field.sortby, (list, tuple)):
                    orderby.append("%s.%s%s" % (tn, field.sortby, direction(i)))
                else:
                    orderby.append(", ".join(["%s.%s%s" %
                                              (tn, fn, direction(i))
                                              for fn in field.sortby]))
            else:
                orderby.append("%s%s" % (field, direction(i)))

        return ", ".join(orderby)

# =============================================================================
class S3ApproveRecords(S3CRUD):
    """
        Method handler for record approval

        @status: work in progress
    """

    # -------------------------------------------------------------------------
    def apply_method(self, r, **attr):
        """
            Entry point for REST interface

            @param r: the S3Request
            @param attr: controller parameters for the request
        """

        if self.method == "approve":
            if r.record is None:
                output = self.select(r, **attr)
            else:
                output = self.approve(r, **attr)
        elif self.method == "reject":
            if r.record is None:
                output = self.select(r, **attr)
            else:
                output = self.approve(r, **attr)
        else:
            r.error(405, current.manager.ERROR.BAD_METHOD)
        return output

    # -------------------------------------------------------------------------
    def approve(self, r, **attr):
        """
            Approve an unapproved record

            @param r: the S3Request
            @param attr: controller parameters for the request
        """

        raise NotImplementedError

    # -------------------------------------------------------------------------
    def reject(self, r, **attr):
        """
            Reject an unapproved record

            @param r: the S3Request
            @param attr: controller parameters for the request
        """

        raise NotImplementedError

    # -------------------------------------------------------------------------
    def select(self, r, **attr):
        """
            List unapproved records

            @param r: the S3Request
            @param attr: controller parameters for the request
        """

        from s3.s3utils import S3DataTable
        session = current.session
        response = current.response
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

        # Check permission to read in this table
        authorised = self._permitted()
        if not authorised:
            r.unauthorised()

        # Pagination
        vars = self.request.get_vars
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

        # Only show unapproved records
        from s3resource import S3FieldSelector
        resource.add_filter(S3FieldSelector("approved_by") == None)

        if r.interactive:

            left = []

            # SSPag?
            if not s3.no_sspag:
                limit = 1
                session.s3.filter = vars
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

            # Page title
            if r.component:
                title = crud_string(r.tablename, "title_display")
            else:
                title = crud_string(self.tablename, "title_list")
            output["title"] = title

            # Empty table - or just no match?
            if not items:
                if "deleted" in self.table:
                    available_records = current.db(self.table.deleted == False)
                else:
                    available_records = current.db(self.table._id > 0)
                if available_records.select(self.table._id,
                                            limitby=(0, 1)).first():
                    items = DIV(crud_string(self.tablename, "msg_no_match"),
                                _class="empty")
                else:
                    items = DIV(crud_string(self.tablename, "msg_list_empty"),
                                _class="empty")
                s3.no_formats = True

            # Update output
            items = S3DataTable.htmlConfig(items,
                                           "list",
                                           sortby,
                                           "", # the filter string
                                           None, # the rfields
                                           **S3DataTable.getConfigData()
                                           )
            output["items"] = items
            output["sortby"] = sortby

        elif representation == "aadata":

            left = []
            distinct = r.method == "search"

            # Get the master query for SSPag
            # FixMe: don't use session to store filters; also causes resource
            # filters to be discarded
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

        else:
            r.error(501, current.manager.ERROR.BAD_FORMAT)

        self.action_button(current.T("Review"), r.url(id="[id]"))

        return output

# END =========================================================================
