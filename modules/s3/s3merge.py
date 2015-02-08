# -*- coding: utf-8 -*-

""" S3 Record Merger

    @requires: U{B{I{gluon}} <http://web2py.com>}

    @copyright: 2012-13 (c) Sahana Software Foundation
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

__all__ = ["S3Merge"]

import sys

from gluon import *
from gluon.html import BUTTON
from gluon.storage import Storage
from s3rest import S3Method
from s3resource import S3FieldSelector
from s3widgets import *
from s3validators import *
from s3utils import s3_unicode
from s3data import S3DataTable

# =============================================================================
class S3Merge(S3Method):
    """ Interactive Record Merger """

    DEDUPLICATE = "deduplicate"

    ORIGINAL = "original"
    DUPLICATE = "duplicate"
    KEEP = Storage(o="keep_original", d="keep_duplicate")

    # -------------------------------------------------------------------------
    def apply_method(self, r, **attr):
        """
            Apply Merge methods

            @param r: the S3Request
            @param attr: dictionary of parameters for the method handler

            @return: output object to send to the view
        """

        output = dict()

        auth = current.auth
        system_roles = auth.get_system_roles()
        if not auth.s3_has_role(system_roles.ADMIN):
            r.unauthorized()

        if r.method == "deduplicate":
            if r.http in ("GET", "POST"):
                if "remove" in r.get_vars:
                    remove = r.get_vars["remove"].lower() in ("1", "true")
                else:
                    remove = False
                if remove:
                    output = self.unmark(r, **attr)
                elif self.record_id:
                    if r.component and not r.component.multiple:
                        if r.http == "POST":
                            output = self.mark(r, **attr)
                        else:
                            # This does really not make much sense here
                            # => duplicate list is filtered per master
                            # and hence there is always only one record
                            output = self.duplicates(r, **attr)
                    else:
                        output = self.mark(r, **attr)
                else:
                    output = self.duplicates(r, **attr)
            elif r.http == "DELETE":
                output = self.unmark(r, **attr)
            else:
                r.error(405, r.ERROR.BAD_METHOD)
        else:
            r.error(405, r.ERROR.BAD_METHOD)

        return output

    # -------------------------------------------------------------------------
    def mark(self, r, **attr):
        """
            Bookmark the current record for de-duplication

            @param r: the S3Request
            @param attr: the controller parameters for the request
        """

        s3 = current.session.s3

        DEDUPLICATE = self.DEDUPLICATE

        if DEDUPLICATE not in s3:
            bookmarks = s3[DEDUPLICATE] = Storage()
        else:
            bookmarks = s3[DEDUPLICATE]

        record_id = str(self.record_id)
        if record_id:
            tablename = self.tablename
            if tablename not in bookmarks:
                records = bookmarks[tablename] = []
            else:
                records = bookmarks[tablename]
            if record_id not in records:
                records.append(record_id)
        else:
            return self.duplicates(r, **attr)

        return current.xml.json_message()

    # -------------------------------------------------------------------------
    def unmark(self, r, **attr):
        """
            Remove a record from the deduplicate list

            @param r: the S3Request
            @param attr: the controller parameters for the request
        """

        s3 = current.session.s3
        DEDUPLICATE = self.DEDUPLICATE

        success = current.xml.json_message()

        if DEDUPLICATE not in s3:
            return success
        else:
            bookmarks = s3[DEDUPLICATE]
        tablename = self.tablename
        if tablename not in bookmarks:
            return success
        else:
            records = bookmarks[tablename]

        record_id = str(self.record_id)
        if record_id:
            if record_id in records:
                records.remove(record_id)
            if not records:
                bookmarks.pop(tablename)
        else:
            bookmarks.pop(tablename)
        return success

    # -------------------------------------------------------------------------
    @classmethod
    def bookmark(cls, r, tablename, record_id):
        """
            Get a bookmark link for a record in order to embed it in the
            view, also renders a link to the duplicate bookmark list to
            initiate the merge process from

            @param r: the S3Request
            @param tablename: the table name
            @param record_id: the record ID
        """

        auth = current.auth
        system_roles = auth.get_system_roles()
        if not auth.s3_has_role(system_roles.ADMIN):
            return ""
        if r.component and not r.component.multiple:
            # Cannot de-duplicate single-components
            return ""

        s3 = current.session.s3
        DEDUPLICATE = cls.DEDUPLICATE

        remove = DEDUPLICATE in s3 and \
                 tablename in s3[DEDUPLICATE] and \
                 str(record_id) in s3[DEDUPLICATE][tablename] and \
                 True or False

        mark = "mark-deduplicate action-lnk"
        unmark = "unmark-deduplicate action-lnk"
        deduplicate = "deduplicate action-lnk"

        if remove:
            mark += " hide"
        else:
            unmark += " hide"
            deduplicate += " hide"

        T = current.T
        link = DIV(A(T("Mark as duplicate"),
                       _class=mark),
                   A(T("Unmark as duplicate"),
                       _class=unmark),
                   A("",
                     _href=r.url(method="deduplicate", vars={}),
                     _id="markDuplicateURL",
                     _class="hide"),
                   A(T("De-duplicate"),
                     _href=r.url(method="deduplicate", target=0, vars={}),
                     _class=deduplicate),
                   _id="markDuplicate")

        return link

    # -------------------------------------------------------------------------
    def duplicates(self, r, **attr):
        """
            Renders a list of all currently duplicate-bookmarked
            records in this resource, with option to select two
            and initiate the merge process from here

            @param r: the S3Request
            @param attr: the controller attributes for the request
        """

        s3 = current.session.s3

        resource = self.resource
        tablename = self.tablename

        if r.http == "POST":
            return self.merge(r, **attr)

        # Bookmarks
        record_ids = []
        DEDUPLICATE = self.DEDUPLICATE
        if DEDUPLICATE in s3:
            bookmarks = s3[DEDUPLICATE]
            if tablename in bookmarks:
                record_ids = bookmarks[tablename]
        query = S3FieldSelector(resource._id.name).belongs(record_ids)
        resource.add_filter(query)

        # Representation
        representation = r.representation

        # List fields
        list_fields = resource.list_fields()

        # Start/Limit
        vars = r.get_vars
        if representation == "aadata":
            start = vars.get("iDisplayStart", None)
            limit = vars.get("iDisplayLength", None)
            sEcho = int(vars.sEcho or 0)
        else: # catch all
            start = 0
            limit = current.manager.ROWSPERPAGE
        if limit is not None:
            try:
                start = int(start)
                limit = int(limit)
            except ValueError:
                start = None
                limit = None # use default
        else:
            start = None # use default
        if current.response.s3.dataTable_iDisplayLength:
            display_length = current.response.s3.dataTable_iDisplayLength
        else:
            display_length = 25
        if limit is None:
            limit = 2 * display_length

        # Datatable Filter
        totalrows = None
        if representation == "aadata":
            searchq, orderby, left = resource.datatable_filter(list_fields,
                                                               vars)
            if searchq is not None:
                totalrows = resource.count()
                resource.add_filter(searchq)
        else:
            orderby, left = None, None

        # Get the records
        data = resource.select(list_fields,
                               start=start,
                               limit=limit,
                               orderby=orderby,
                               left=left,
                               count=True,
                               represent=True)

        
        displayrows = data["numrows"]
        if totalrows is None:
            totalrows = displayrows

        # Generate a datatable
        dt = S3DataTable(data["rfields"], data["rows"])
        
        datatable_id = "s3merge_1"
        response = current.response

        if representation == "aadata":
            output = dt.json(totalrows,
                             displayrows,
                             datatable_id,
                             sEcho,
                             dt_bulk_actions = [(current.T("Merge"),
                                                 "merge", "pair-action")])
                                                 
        elif representation == "html":
            # Initial HTML response
            T = current.T
            output = {"title": T("De-duplicate Records")}

            url = r.url(representation="aadata")

            #url = "/%s/%s/%s/deduplicate.aadata" % (r.application,
                                                    #r.controller,
                                                    #r.function)
            items =  dt.html(totalrows,
                             displayrows,
                             datatable_id,
                             dt_ajax_url=url,
                             dt_displayLength=display_length,
                             dt_bulk_actions = [(T("Merge"),
                                                 "merge", "pair-action")])

            output["items"] = items
            response.s3.actions = [{"label": str(T("View")),
                                    "url": r.url(target="[id]", method="read"),
                                    "_class": "action-btn"}]

            if len(record_ids) < 2:
                output["add_btn"] = DIV(
                    SPAN(T("You need to have at least 2 records in this list in order to merge them."),
                      _style="float:left; padding-right:10px;"),
                    A(T("Find more"),
                      _href=r.url(method="search", id=0, component_id=0, vars={}))
                )
            else:
                output["add_btn"] = DIV(
                    SPAN(T("Select 2 records from this list, then click 'Merge'.")),
                )

            response.s3.dataTableID = [datatable_id]
            response.view = self._view(r, "list.html")

        else:
            r.error(501, r.ERROR.BAD_FORMAT)

        return output

    # -------------------------------------------------------------------------
    def merge(self, r, **attr):
        """
            Merge form for two records

            @param r: the S3Request
            @param **attr: the controller attributes for the request

            @note: this method can always only be POSTed, and requires
                   both "selected" and "mode" in post_vars, as well as
                   the duplicate bookmarks list in session.s3
        """

        T = current.T
        session = current.session
        response = current.response

        output = dict()
        tablename = self.tablename

        # Get the duplicate bookmarks
        s3 = session.s3
        DEDUPLICATE = self.DEDUPLICATE
        if DEDUPLICATE in s3:
            bookmarks = s3[DEDUPLICATE]
            if tablename in bookmarks:
                record_ids = bookmarks[tablename]

        # Process the post variables
        post_vars = r.post_vars
        if "mode" in post_vars:
            mode = post_vars["mode"]
        if "selected" in post_vars:
            selected = post_vars["selected"]
        else:
            selected = ""
        selected = selected.split(",")
        if mode == "Inclusive":
            ids = selected
        elif mode == "Exclusive":
            ids = [i for i in record_ids if i not in selected]
        if len(ids) != 2:
            r.error(501, T("Please select exactly two records"),
                    next = r.url(id=0, vars={}))

        # Get the selected records
        table = self.table
        query = (table._id == ids[0]) | (table._id == ids[1])
        orderby = table.created_on if "created_on" in table else None
        rows = current.db(query).select(orderby=orderby,
                                        limitby=(0, 2))
        if len(rows) != 2:
            r.error(404, r.ERROR.BAD_RECORD, next = r.url(id=0, vars={}))
        original = rows[0]
        duplicate = rows[1]

        # Prepare form construction
        formfields = [f for f in table if f.readable or f.writable]

        ORIGINAL, DUPLICATE, KEEP = self.ORIGINAL, self.DUPLICATE, self.KEEP
        keep_o = KEEP.o in post_vars and post_vars[KEEP.o]
        keep_d = KEEP.d in post_vars and post_vars[KEEP.d]

        trs = []
        represent = current.manager.represent
        init_requires = self.init_requires
        for f in formfields:

            # Render the widgets
            oid = "%s_%s" % (ORIGINAL, f.name)
            did = "%s_%s" % (DUPLICATE, f.name)
            sid = "swap_%s" % f.name
            init_requires(f, original[f], duplicate[f])
            if keep_o or not any((keep_o, keep_d)):
                owidget = self.widget(f, original[f], _name=oid, _id=oid)
            else:
                try:
                    owidget = represent(f, value=original[f])
                except:
                    owidget = s3_unicode(original[f])
            if keep_d or not any((keep_o, keep_d)):
                dwidget = self.widget(f, duplicate[f], _name=did, _id=did)
            else:
                try:
                    dwidget = represent(f, value=duplicate[f])
                except:
                    dwidget = s3_unicode(duplicate[f])

            # Swap button
            if not any((keep_o, keep_d)):
                swap = INPUT(_value="<-->",
                             _class="swap-button",
                             _id=sid,
                             _type="button")
            else:
                swap = DIV(_class="swap-button")

            if owidget is None or dwidget is None:
                continue

            # Render label row
            label = f.label
            trs.append(TR(TD(label, _class="w2p_fl"),
                          TD(),
                          TD(label, _class="w2p_fl")))

            # Append widget row
            trs.append(TR(TD(owidget, _class="mwidget"),
                          TD(swap),
                          TD(dwidget, _class="mwidget")))

        # Show created_on/created_by for each record
        if "created_on" in table:
            original_date = original.created_on
            duplicate_date = duplicate.created_on
            if "created_by" in table:
                represent = table.created_by.represent
                original_author = represent(original.created_by)
                duplicate_author = represent(duplicate.created_by)
                created = T("Created on %s by %s")
                original_created = created % (original_date, original_author)
                duplicate_created = created % (duplicate_date, duplicate_author)
            else:
                created = T("Created on %s")
                original_created = created % original_date
                duplicate_created = created % duplicate_date
        else:
            original_created = ""
            duplicate_created = ""

        # Page title and subtitle
        output["title"] = T("Merge records")
        #output["subtitle"] = self.crud_string(tablename, "title_list")

        # Submit buttons
        if keep_o or not any((keep_o, keep_d)):
            submit_original = INPUT(_value=T("Keep Original"),
                                    _type="submit", _name=KEEP.o, _id=KEEP.o)
        else:
            submit_original = ""

        if keep_d or not any((keep_o, keep_d)):
            submit_duplicate = INPUT(_value=T("Keep Duplicate"),
                                     _type="submit", _name=KEEP.d, _id=KEEP.d)
        else:
            submit_duplicate = ""

        # Build the form
        form = FORM(TABLE(
                        THEAD(
                            TR(TH(H3(T("Original"))),
                               TH(),
                               TH(H3(T("Duplicate"))),
                            ),
                            TR(TD(original_created),
                               TD(),
                               TD(duplicate_created),
                               _class="authorinfo",
                            ),
                        ),
                        TBODY(trs),
                        TFOOT(
                            TR(TD(submit_original),
                               TD(),
                               TD(submit_duplicate),
                            ),
                        ),
                    ),
                    # Append mode and selected - required to get back here!
                    hidden = {
                        "mode": "Inclusive",
                        "selected": ",".join(ids),
                    }
                )

        output["form"] = form

        # Add RESET and CANCEL options
        output["reset"] = FORM(INPUT(_value=T("Reset"),
                                     _type="submit",
                                     _name="reset", _id="form-reset"),
                               A(T("Cancel"), _href=r.url(id=0, vars={}), _class="action-lnk"),
                               hidden = {"mode": mode,
                                         "selected": ",".join(ids)})

        # Process the merge form
        formname = "merge_%s_%s_%s" % (tablename,
                                       original[table._id],
                                       duplicate[table._id])
        if form.accepts(post_vars, session,
                        formname=formname,
                        onvalidation=lambda form: self.onvalidation(tablename, form),
                        keepvalues=False,
                        hideerror=False):

            s3db = current.s3db

            if form.vars[KEEP.d]:
                prefix = "%s_" % DUPLICATE
                original, duplicate = duplicate, original
            else:
                prefix = "%s_" % ORIGINAL

            data = Storage()
            for key in form.vars:
                if key.startswith(prefix):
                    fname = key.split("_", 1)[1]
                    data[fname] = form.vars[key]

            search = False
            resource = s3db.resource(tablename)
            try:
                resource.merge(original[table._id],
                               duplicate[table._id],
                               update=data)
            except current.auth.permission.error:
                r.unauthorized()
            except KeyError:
                r.error(404, r.ERROR.BAD_RECORD)
            except:
                r.error(424,
                        T("Could not merge records. (Internal Error: %s)") %
                            sys.exc_info()[1],
                        next=r.url())
            else:
                # Cleanup bookmark list
                if mode == "Inclusive":
                    bookmarks[tablename] = [i for i in record_ids if i not in ids]
                    if not bookmarks[tablename]:
                        del bookmarks[tablename]
                        search = True
                elif mode == "Exclusive":
                    bookmarks[tablename].extend(ids)
                    if not selected:
                        search = True
                # Confirmation message
                # @todo: Having the link to the merged record in the confirmation
                # message would be nice, but it's currently not clickable there :/
                #result = A(T("Open the merged record"),
                        #_href=r.url(method="read",
                                    #id=original[table._id],
                                    #vars={}))
                response.confirmation = T("Records merged successfully.")

            # Go back to bookmark list
            if search:
                self.next = r.url(method="search", id=0, vars={})
            else:
                self.next = r.url(id=0, vars={})

        # View
        response.view = self._view(r, "merge.html")

        return output

    # -------------------------------------------------------------------------
    @classmethod
    def onvalidation(cls, tablename, form):
        """
            Runs the onvalidation routine for this table, and maps
            form fields and errors to regular keys

            @param tablename: the table name
            @param form: the FORM
        """

        ORIGINAL, DUPLICATE, KEEP = cls.ORIGINAL, cls.DUPLICATE, cls.KEEP

        if form.vars[KEEP.d]:
            prefix = "%s_" % DUPLICATE
        else:
            prefix = "%s_" % ORIGINAL

        data = Storage()
        for key in form.vars:
            if key.startswith(prefix):
                fname = key.split("_", 1)[1]
                data[fname] = form.vars[key]

        errors = current.manager.onvalidation(tablename, data,
                                              method="update")
        if errors:
            for fname in errors:
                form.errors["%s%s" % (prefix, fname)] = errors[fname]
        return

    # -------------------------------------------------------------------------
    @staticmethod
    def init_requires(field, o, d):
        """
            Initialize all IS_NOT_IN_DB to allow override of
            both original and duplicate value

            @param field: the Field
            @param o: the original value
            @param d: the duplicate value
        """

        allowed_override = [str(o), str(d)]

        requires = field.requires
        if field.unique and not requires:
            field.requires = IS_NOT_IN_DB(current.db, str(field),
                                          allowed_override=allowed_override)
        else:
            if not isinstance(requires, (list, tuple)):
                requires = [requires]
            for r in requires:
                if hasattr(r, "allowed_override"):
                    r.allowed_override = allowed_override
                if hasattr(r, "other") and \
                   hasattr(r.other, "allowed_override"):
                    r.other.allowed_override = allowed_override
        return

    # -------------------------------------------------------------------------
    @staticmethod
    def widget(field, value, download_url=None, **attr):
        """
            Render a widget for the Field/value

            @param field: the Field
            @param value: the value
            @param download_url: the download URL for upload fields
            @param attr: the HTML attributes for the widget

            @note: upload fields currently not rendered because the
                   upload widget wouldn't render the current value,
                   hence pointless for merge
            @note: custom widgets must allow override of both _id
                   and _name attributes
        """

        widgets = SQLFORM.widgets
        ftype = str(field.type)

        if ftype == "id":
            inp = None
        elif ftype == "upload":
            inp = None
            #if field.widget:
                #inp = field.widget(field, value,
                                   #download_url=download_url, **attr)
            #else:
                #inp = widgets.upload.widget(field, value,
                                            #download_url=download_url, **attr)
        elif field.widget:
            if isinstance(field.widget, S3LocationSelectorWidget):
                # Workaround - location selector does not support
                # renaming of the fields => switch to dropdown
                level = None
                if value:
                    try:
                        level = s3db.gis_location[value].level
                    except:
                        pass
                widget = S3LocationDropdownWidget(level, value)
                field.requires = IS_EMPTY_OR(IS_ONE_OF(current.db, "gis_location.id"))
                inp = widget(field, value, **attr)
            else:
                inp = field.widget(field, value, **attr)
        elif ftype == "boolean":
            inp = widgets.boolean.widget(field, value, **attr)
        elif widgets.options.has_options(field):
            if not field.requires.multiple:
                inp = widgets.options.widget(field, value, **attr)
            else:
                inp = widgets.multiple.widget(field, value, **attr)
        elif ftype[:5] == "list:":
            inp = widgets.list.widget(field, value, **attr)
        elif ftype == "text":
            inp = widgets.text.widget(field, value, **attr)
        elif ftype == "password":
            inp = widgets.password.widget(field, value, **attr)
        elif ftype == "blob":
            inp = None
        else:
            ftype = ftype in widgets and ftype or "string"
            inp = widgets[ftype].widget(field, value, **attr)

        return inp

# END =========================================================================
