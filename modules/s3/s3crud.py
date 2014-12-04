# -*- coding: utf-8 -*-

""" S3 RESTful CRUD Methods

    @see: U{B{I{S3XRC}} <http://eden.sahanafoundation.org/wiki/S3XRC>}

    @requires: U{B{I{gluon}} <http://web2py.com>}
    @requires: U{B{I{lxml}} <http://codespeak.net/lxml>}

    @copyright: 2009-2014 (c) Sahana Software Foundation
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

__all__ = ("S3CRUD",)

try:
    import json # try stdlib (Python 2.6)
except ImportError:
    try:
        import simplejson as json # try external module
    except:
        import gluon.contrib.simplejson as json # fallback to pure-Python module

try:
    from lxml import etree
except ImportError:
    import sys
    print >> sys.stderr, "ERROR: lxml module needed for XML handling"
    raise

from gluon import *
from gluon.languages import lazyT
from gluon.storage import Storage
from gluon.tools import callback

from s3export import S3Exporter
from s3forms import S3SQLDefaultForm
from s3rest import S3Method
from s3utils import s3_unicode, s3_validate, s3_represent_value, s3_set_extension
from s3widgets import S3EmbedComponentWidget, S3Selector, ICON

# Compact JSON encoding
SEPARATORS = (",", ":")

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

            @return: output object to send to the view
        """

        self.settings = current.response.s3.crud
        sqlform = self._config("crud_form")
        self.sqlform = sqlform if sqlform else S3SQLDefaultForm()

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

        method = self.method

        if r.http == "DELETE" or self.method == "delete":
            output = self.delete(r, **attr)
        elif method == "create":
            output = self.create(r, **attr)
        elif method == "read":
            output = self.read(r, **attr)
        elif method == "update":
            output = self.update(r, **attr)

        # Standard list view: list-type and hide-filter set by controller
        # (default: list_type="datatable", hide_filter=None)
        elif method == "list":
            output = self.select(r, **attr)

        # URL Methods to explicitly choose list-type and hide-filter in the URL
        elif method in ("datatable", "datatable_f"):
            _attr = Storage(attr)
            _attr["list_type"] = "datatable"
            if method == "datatable_f":
                self.hide_filter = False
            output = self.select(r, **_attr)
        elif method in ("datalist", "datalist_f"):
            _attr = Storage(attr)
            _attr["list_type"] = "datalist"
            if method == "datalist_f":
                self.hide_filter = False
            output = self.select(r, **_attr)

        elif method == "validate":
            output = self.validate(r, **attr)
        elif method == "review":
            if r.record:
                output = self.review(r, **attr)
            else:
                output = self.unapproved(r, **attr)
        else:
            r.error(405, current.ERROR.BAD_METHOD)

        return output

    # -------------------------------------------------------------------------
    def widget(self, r, method=None, widget_id=None, visible=True, **attr):
        """
            Entry point for other method handlers to embed this
            method as widget

            @param r: the S3Request
            @param method: the widget method
            @param widget_id: the widget ID
            @param visible: whether the widget is initially visible
            @param attr: controller attributes
        """

        # Settings
        self.settings = current.response.s3.crud
        sqlform = self._config("crud_form")
        self.sqlform = sqlform if sqlform else S3SQLDefaultForm()

        _attr = Storage(attr)
        _attr["list_id"] = widget_id

        if method == "datatable":
            output = self._datatable(r, **_attr)
            if isinstance(output, dict):
                output = DIV(output["items"], _id="table-container")
            return output
        elif method == "datalist":
            output = self._datalist(r, **_attr)
            if isinstance(output, dict) and "items" in output:
                output = DIV(output["items"], _id="list-container")
            return output
        elif method == "create":
            return self._widget_create(r, **_attr)
        else:
            return None

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

        native = r.method == "create"

        # Get table configuration
        _config = self._config
        insertable = _config("insertable", True)
        if not insertable:
            if native:
                r.error(405, current.ERROR.METHOD_DISABLED)
            else:
                return dict(form=None)

        authorised = self._permitted(method="create")
        if not authorised:
            if native:
                r.unauthorised()
            else:
                return dict(form=None)

        # Get callbacks
        onvalidation = _config("create_onvalidation") or \
                       _config("onvalidation")
        onaccept = _config("create_onaccept") or \
                   _config("onaccept")

        if r.interactive:

            crud_string = self.crud_string

            # Page details
            if native:

                # Set view
                if representation in ("popup", "iframe"):
                    response.view = self._view(r, "popup.html")
                    output["caller"] = request.vars.caller
                else:
                    response.view = self._view(r, "create.html")

                # Title
                if r.component:
                    title = crud_string(r.tablename, "title_display")
                    output["title"] = title
                else:
                    title = crud_string(tablename, "label_create")
                    output["title"] = title
                output["title_list"] = crud_string(tablename, "title_list")

                # Buttons
                buttons = self.render_buttons(r, ["list"], **attr)
                if buttons:
                    output["buttons"] = buttons

            # Component join
            link = None
            if r.component:
                if resource.link is None:
                    # No link table - direct component
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

            get_vars = r.get_vars

            # Hierarchy parent
            hierarchy = None
            link_to_parent = get_vars.get("link_to_parent")
            if link_to_parent:
                try:
                    parent = long(link_to_parent)
                except ValueError:
                    r.error(400, "Invalid parent record ID: %s" % link_to_parent)
                else:
                    from s3hierarchy import S3Hierarchy
                    h = S3Hierarchy(tablename)
                    if h.config:
                        try:
                            hierarchy = h.preprocess_create_node(r, parent)
                        except KeyError:
                            import sys
                            r.error(404, sys.exc_info()[1])

            # Copy record
            from_table = None
            from_record = get_vars.get("from_record")
            map_fields = get_vars.get("from_fields")

            if from_record:
                del get_vars["from_record"] # forget it
                if from_record.find(".") != -1:
                    from_table, from_record = from_record.split(".", 1)
                    from_table = current.db.get(from_table, None)
                    if not from_table:
                        r.error(404, current.ERROR.BAD_RESOURCE)
                else:
                    from_table = table
                try:
                    from_record = long(from_record)
                except:
                    r.error(404, current.ERROR.BAD_RECORD)
                authorised = current.auth.s3_has_permission("read",
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
                post_vars = request.post_vars
                original = str(post_vars.id)
                formkey = session.get("_formkey[%s/None]" % tablename)
                formname = "%s/%s" % (tablename, original)
                session["_formkey[%s]" % formname] = formkey
                if "deleted" in table:
                    table.deleted.writable = True
                    post_vars["deleted"] = False
                if "created_on" in table:
                    table.created_on.writable = True
                    post_vars["created_on"] = request.utcnow
                if "created_by" in table:
                    table.created_by.writable = True
                    if current.auth.user:
                        post_vars["created_by"] = current.auth.user.id
                    else:
                        post_vars["created_by"] = None
                post_vars["_formname"] = formname
                post_vars["id"] = original
                request.vars.update(**post_vars)
            else:
                original = None

            subheadings = _config("subheadings")

            # Interim save button
            self._interim_save_button()

            # Default Cancel Button
            if r.representation == "html" and r.method == "create":
                self._default_cancel_button(r)

            # Get the form
            output["form"] = self.sqlform(request=request,
                                          resource=resource,
                                          data=self.data,
                                          record_id=original,
                                          from_table=from_table,
                                          from_record=from_record,
                                          map_fields=map_fields,
                                          onvalidation=onvalidation,
                                          onaccept=onaccept,
                                          link=link,
                                          hierarchy=hierarchy,
                                          message=message,
                                          subheadings=subheadings,
                                          format=representation)

            # Navigate-away confirmation
            if self.settings.navigate_away_confirm:
                response.s3.jquery_ready.append("S3EnableNavigateAwayConfirm()")

            # Redirection
            if representation in ("popup", "iframe", "plain", "dl"):
                self.next = None
            else:
                if r.http == "POST" and "interim_save" in r.post_vars:
                    next_vars = self._remove_filters(r.get_vars)
                    create_next = r.url(target="[id]", method="update",
                                        vars=next_vars)
                elif r.http == "POST" and "save_close" in r.post_vars:
                    create_next = _config("create_next_close")
                elif session.s3.rapid_data_entry and not r.component:
                    create_next = r.url()
                else:
                    create_next = _config("create_next")

                if not create_next:
                    next_vars = self._remove_filters(r.get_vars)
                    if r.component:
                        self.next = r.url(method="",
                                          vars=next_vars)
                    else:
                        self.next = r.url(id="[id]",
                                          method="read",
                                          vars=next_vars)
                elif callable(create_next):
                    self.next = create_next(r)
                else:
                    self.next = create_next

        elif representation == "plain":
            # NB formstyle will be "table3cols" so widgets need to support that
            #    or else we need to be able to override this
            response.view = self._view(r, "plain.html")
            crud_string = self.crud_string
            message = crud_string(tablename, "msg_record_created")
            subheadings = _config("subheadings")
            output["title"] = crud_string(tablename, "label_create")
            output["details_btn"] = ""
            output["item"] = self.sqlform(request=request,
                                          resource=resource,
                                          data=self.data,
                                          onvalidation=onvalidation,
                                          onaccept=onaccept,
                                          #link=link,
                                          message=message,
                                          subheadings=subheadings,
                                          format=representation)

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
                    session.error = current.T("Cannot read from file: %(filename)s") % \
                                                dict(filename=infile)
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

        elif representation == "url":
            results = self.import_url(r)
            return results

        else:
            r.error(501, current.ERROR.BAD_FORMAT)

        return output

    # -------------------------------------------------------------------------
    def _widget_create(self, r, **attr):
        """
            Create-buttons/form in summary views, both GET and POST

            @param r: the S3Request
            @param attr: dictionary of parameters for the method handler
        """

        response = current.response

        resource = self.resource
        get_config = resource.get_config
        tablename = resource.tablename

        output = {}
        insertable = get_config("insertable", True)
        if insertable:

            listadd = get_config("listadd", True)
            addbtn = get_config("addbtn", False)

            if listadd:
                # Hidden form + Add-button to activate it
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

                view = response.view

                # JS Cancel (no redirect with embedded form)
                s3 = response.s3
                cancel = s3.cancel
                s3.cancel = {"hide": "list-add", "show": "show-add-btn"}

                form = self.create(r, **attr).get("form", None)
                if form and form.accepted and self.next:
                    # Tell the summary handler that we're done
                    # and supposed to redirect to another view
                    return {"success": True, "next": self.next}

                # Restore standard view and cancel-config
                response.view = view
                s3.cancel = cancel

                if form is not None:
                    output["form"] = form
                    output["showadd_btn"] = self.crud_button(tablename=tablename,
                                                             name="label_create",
                                                             icon="add",
                                                             _id="show-add-btn")
                    addtitle = self.crud_string(tablename, "label_create")
                    output["addtitle"] = addtitle
                    if r.http == "POST":
                        # Always show the form if there was a form error
                        script = '''$('#list-add').show();$('#show-add-btn').hide()'''
                        s3.jquery_ready.append(script)

                    # Add-button script
                    # - now in S3.js
                    #script = '''$('#show-add-btn').click(function(){$('#show-add-btn').hide(10, function(){$('#list-add').slideDown('medium')})})'''
                    #s3.jquery_ready.append(script)

            elif addbtn:
                # No form, just Add-button linked to create-view
                add_btn = self.crud_button(
                                    tablename=tablename,
                                    name="label_create",
                                    icon="add",
                                    _id="add-btn")
                if buttons:
                    output["buttons"] = {"add_btn": add_btn}

        view = self._view(r, "listadd.html")
        output = XML(response.render(view, output))
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

        request = self.request
        response = current.response

        resource = self.resource
        table = resource.table
        tablename = resource.tablename

        representation = r.representation

        output = dict()

        _config = self._config
        editable = _config("editable", True)
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
                    # This should become Native
                    r.method = "create"
                    return self.create(r, **attr)
                else:
                    return self.select(r, **attr)

            # Redirect to update if user has permission unless
            # a method has been specified in the URL
            # MH: Is this really desirable? Many users would prefer to open as read
            if not r.method or r.method == "review":
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
            output["title_list"] = crud_string(tablename, "title_list")

            # Item
            if record_id:
                item = self.sqlform(request=request,
                                    resource=resource,
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
            elif representation == "popup":
                response.view = self._view(r, "popup.html")
                output["form"] = item
                caller = attr.get("caller", None)
                output["caller"] = caller
            elif representation == "iframe":
                response.view = self._view(r, "iframe.html")
                output["form"] = item

            # Buttons
            buttons = self.render_buttons(r,
                                          ["edit", "delete", "list", "summary"],
                                          record_id=record_id,
                                          **attr)
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

            # De-duplication
            from s3merge import S3Merge
            output["deduplicate"] = S3Merge.bookmark(r, tablename, record_id)

        elif representation == "plain":
            T = current.T
            fields = [f for f in table if f.readable]
            if r.component:
                if record_id:
                    record = current.db(table._id == record_id).select(limitby=(0, 1),
                                                                       *fields
                                                                       ).first()
                else:
                    record = None
            else:
                record = r.record
            if record:
                # Hide empty fields from popups on map
                for field in fields:
                    try:
                        value = record[field]
                    except:
                        # e.g. gis_location.wkt
                        value = None
                    if value is None or value == "" or value == []:
                        field.readable = False
                item = self.sqlform(request=request,
                                    resource=resource,
                                    record_id=record_id,
                                    readonly=True,
                                    format=representation)

                # Link to Open record
                popup_edit_url = _config("popup_edit_url", None)
                if popup_edit_url and \
                   current.auth.s3_has_permission("update", table, record_id):
                    # Open edit form in iframe
                    details_btn = A(T("Edit"),
                                    _href=popup_edit_url,
                                    _class="btn iframe",
                                    )
                    output["details_btn"] = details_btn
                else:
                    # Open read view in new tab
                    # Set popup_url to "" to have no button present
                    popup_url = _config("popup_url", None)
                    if popup_url is None:
                        popup_url = r.url(method="read", representation="html")
                    if popup_url:
                        details_btn = A(T("Open"),
                                        _href=popup_url,
                                        _class="btn",
                                        _target="_blank",
                                        )
                        output["details_btn"] = details_btn

                # Title and subtitle
                title = self.crud_string(r.tablename, "title_display")
                output["title"] = title

            else:
                item = T("Record not found")

            output["item"] = item
            response.view = self._view(r, "plain.html")

        elif representation == "csv":
            exporter = S3Exporter().csv
            return exporter(resource)

        #elif representation == "map":
        #    exporter = S3Map()
        #    return exporter(r, **attr)

        elif representation == "pdf":
            exporter = S3Exporter().pdf
            return exporter(resource, request=r, **attr)

        elif representation == "shp":
            exporter = S3Exporter().shp
            return exporter(resource,
                            list_fields=list_fields,
                            **attr)

        elif representation == "svg":
            exporter = S3Exporter().svg
            return exporter(resource,
                            list_fields=list_fields,
                            **attr)

        elif representation == "xls":
            list_fields = _config("list_fields")
            exporter = S3Exporter().xls
            return exporter(resource, list_fields=list_fields)

        elif representation == "json":
            exporter = S3Exporter().json

            # Render extra "_tooltip" field for each row?
            get_vars = request.get_vars
            if "tooltip" in get_vars:
                tooltip = get_vars["tooltip"]
            else:
                tooltip = None

            return exporter(resource, tooltip=tooltip)

        else:
            r.error(501, current.ERROR.BAD_FORMAT)

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

        # Get callbacks
        onvalidation = _config("update_onvalidation") or \
                       _config("onvalidation")
        onaccept = _config("update_onaccept") or \
                   _config("onaccept")

        # Get the target record ID
        record_id = self.record_id
        if r.interactive and not record_id:
            r.error(404, current.ERROR.BAD_RECORD)

        # Check if editable
        if not editable:
            if r.interactive:
                return self.read(r, **attr)
            else:
                r.error(405, current.ERROR.METHOD_DISABLED)

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
            elif representation in "popup":
                response.view = self._view(r, "popup.html")
            elif representation == "plain":
                response.view = self._view(r, "plain.html")
            elif representation == "iframe":
                response.view = self._view(r, "iframe.html")

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
            output["title_list"] = crud_string(tablename, "title_list")

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

            # Interim save button
            self._interim_save_button()

            # Default Cancel Button
            if r.representation == "html" and \
               (r.method == "update" or not r.method):
                self._default_cancel_button(r)

            # Get the form
            form = self.sqlform(request=self.request,
                                resource=resource,
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
            buttons = self.render_buttons(r,
                                          ["delete"],
                                          record_id=record_id,
                                          **attr)
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

            # De-duplication
            from s3merge import S3Merge
            output["deduplicate"] = S3Merge.bookmark(r, tablename, record_id)

            # Redirection
            if r.http == "POST" and "interim_save" in r.post_vars:
                next_vars = self._remove_filters(r.get_vars)
                self.next = r.url(target="[id]", method="update",
                                  vars=next_vars)
            else:
                update_next = _config("update_next")
                if representation in ("popup", "iframe", "plain", "dl"):
                    self.next = None
                elif not update_next:
                    next_vars = self._remove_filters(r.get_vars)
                    if r.component:
                        self.next = r.url(method="", vars=next_vars)
                    else:
                        self.next = r.url(id="[id]",
                                          method="read",
                                          vars=next_vars)
                else:
                    try:
                        self.next = update_next(self)
                    except TypeError:
                        self.next = update_next

        elif representation == "url":
            return self.import_url(r)

        else:
            r.error(501, current.ERROR.BAD_FORMAT)

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
            r.error(403, current.ERROR.NOT_PERMITTED,
                    next=r.url(method=""))

        # Get the target record ID
        record_id = self.record_id

        # Check permission to delete
        authorised = self._permitted()
        if not authorised:
            r.unauthorised()

        elif (r.interactive or r.representation == "aadata") and \
             r.http == "GET" and not record_id:
            output = self._datatable(r, **attr)
            if isinstance(output, dict):
                # Provide a confirmation form and a record list
                form = FORM(TABLE(TR(TD(self.settings.confirm_delete,
                                        _style="color:red"),
                                     TD(INPUT(_type="submit",
                                              _value=current.T("Delete"),
                                              _style="margin-left:10px")))))
                output["form"] = form
                current.response.view = self._view(r, "delete.html")
            else:
                # @todo: sorting not working yet
                return output

        elif r.interactive and (r.http == "POST" or
                                r.http == "GET" and record_id):
            # Delete the records, notify success and redirect to the next view
            numrows = self.resource.delete(format=r.representation)
            if numrows > 1:
                message = "%s %s" % (numrows, current.T("records deleted"))
            elif numrows == 1:
                message = self.crud_string(self.tablename,
                                           "msg_record_deleted")
            else:
                r.error(404, self.resource.error, next=r.url(method=""))
            current.response.confirmation = message
            r.http = "DELETE" # must be set for immediate redirect
            self.next = delete_next or r.url(method="")

        elif r.http == "DELETE" or \
             r.representation == "json" and r.http == "POST" and record_id:
            # Delete the records and return a JSON message
            numrows = self.resource.delete(format=r.representation)
            if numrows > 1:
                message = "%s %s" % (numrows, current.T("records deleted"))
            elif numrows == 1:
                message = self.crud_string(self.tablename,
                                           "msg_record_deleted")
            else:
                r.error(404, self.resource.error, next=r.url(method=""))
            item = current.xml.json_message(message=message)
            current.response.view = "xml.html"
            output.update(item=item)

        else:
            r.error(405, current.ERROR.BAD_METHOD)

        return output

    # -------------------------------------------------------------------------
    def select(self, r, **attr):
        """
            Filtered datatable/datalist

            @param r: the S3Request
            @param attr: dictionary of parameters for the method handler
        """

        resource = self.resource

        tablename = resource.tablename
        get_config = resource.get_config

        list_fields = get_config("list_fields", None)

        representation = r.representation
        if representation in ("html", "iframe", "aadata", "dl", "popup"):

            hide_filter = self.hide_filter
            filter_widgets = get_config("filter_widgets", None)

            show_filter_form = False
            if filter_widgets and not hide_filter and \
               representation not in ("aadata", "dl"):
                show_filter_form = True
                # Apply filter defaults (before rendering the data!)
                from s3filter import S3FilterForm
                S3FilterForm.apply_filter_defaults(r, resource)

            # Data
            list_type = attr.get("list_type", "datatable")
            if list_type == "datalist":
                filter_ajax = True
                target = "datalist"
                output = self._datalist(r, **attr)
            else:
                # Hide datatable filter box if we have a filter form
                if filter_widgets and not hide_filter:
                    dtargs = attr.get("dtargs", {})
                    if "dt_searching" not in dtargs:
                        dtargs["dt_searching"] = False
                    _attr = dict(attr)
                    _attr["dtargs"] = dtargs
                else:
                    _attr = attr
                filter_ajax = True
                target = "datatable"
                output = self._datatable(r, **_attr)

            if representation in ("aadata", "dl"):
                return output

            output["list_type"] = list_type

            crud_string = self.crud_string

            # Page title
            if representation != "iframe":
                if r.component:
                    title = crud_string(r.tablename, "title_display")
                else:
                    title = crud_string(self.tablename, "title_list")
                output["title"] = title

            # Filter-form
            if show_filter_form:

                # Where to retrieve filtered data from:
                filter_submit_url = attr.get("filter_submit_url")
                if not filter_submit_url:
                    _vars = self._remove_filters(r.get_vars)
                    filter_submit_url = r.url(vars=_vars)

                # Where to retrieve updated filter options from:
                filter_ajax_url = attr.get("filter_ajax_url",
                                           r.url(method="filter",
                                                 vars={},
                                                 representation="options"))

                filter_clear = get_config("filter_clear",
                                          current.deployment_settings.get_ui_filter_clear())
                filter_formstyle = get_config("filter_formstyle", None)
                filter_submit = get_config("filter_submit", True)
                filter_form = S3FilterForm(filter_widgets,
                                           clear=filter_clear,
                                           formstyle=filter_formstyle,
                                           submit=filter_submit,
                                           ajax=filter_ajax,
                                           url=filter_submit_url,
                                           ajaxurl=filter_ajax_url,
                                           _class="filter-form",
                                           _id="%s-filter-form" % target
                                           )
                fresource = current.s3db.resource(resource.tablename)
                alias = resource.alias if r.component else None
                output["list_filter_form"] = filter_form.html(fresource,
                                                              r.get_vars,
                                                              target=target,
                                                              alias=alias
                                                              )
            else:
                # Render as empty string to avoid the exception in the view
                output["list_filter_form"] = ""

            # Add-form or -button
            insertable = get_config("insertable", True)
            if insertable:

                addbtn = get_config("addbtn", False)
                listadd = get_config("listadd", True)

                if listadd:
                    # Save the view
                    response = current.response
                    view = response.view

                    # JS Cancel (no redirect with embedded form)
                    s3 = response.s3
                    cancel = s3.cancel
                    s3.cancel = {"hide": "list-add", "show": "show-add-btn"}

                    # Add a hidden add-form and a button to activate it
                    form = self.create(r, **attr).get("form", None)
                    if form is not None:
                        output["form"] = form
                        addtitle = self.crud_string(tablename, "label_create")
                        output["addtitle"] = addtitle
                        showadd_btn = self.crud_button(None,
                                                       tablename=tablename,
                                                       name="label_create",
                                                       icon="add",
                                                       _id="show-add-btn")
                        output["showadd_btn"] = showadd_btn

                    # Restore the view
                    response.view = view
                    s3.cancel = cancel

                elif addbtn:
                    # Add an action-button linked to the create view
                    buttons = self.render_buttons(r, ["add"], **attr)
                    if buttons:
                        output["buttons"] = buttons

            return output

        elif representation == "plain":

            if resource.count() == 1:
                # Provide the record
                # (used by Map's Layer Properties window)
                resource.load()
                r.record = resource.records().first()
                if r.record:
                    r.id = r.record.id
                    self.record_id = self._record_id(r)
                    if "update" in r.get_vars and \
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
                rows = resource.select(list_fields,
                                       limit=None,
                                       as_rows=True)
                if rows:
                    items = rows.as_list()
                else:
                    items = []

            current.response.view = "plain.html"
            return dict(item=items)

        elif representation == "csv":

            exporter = S3Exporter().csv
            return exporter(resource)

        elif representation == "json":

            get_vars = self.request.get_vars

            # Start/limit
            start, limit = self._limits(get_vars)

            # Render extra "_tooltip" field for each row?
            if "tooltip" in get_vars:
                tooltip = get_vars["tooltip"]
            else:
                tooltip = None

            fields = resource.list_fields(id_column=True)
            rfields = resource.resolve_selectors(fields,
                                                 extra_fields=False)[0]
            fields = [rfield.fname for rfield in rfields
                                   if rfield.tname == tablename]
            orderby = get_config("orderby", None)

            exporter = S3Exporter().json
            return exporter(resource,
                            start=start,
                            limit=limit,
                            fields=fields,
                            orderby=orderby,
                            tooltip=tooltip)

        elif representation == "pdf":

            report_hide_comments = get_config("report_hide_comments", None)
            report_filename = get_config("report_filename", None)
            report_formname = get_config("report_formname", None)

            exporter = S3Exporter().pdf
            return exporter(resource,
                            request=r,
                            list_fields=list_fields,
                            report_hide_comments = report_hide_comments,
                            report_filename = report_filename,
                            report_formname = report_formname,
                            **attr)

        elif representation == "shp":
            exporter = S3Exporter().shp
            return exporter(resource,
                            list_fields=list_fields,
                            **attr)

        elif representation == "svg":
            exporter = S3Exporter().svg
            return exporter(resource,
                            list_fields=list_fields,
                            **attr)

        elif representation == "xls":
            report_groupby = get_config("report_groupby", None)
            exporter = S3Exporter().xls
            return exporter(resource,
                            list_fields=list_fields,
                            report_groupby=report_groupby,
                            **attr)

        elif representation == "msg":
            if r.http == "POST":
                from s3notify import S3Notifications
                return S3Notifications.send(r, resource)
            else:
                r.error(405, current.ERROR.BAD_METHOD)

        else:
            r.error(501, current.ERROR.BAD_FORMAT)

    # -------------------------------------------------------------------------
    def _datatable(self, r, **attr):
        """
            Get a data table

            @param r: the S3Request
            @param attr: parameters for the method handler
        """

        # Check permission to read in this table
        authorised = self._permitted()
        if not authorised:
            r.unauthorised()

        resource = self.resource
        get_config = resource.get_config

        # Get table-specific parameters
        linkto = get_config("linkto", None)

        # List ID
        list_id = attr.get("list_id", "datatable")

        # List fields
        list_fields = resource.list_fields()

        # Default orderby
        orderby = get_config("orderby", None)

        response = current.response
        s3 = response.s3
        representation = r.representation

        # Pagination
        get_vars = self.request.get_vars
        if representation == "aadata":
            start, limit = self._limits(get_vars)
        else:
            # Initial page request always uses defaults (otherwise
            # filtering and pagination would have to be relative to
            # the initial limits, but there is no use-case for that)
            start = None
            limit = None if s3.no_sspag else 0

        # Initialize output
        output = {}

        # Filter
        if s3.filter is not None:
            resource.add_filter(s3.filter)

        # Linkto
        if not linkto:
            linkto = self._linkto(r)

        left = []
        distinct = False
        dtargs = attr.get("dtargs", {})

        if r.interactive:

            # How many records per page?
            if s3.dataTable_pageLength:
                display_length = s3.dataTable_pageLength
            else:
                display_length = 25

            # Server-side pagination?
            if not s3.no_sspag:
                dt_pagination = "true"
                if not limit:
                    limit = 2 * display_length
                current.session.s3.filter = get_vars
                if orderby is None:
                    dt_sorting = {"iSortingCols": "1",
                                  "sSortDir_0": "asc"
                                  }

                    if len(list_fields) > 1:
                        dt_sorting["bSortable_0"] = "false"
                        dt_sorting["iSortCol_0"] = "1"
                    else:
                        dt_sorting["bSortable_0"] = "true"
                        dt_sorting["iSortCol_0"] = "0"

                    q, orderby, left = resource.datatable_filter(list_fields,
                                                                 dt_sorting)
            else:
                dt_pagination = "false"

            # Get the data table
            dt, totalrows, ids = resource.datatable(fields=list_fields,
                                                    start=start,
                                                    limit=limit,
                                                    left=left,
                                                    orderby=orderby,
                                                    distinct=distinct)
            displayrows = totalrows

            if not dt.data:
                # Empty table - or just no match?
                #if dt.empty:
                #    datatable = DIV(self.crud_string(resource.tablename,
                #                                     "msg_list_empty"),
                #                    _class="empty")
                #else:
                #    #datatable = DIV(self.crud_string(resource.tablename,
                #                                      "msg_no_match"),
                #                     _class="empty")
                s3.no_formats = True

                if r.component and "showadd_btn" in output:
                    # Hide the list and show the form by default
                    del output["showadd_btn"]
                    datatable = ""
            #else:

            # Always show table, otherwise it can't be Ajax-filtered
            # @todo: need a better algorithm to determine total_rows
            #        (which excludes URL filters), so that datatables
            #        shows the right empty-message (ZeroRecords instead
            #        of EmptyTable)
            dtargs["dt_pagination"] = dt_pagination
            dtargs["dt_pageLength"] = display_length
            dtargs["dt_base_url"] = r.url(method="", vars={})
            dtargs["dt_permalink"] = r.url()
            datatable = dt.html(totalrows,
                                displayrows,
                                id=list_id,
                                **dtargs)

            # View + data
            response.view = self._view(r, "list_filter.html")
            output["items"] = datatable

        elif representation == "aadata":

            # Apply datatable filters
            searchq, orderby, left = resource.datatable_filter(list_fields,
                                                               get_vars)
            if searchq is not None:
                totalrows = resource.count()
                resource.add_filter(searchq)
            else:
                totalrows = None

            # Orderby fallbacks
            if orderby is None:
                orderby = get_config("orderby", None)

            # Get a data table
            if totalrows != 0:
                dt, displayrows, ids = resource.datatable(fields=list_fields,
                                                          start=start,
                                                          limit=limit,
                                                          left=left,
                                                          orderby=orderby,
                                                          distinct=distinct,
                                                          getids=False)
            else:
                dt, displayrows = None, 0
            if totalrows is None:
                totalrows = displayrows

            # Echo
            draw = int(get_vars.draw or 0)

            # Representation
            if dt is not None:
                output = dt.json(totalrows,
                                 displayrows,
                                 list_id,
                                 draw,
                                 **dtargs)
            else:
                output = '{"recordsTotal":%s,' \
                         '"recordsFiltered":0,' \
                         '"dataTable_id":"%s",' \
                         '"draw":%s,' \
                         '"data":[]}' % (totalrows, list_id, draw)

        else:
            r.error(501, current.ERROR.BAD_FORMAT)

        return output

    # -------------------------------------------------------------------------
    def _datalist(self, r, **attr):
        """
            Get a data list

            @param r: the S3Request
            @param attr: parameters for the method handler
        """

        # Check permission to read in this table
        authorised = self._permitted()
        if not authorised:
            r.unauthorised()

        resource = self.resource
        get_config = resource.get_config
        get_vars = self.request.get_vars

        # Get table-specific parameters
        layout = get_config("list_layout", None)

        # List ID
        list_id = get_vars.get("list_id",
                               attr.get("list_id", "datalist"))

        # List fields
        list_fields = resource.list_fields()

        # Default orderby
        orderby = get_config("list_orderby",
                             get_config("orderby", None))
        if orderby is None:
            if "created_on" in resource.fields:
                default_orderby = ~(resource.table["created_on"])
            else:
                for f in list_fields:
                    rfield = resource.resolve_selector(f)
                    if rfield.field and rfield.colname != str(resource._id):
                        default_orderby = rfield.field
                        break
        else:
            default_orderby = None

        # Pagination
        response = current.response
        s3 = response.s3

        # Pagelength = number of items per page
        if "dl_pagelength" in attr:
            pagelength = attr["dl_pagelength"]
        elif s3.dl_pagelength:
            pagelength = s3.dl_pagelength
        else:
            pagelength = 10

        # Rowsize = number of items per row
        if "dl_rowsize" in attr:
            rowsize = attr["dl_rowsize"]
        elif s3.dl_rowsize:
            rowsize = s3.dl_rowsize
        else:
            rowsize = 1

        # Make sure that pagelength is a multiple of rowsize
        if pagelength % rowsize:
            pagelength = (int(pagelength / rowsize) + 1) * rowsize

        record_id = get_vars.get("record", None)
        if record_id is not None:
            # Ajax-reload of a single record
            from s3query import FS
            resource.add_filter(FS("id") == record_id)
            start = 0
            limit = 1
        else:
            start, limit = self._limits(get_vars)

        # Initialize output
        output = {}

        # Filter
        if s3.filter is not None:
            resource.add_filter(s3.filter)

        # Prepare data list
        representation = r.representation

        # Ajax-delete items?
        if representation == "dl" and r.http in ("DELETE", "POST"):
            if "delete" in get_vars:
                return {"item": self._dl_ajax_delete(r, resource)}
            else:
                r.error(405, current.ERROR.BAD_METHOD)

        if representation in ("html", "dl", "popup"):

            # Retrieve the data
            if limit:
                initial_limit = min(limit, pagelength)
            else:
                initial_limit = pagelength

            # We don't have client-side sorting yet to override
            # default-orderby, so fall back unconditionally here:
            if not orderby:
                orderby = default_orderby

            datalist, numrows, ids = resource.datalist(fields=list_fields,
                                                       start=start,
                                                       limit=initial_limit,
                                                       orderby=orderby,
                                                       list_id=list_id,
                                                       layout=layout)

            if numrows == 0:
                # Empty table or just no match?

                #table = resource.table
                #if "deleted" in table:
                #    available_records = current.db(table.deleted != True)
                #else:
                #    available_records = current.db(table._id > 0)
                #if available_records.select(table._id,
                #                            limitby=(0, 1)).first():
                #    empty = self.crud_string(resource.tablename,
                #                             "msg_no_match")
                #else:
                #    empty = self.crud_string(resource.tablename,
                #                             "msg_list_empty")

                s3.no_formats = True
                if r.component and "showadd_btn" in output:
                    # Hide the list and show the form by default
                    del output["showadd_btn"]
                    #empty = ""
            #else:
            #    empty = None

            # Allow customization of the datalist Ajax-URL
            # Note: the Ajax-URL must use the .dl representation and
            # plain.html view for pagination to work properly!
            ajax_url = attr.get("list_ajaxurl", None)
            if not ajax_url:
                vars = dict((k,v) for k, v in r.get_vars.iteritems()
                                  if k not in ("start", "limit"))
                ajax_url = r.url(representation="dl", vars=vars)

            # Render the list (even if empty => Ajax-section is required
            # in any case to be able to Ajax-refresh e.g. after adding
            # new records or changing the filter)
            dl = datalist.html(start = start if start else 0,
                               limit = limit if limit else numrows,
                               pagesize = pagelength,
                               rowsize = rowsize,
                               ajaxurl = ajax_url)
            #if empty:
            #    # Insert empty message
            #    dl.insert(0, DIV(empty, _class="empty"))
            data = dl
        else:
            r.error(501, current.ERROR.BAD_FORMAT)


        if representation == "html":

            # View + data
            response.view = self._view(r, "list_filter.html")
            output["items"] = data

        elif representation == "dl":

            # View + data
            response.view = "plain.html"
            output["item"] = data

        elif representation == "popup":

            # View + data
            response.view = "popup.html"
            output["items"] = data
            # Pagination Support (normally added by views/dataLists.html)
            if s3.debug:
                appname = current.request.application
                sappend = s3.scripts.append
                sappend("/%s/static/scripts/jquery.infinitescroll.js" % appname)
                sappend("/%s/static/scripts/jquery.viewport.js" % appname)
                sappend("/%s/static/scripts/S3/s3.dataLists.js" % appname)
            else:
                s3.scripts.append("/%s/static/scripts/S3/s3.dataLists.min.js" % current.request.application)

        return output

    # -------------------------------------------------------------------------
    def unapproved(self, r, **attr):
        """
            Get a list of unapproved records in this resource

            @param r: the S3Request
            @param attr: dictionary of parameters for the method handler
        """

        session = current.session
        response = current.response
        s3 = response.s3

        resource = self.resource
        table = self.table

        representation = r.representation

        output = dict()

        # Get table-specific parameters
        _config = self._config
        orderby = _config("orderby", None)
        linkto = _config("linkto", None)
        list_fields = _config("list_fields")

        list_id = "datatable"

        # Check permission to read in this table
        authorised = self._permitted()
        if not authorised:
            r.unauthorised()

        # Pagination
        get_vars = self.request.get_vars
        if representation == "aadata":
            start, limit = self._limits(get_vars)
        else:
            start = None
            limit = None if s3.no_sspag else 0

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

        left = []
        distinct = False

        if r.interactive:

            resource.build_query(filter=s3.filter)

            # View
            response.view = self._view(r, "list.html")

            # Page title
            crud_string = self.crud_string
            if r.component:
                title = crud_string(r.tablename, "title_display")
            else:
                title = crud_string(self.tablename, "title_list")
            output["title"] = title

            # How many records per page?
            if s3.dataTable_pageLength:
                display_length = s3.dataTable_pageLength
            else:
                display_length = 25

            # Server-side pagination?
            if not s3.no_sspag:
                dt_pagination = "true"
                if not limit:
                    limit = 2 * display_length
                session.s3.filter = get_vars
                if orderby is None:
                    # Default initial sorting
                    scol = len(list_fields) > 1 and "1" or "0"
                    get_vars.update(iSortingCols="1",
                                    iSortCol_0=scol,
                                    sSortDir_0="asc")
                    q, orderby, left = resource.datatable_filter(list_fields,
                                                                 get_vars)
                    del get_vars["iSortingCols"]
                    del get_vars["iSortCol_0"]
                    del get_vars["sSortDir_0"]
            else:
                dt_pagination = "false"

            # Get the data table
            dt, totalrows, ids = resource.datatable(fields=list_fields,
                                                    start=start,
                                                    limit=limit,
                                                    left=left,
                                                    orderby=orderby,
                                                    distinct=distinct)
            displayrows = totalrows

            # No records?
            if dt is None:
                s3.no_formats = True
                datatable = current.T("No records to review")
            else:
                dt_dom = s3.get("dataTable_dom",
                                current.deployment_settings.get_ui_datatables_dom())
                datatable = dt.html(totalrows, displayrows, list_id,
                                    dt_pagination=dt_pagination,
                                    dt_pageLength=display_length,
                                    dt_dom = dt_dom,
                                    )
                s3.actions = [{"label": str(current.T("Review")),
                               "url": r.url(id="[id]", method="review"),
                               "_class": "action-btn"}]

            # Add items to output
            output["items"] = datatable

        elif r.representation == "aadata":

            resource.build_query(filter=s3.filter, vars=session.s3.filter)

            # Apply datatable filters
            searchq, orderby, left = resource.datatable_filter(list_fields, get_vars)
            if searchq is not None:
                totalrows = resource.count()
                resource.add_filter(searchq)
            else:
                totalrows = None

            # Orderby fallbacks
            if orderby is None:
                orderby = _config("orderby", None)

            # Get a data table
            if totalrows != 0:
                dt, displayrows, ids = resource.datatable(fields=list_fields,
                                                          start=start,
                                                          limit=limit,
                                                          left=left,
                                                          orderby=orderby,
                                                          distinct=distinct)
            else:
                dt, displayrows = None, 0
            if totalrows is None:
                totalrows = displayrows

            # Echo
            draw = int(get_vars.draw or 0)

            # Representation
            if dt is not None:
                output = dt.json(totalrows,
                                 displayrows,
                                 list_id,
                                 draw)
            else:
                output = '{"recordsTotal": %s, ' \
                         '"recordsFiltered": 0,' \
                         '"dataTable_id": "%s", ' \
                         '"draw": %s, ' \
                         '"data": []}' % (totalrows, list_id, draw)

        else:
            r.error(501, current.ERROR.BAD_FORMAT)

        return output

    # -------------------------------------------------------------------------
    def review(self, r, **attr):
        """
            Review/approve/reject an unapproved record.

            @param r: the S3Request
            @param attr: dictionary of parameters for the method handler
        """

        if not self._permitted("review"):
            r.unauthorized()

        T = current.T

        session = current.session
        response = current.response

        output = Storage()
        if r.interactive:

            _next = r.url(id="[id]", method="review")

            if self._permitted("approve"):

                approve = FORM(INPUT(_value=T("Approve"),
                                    _type="submit",
                                    _name="approve-btn",
                                    _id="approve-btn"))

                reject = FORM(INPUT(_value=T("Reject"),
                                    _type="submit",
                                    _name="reject-btn",
                                    _id="reject-btn"))

                cancel = A(T("Cancel"),
                           _href=r.url(id=0),
                           _class="action-lnk")

                output["approve_form"] = DIV(TABLE(TR(approve, reject, cancel)),
                                             _id="approve_form")

                reviewing = False
                if approve.accepts(r.post_vars, session, formname="approve"):
                    resource = current.s3db.resource(r.tablename, r.id,
                                                     approved=False,
                                                     unapproved=True)
                    try:
                        success = resource.approve()
                    except:
                        success = False
                    if success:
                        response.confirmation = T("Record approved")
                        output["approve_form"] = ""
                    else:
                        response.warning = T("Record could not be approved.")

                    r.http = "GET"
                    _next = r.url(id=0, method="review")

                elif reject.accepts(r.post_vars, session, formname="reject"):
                    resource = current.s3db.resource(r.tablename, r.id,
                                                     approved=False,
                                                     unapproved=True)
                    try:
                        success = resource.reject()
                    except:
                        success = False
                    if success:
                        response.confirmation = T("Record deleted")
                        output["approve_form"] = ""
                    else:
                        response.warning = T("Record could not be deleted.")

                    r.http = "GET"
                    _next = r.url(id=0, method="review")

                else:
                    reviewing = True

            if reviewing:
                output.update(self.read(r, **attr))
            self.next = _next
            r.http = r.env.request_method
            current.response.view = "review.html"

        else:
            r.error(501, current.ERROR.BAD_FORMAT)

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
            r.error(501, current.ERROR.BAD_FORMAT)

        resource = self.resource

        get_vars = r.get_vars
        if "component" in get_vars:
            alias = get_vars["component"]
        else:
            alias = None
        if "resource" in get_vars:
            tablename = get_vars["resource"]
            components = [alias] if alias else None
            try:
                resource = current.s3db.resource(tablename,
                                                 components=components)
            except:
                r.error(404, current.ERROR.BAD_RESOURCE)
        if alias:
            if alias in resource.components:
                component = resource.components[alias]
            else:
                r.error(404, current.ERROR.BAD_RESOURCE)
        else:
            component = resource

        source = r.body
        source.seek(0)

        try:
            data = json.load(source)
        except ValueError:
            r.error(501, current.ERROR.BAD_SOURCE)

        if not isinstance(data, list):
            single = True
            data = [data]
        else:
            single = False

        table = component.table
        pkey = table._id.name

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

                error = None
                validated = fields[fname] = Storage()

                # We do not validate primary keys
                # (because we don't update them)
                if fname in (pkey, "_id"):
                    continue

                value = record[fname]

                if fname not in table.fields:
                    validated["value"] = value
                    validated["_error"] = "invalid field"
                    continue
                else:
                    field = table[fname]

                # Convert numeric type (does not always happen in the widget)
                field = table[fname]
                if field.type == "integer":
                    if value not in (None, ""):
                        try:
                            value = int(value)
                        except ValueError:
                            value = 0
                    else:
                        value = None
                if field.type == "double":
                    if value not in (None, ""):
                        try:
                            value = float(value)
                        except ValueError:
                            value = 0
                    else:
                        value = None

                widget = field.widget
                if isinstance(widget, S3Selector):
                    # Use widget-validator instead of field-validator
                    value, error = widget.validate(value)
                    validated["value"] = widget.serialize(value)
                    # Use widget-represent instead of standard represent
                    widget_represent = widget.represent
                else:
                    # Validate and format the value
                    try:
                        value, error = s3_validate(table, fname, value, original)
                    except AttributeError:
                        error = "invalid field"
                    validated["value"] = field.formatter(value)
                    widget_represent = None

                # Handle errors, update the validated item
                if error:
                    has_errors = True
                    validated["_error"] = s3_unicode(error)
                elif widget_represent:
                    try:
                        text = widget_represent(value)
                    except:
                        text = s3_unicode(value)
                    validated["text"] = text
                else:
                    try:
                        text = s3_represent_value(field, value = value)
                    except:
                        text = s3_unicode(value)
                    validated["text"] = text

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

        return json.dumps(output, separators=SEPARATORS)

    # -------------------------------------------------------------------------
    # Utility functions
    # -------------------------------------------------------------------------
    @staticmethod
    def crud_button(label=None,
                    tablename=None,
                    name=None,
                    icon=None,
                    _href=None,
                    _id=None,
                    _class=None,
                    _title=None,
                    _target=None,
                    **attr):
        """
            Generate a CRUD action button

            @param label: the link label (None if using CRUD string)
            @param tablename: the name of table for CRUD string selection
            @param name: name of CRUD string for the button label
            @param icon: name of the icon (e.g. "add")
            @param _href: the target URL
            @param _id: the HTML id of the link
            @param _class: the HTML class of the link
            @param _title: the HTML title of the link
            @param _target: the HTML target of the link

            @keyword custom: custom CRUD button (just add classes)
        """

        settings = current.deployment_settings

        # If using Bootstrap then we need to amend our core HTML markup
        bootstrap = settings.ui.formstyle == "bootstrap"

        # Custom button?
        if "custom" in attr:
            custom = attr["custom"]
            if custom is None:
                custom = ""
            elif bootstrap and hasattr(custom, "add_class"):
                custom.add_class("btn btn-primary")
            return custom

        # Default class
        if _class is None and not bootstrap:
            _class = "action-btn"

        # Default label
        if name:
            labelstr = S3CRUD.crud_string(tablename, name)
        else:
            labelstr = str(label)

        # Show icon on button?
        if icon and settings.get_ui_use_button_icons():
            button = A(ICON(icon), labelstr, _id=_id, _class=_class)
        else:
            button = A(labelstr, _id=_id, _class=_class)

        # Button attributes
        if _href:
            button["_href"] = _href
        if _title:
            button["_title"] = _title
        if _target:
            button["_target"] = _target

        # Additional classes?
        if bootstrap:
            button.add_class("btn btn-primary")
        return button

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
                record = current.db(query).select(limitby=(0, 1),
                                                  *fields).first()

                if record:
                    if "modified_by" in record:
                        if not record.modified_by:
                            modified_by = T("anonymous user")
                        else:
                            modified_by = \
                                table.modified_by.represent(record.modified_by)
                        output["modified_by"] = T("by %(person)s") % \
                                                  dict(person = modified_by)
                    if "modified_on" in record:
                        output["modified_on"] = T("on %(date)s") % \
                                                dict(date = record.modified_on)

        return output

    # -------------------------------------------------------------------------
    def render_buttons(self, r, buttons, record_id=None, **attr):
        """
            Render CRUD buttons

            @param r: the S3Request
            @param buttons: list of button names, any of:
                            "add", "edit", "delete", "list", "summary"
            @param record_id: the record ID
            @param attr: the controller attributes

            @return: a dict of buttons for the view
        """

        output = {}
        custom_crud_buttons = attr.get("custom_crud_buttons", {})

        tablename = self.tablename
        representation = r.representation

        url = r.url

        remove_filters = self._remove_filters
        crud_string = self.crud_string
        config = self._config
        crud_button = self.crud_button

        # Add button
        if "add" in buttons and config("insertable", True):
            ADD_BTN = "add_btn"
            authorised = self._permitted(method="create")
            if authorised:
                if ADD_BTN in custom_crud_buttons:
                    btn = crud_button(custom=custom_crud_buttons[ADD_BTN])
                else:
                    label = crud_string(tablename, "label_create")
                    _href = url(method="create",
                                representation=representation)
                    btn = crud_button(label=label,
                                      icon="add",
                                      _href=_href,
                                      _id="add-btn")
                output[ADD_BTN] = btn

        # List button
        if "list" in buttons:
            LIST_BTN = "list_btn"
            if not r.component or r.multiple:
                if LIST_BTN in custom_crud_buttons:
                    btn = crud_button(custom=custom_crud_buttons[LIST_BTN])
                else:
                    label = crud_string(tablename, "label_list_button")
                    _href = url(method="",
                                id=r.id if r.component else 0,
                                vars=remove_filters(r.get_vars),
                                representation=representation)
                    btn = crud_button(label=label,
                                      icon="list",
                                      _href=_href,
                                      _id="list-btn")
                output[LIST_BTN] = btn

        # Summary button
        if "summary" in buttons:
            SUMMARY_BTN = "summary_btn"
            if not r.component or r.multiple:
                if SUMMARY_BTN in custom_crud_buttons:
                    btn = crud_button(custom=custom_crud_buttons[SUMMARY_BTN])
                else:
                    label = crud_string(tablename, "label_list_button")
                    _href = url(method="summary",
                                id=0,
                                vars=remove_filters(r.get_vars),
                                representation=representation)
                    btn = crud_button(label=label,
                                      icon="list",
                                      _href=_href,
                                      _id="summary-btn")
                output[SUMMARY_BTN] = btn

        if not record_id:
            return output

        # Edit button
        if "edit" in buttons and config("editable", True):
            EDIT_BTN = "edit_btn"
            authorised = self._permitted(method="update")
            if authorised:
                if EDIT_BTN in custom_crud_buttons:
                    btn = crud_button(custom=custom_crud_buttons[EDIT_BTN])
                else:
                    label = current.messages.UPDATE
                    _href = url(method="update",
                                representation=representation)
                    btn = crud_button(label=label,
                                      icon="edit",
                                      _href=_href,
                                      _id="edit-btn")
                output[EDIT_BTN] = btn

        # Delete button
        if "delete" in buttons and config("deletable", True):
            DELETE_BTN = "delete_btn"
            authorised = self._permitted(method="delete")
            if authorised:
                if DELETE_BTN in custom_crud_buttons:
                    btn = crud_button(custom=custom_crud_buttons[DELETE_BTN])
                else:
                    label = crud_string(tablename, "label_delete_button")
                    _href = url(method="delete",
                                representation=representation)
                    btn = crud_button(label=label,
                                      icon="delete",
                                      _href=_href,
                                      _id="delete-btn",
                                      _class="delete-btn")
                output[DELETE_BTN] = btn

        return output

    # -------------------------------------------------------------------------
    @staticmethod
    def action_button(label, url, icon=None, **attr):
        """
            Add a link to response.s3.actions

            @param label: the link label
            @param url: the target URL
            @param attr: attributes for the link (default: {"_class":"action-btn"})
        """

        link = dict(attr)
        link["label"] = str(label)
        link["url"] = url
        if icon and current.deployment_settings.get_ui_use_button_icons():
            link["icon"] = ICON.css_class(icon)
        if "_class" not in link:
            link["_class"] = "action-btn"

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
        s3 = current.response.s3
        labels = s3.crud_labels

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

        get_vars = Storage()
        if "viewing" in r.get_vars:
            get_vars["viewing"] = r.get_vars["viewing"]

        # If this request is in iframe-format, action URLs should be in
        # iframe-format as well
        if r.representation == "iframe":
            if current.deployment_settings.get_ui_iframe_opens_full():
                iframe_safe = lambda url: url
                # This is processed client-side in s3.dataTables.js
                target = dict(_target="_blank")
            else:
                iframe_safe = lambda url: s3_set_extension(url, "iframe")
                target = {}
        else:
            iframe_safe = lambda url: url
            target = {}

        # Open-action (Update or Read)
        if editable and has_permission("update", table) and \
           not ownership_required("update", table):
            if not update_url:
                # To use modals
                #get_vars["refresh"] = "list"
                update_url = iframe_safe(URL(args = args + ["update"], #.popup to use modals
                                             vars = get_vars))
            s3crud.action_button(labels.UPDATE, update_url,
                                 # To use modals
                                 #_class="action-btn s3_modal"
                                 _class="action-btn edit",
                                 icon = "edit",
                                 **target
                                 )
        else:
            if not read_url:
                read_url = iframe_safe(URL(args = args,
                                           vars = get_vars))
            s3crud.action_button(labels.READ, read_url,
                                 # To use modals
                                 #_class="action-btn s3_modal"
                                 _class="action-btn read",
                                 icon = "file",
                                 **target
                                 )

        # Delete-action
        if deletable and has_permission("delete", table):
            icon = "delete"
            if not delete_url:
                delete_url = iframe_safe(URL(args = args + ["delete"],
                                             vars = get_vars))
            if ownership_required("delete", table):
                # Check which records can be deleted
                query = auth.s3_accessible_query("delete", table)
                rows = current.db(query).select(table._id)
                restrict = []
                rappend = restrict.append
                for row in rows:
                    row_id = row.get("id", None)
                    if row_id:
                        rappend(str(row_id))
                s3crud.action_button(labels.DELETE, delete_url,
                                     _class="delete-btn",
                                     icon=icon,
                                     restrict=restrict,
                                     **target
                                     )
            else:
                s3crud.action_button(labels.DELETE, delete_url,
                                     _class="delete-btn",
                                     icon=icon,
                                     **target
                                     )

        # Copy-action
        if copyable and has_permission("create", table):
            if not copy_url:
                copy_url = iframe_safe(URL(args = args + ["copy"]))
            s3crud.action_button(labels.COPY,
                                 copy_url,
                                 icon="icon-copy",
                                 **target
                                 )

        # Append custom actions
        if custom_actions:
            s3.actions = s3.actions + custom_actions
        return

    # -------------------------------------------------------------------------
    def _default_cancel_button(self, r):
        """
            Show a default cancel button in standalone create/update forms.
            Individual controllers can override this by setting
            response.s3.cancel = False.

            @param r: the S3Request
        """

        if r.representation != "html":
            return False

        s3 = current.response.s3

        cancel = s3.cancel
        if cancel is False or isinstance(cancel, dict):
            success = False
        elif cancel is True or \
             current.deployment_settings.get_ui_default_cancel_button():

            if isinstance(cancel, basestring):
                default_url = cancel
            else:
                method = r.method
                if method == "create":
                    if r.component:
                        default_url = r.url(method = "",
                                            component_id= "",
                                            vars = {},
                                            )
                    else:
                        config = self._config("summary")
                        if config or \
                           current.deployment_settings.get_ui_summary():
                            default_url = r.url(method="summary", id=0)
                        else:
                            default_url = r.url(method="", id=0)
                elif method == "update" or not method:
                    if r.component:
                        default_url = r.url(method = "",
                                            component_id= "",
                                            vars = {},
                                            )
                    else:
                        default_url = r.url(method="read")
            if default_url:
                script = '''$.cancelButtonS3('%s')''' % default_url
            else:
                script = '''$.cancelButtonS3()'''
            jquery_ready = current.response.s3.jquery_ready
            if script not in jquery_ready:
                jquery_ready.append(script)
            success = s3.cancel = True
        else:
            success = False

        return success

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
                        data.text = value
                    element.append(data)
        tree = xml.tree([element], domain=xml.domain)

        # Import data
        result = Storage(committed=False)
        def log(item):
            result["item"] = item
        resource.configure(oncommit_import_item = log)
        try:
            success = resource.import_xml(tree)
        except SyntaxError:
            pass

        # Check result
        if result.item:
            result = result.item

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

        s3db = current.s3db
        request = current.request

        get_config = lambda key, tablename=component: \
                            s3db.get_config(tablename, key, None)
        try:
            selected = form.vars[key]
        except:
            selected = None

        if request.env.request_method == "POST":
            db = current.db
            table = db[component]

            # Extract data for embedded form from post_vars
            post_vars = request.post_vars
            form_vars = Storage(table._filter_fields(post_vars))

            # Pass values through validator to convert them into db-format
            for k in form_vars:
                value, error = s3_validate(table, k, form_vars[k])
                if not error:
                    form_vars[k] = value

            _form = Storage(vars = form_vars, errors = Storage())
            if _form.vars:
                if selected:
                    form_vars[table._id.name] = selected
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
                    # Update super-entity links
                    s3db.update_super(table, dict(id=selected))
                    # Update realm
                    update_realm = s3db.get_config(table, "update_realm")
                    if update_realm:
                        current.auth.set_realm_entity(table, selected,
                                                      force_update=True)
                    # Onaccept
                    onaccept = get_config("update_onaccept") or \
                               get_config("onaccept")
                    callback(onaccept, _form, tablename=component)
                else:
                    form_vars.pop(table._id.name, None)
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
                        post_vars[key] = str(selected)
                        form.request_vars[key] = str(selected)
                        form.vars[key] = selected
                        # Update super-entity links
                        s3db.update_super(table, dict(id=selected))
                        # Set record owner
                        auth = current.auth
                        auth.s3_set_record_owner(table, selected)
                        auth.s3_make_session_owner(table, selected)
                        # Onaccept
                        onaccept = get_config("create_onaccept") or \
                                   get_config("onaccept")
                        callback(onaccept, _form, tablename=component)
                    else:
                        form.errors[key] = current.T("Could not create record.")
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

        if r.representation == "iframe":
            if current.deployment_settings.get_ui_iframe_opens_full():
                iframe_safe = lambda url: s3_set_extension(url, "html")
            else:
                iframe_safe = lambda url: s3_set_extension(url, "iframe")
        else:
            iframe_safe = False

        def list_linkto(record_id, r=r, c=c, f=f,
                        linkto=linkto,
                        update=authorised and update):

            if linkto:
                try:
                    url = str(linkto(record_id))
                except TypeError:
                    url = linkto % record_id
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
                        url = str(URL(r=r, c=c, f=f,
                                      args=args + ["update"],
                                      # Don't forward all vars unconditionally
                                      #vars=r.get_vars
                                      ))
                    else:
                        url = str(URL(r=r, c=c, f=f,
                                      args=args + ["read"],
                                      # Don't forward all vars unconditionally
                                      #vars=r.get_vars
                                      ))
                else:
                    args = [record_id]
                    if update:
                        url = str(URL(r=r, c=c, f=f,
                                      args=args + ["update"],
                                      # Don't forward all vars unconditionally
                                      #vars=r.get_vars
                                      ))
                    else:
                        url = str(URL(r=r, c=c, f=f,
                                      args=args + ["read"],
                                      # Don't forward all vars unconditionally
                                      #vars=r.get_vars
                                      ))
            if iframe_safe:
                url = iframe_safe(url)
            return url

        return list_linkto

    # -------------------------------------------------------------------------
    @staticmethod
    def _interim_save_button():
        """
            Render an additional custom submit button for interim save,
            which overrides the default _next to returns to an update
            form for the same record after create/update
        """

        label = current.deployment_settings.get_ui_interim_save()
        if label:
            _class = "interim-save"
            if isinstance(label, basestring):
                label = current.T(label)
            elif isinstance(label, (tuple, list)) and len(label) > 1:
                label, _class = label[:2]
            elif not isinstance(label, lazyT):
                label = current.T("Save and Continue Editing")
            item = ("interim_save", label, _class)
        else:
            return
        settings = current.response.s3.crud
        if settings.custom_submit:
            settings.custom_submit.insert(0, item)
        else:
            settings.custom_submit = [item]
        return

    # -------------------------------------------------------------------------
    @classmethod
    def _dl_ajax_delete(cls, r, resource):

        UID = current.xml.UID

        delete = r.get_vars.get("delete", None)
        if delete is not None:

            dresource = current.s3db.resource(resource, id=delete)

            # Deleting in this resource allowed at all?
            deletable = dresource.get_config("deletable", True)
            if not deletable:
                r.error(403, current.ERROR.NOT_PERMITTED)

            # Permitted to delete this record?
            authorised = current.auth.s3_has_permission("delete",
                                                        dresource.table,
                                                        record_id=delete)
            if not authorised:
                r.unauthorised()

            # Delete it
            uid = None
            if UID in dresource.table:
                rows = dresource.select([UID],
                                        start=0,
                                        limit=1,
                                        as_rows=True)
                if rows:
                    uid = rows[0][UID]
            numrows = dresource.delete(format=r.representation)
            if numrows > 1:
                message = "%s %s" % (numrows,
                                     current.T("records deleted"))
            elif numrows == 1:
                message = cls.crud_string(dresource.tablename,
                                          "msg_record_deleted")
            else:
                r.error(404, dresource.error)

            # Return a JSON message
            # @note: make sure the view doesn't get overridden afterwards!
            current.response.view = "xml.html"
            return current.xml.json_message(message=message, uuid=uid)
        else:
            r.error(404, current.ERROR.BAD_RECORD)

    # -------------------------------------------------------------------------
    @staticmethod
    def _limits(get_vars):
        """
            Extract page limits (start and limit) from GET vars

            @param get_vars: the GET vars
        """

        start = get_vars.get("start", None)
        limit = get_vars.get("limit", 0)
        # Deal with overrides (pagination limits come last)
        if isinstance(start, list):
            start = start[-1]
        if isinstance(limit, list):
            limit = limit[-1]
        if limit:
            # Ability to override default limit to "Show All"
            if limit.lower() == "none":
                #start = None # needed?
                limit = None
            else:
                try:
                    start = int(start) if start is not None else None
                    limit = int(limit)
                except (ValueError, TypeError):
                    # Fall back to defaults
                    start, limit = None, 0
        else:
            # Use defaults, assume sspag because this is a
            # pagination request by definition
            start = None
            limit = 0

        return start, limit

# END =========================================================================
