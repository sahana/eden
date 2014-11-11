# -*- coding: utf-8 -*-

""" S3 Record Merger

    @requires: U{B{I{gluon}} <http://web2py.com>}

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

from gluon import *
from gluon.dal import Field
#from gluon.html import BUTTON
from gluon.storage import Storage

from s3data import S3DataTable
from s3query import FS
from s3rest import S3Method
from s3utils import s3_get_foreign_key, s3_represent_value, s3_unicode
from s3validators import IS_ONE_OF
from s3widgets import *

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
                r.error(405, current.ERROR.BAD_METHOD)
        else:
            r.error(405, current.ERROR.BAD_METHOD)

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

        s3 = current.response.s3
        session_s3 = current.session.s3

        resource = self.resource
        tablename = self.tablename

        if r.http == "POST":
            return self.merge(r, **attr)

        # Bookmarks
        record_ids = []
        DEDUPLICATE = self.DEDUPLICATE
        if DEDUPLICATE in session_s3:
            bookmarks = session_s3[DEDUPLICATE]
            if tablename in bookmarks:
                record_ids = bookmarks[tablename]
        query = FS(resource._id.name).belongs(record_ids)
        resource.add_filter(query)

        # Representation
        representation = r.representation

        # List fields
        list_fields = resource.list_fields()

        # Start/Limit
        get_vars = r.get_vars
        if representation == "aadata":
            start = get_vars.get("displayStart", None)
            limit = get_vars.get("pageLength", None)
            draw = int(get_vars.draw or 0)
        else: # catch all
            start = 0
            limit = s3.ROWSPERPAGE
        if limit is not None:
            try:
                start = int(start)
                limit = int(limit)
            except ValueError:
                start = None
                limit = None # use default
        else:
            start = None # use default
        if s3.dataTable_pageLength:
            display_length = s3.dataTable_pageLength
        else:
            display_length = 25
        if limit is None:
            limit = 2 * display_length

        # Datatable Filter
        totalrows = None
        if representation == "aadata":
            searchq, orderby, left = resource.datatable_filter(list_fields,
                                                               get_vars)
            if searchq is not None:
                totalrows = resource.count()
                resource.add_filter(searchq)
        else:
            dt_sorting = {"iSortingCols": "1", "sSortDir_0": "asc"}
            if len(list_fields) > 1:
                dt_sorting["bSortable_0"] = "false"
                dt_sorting["iSortCol_0"] = "1"
            else:
                dt_sorting["bSortable_0"] = "true"
                dt_sorting["iSortCol_0"] = "0"
            orderby, left = resource.datatable_filter(list_fields,
                                                      dt_sorting)[1:]

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

        if representation == "aadata":
            output = dt.json(totalrows,
                             displayrows,
                             datatable_id,
                             draw,
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
                             dt_bulk_actions = [(T("Merge"),
                                                 "merge", "pair-action")],
                             dt_pageLength=display_length,
                             )

            output["items"] = items
            s3.actions = [{"label": str(T("View")),
                           "url": r.url(target="[id]", method="read"),
                           "_class": "action-btn",
                           },
                          ]

            if len(record_ids) < 2:
                output["add_btn"] = DIV(
                    SPAN(T("You need to have at least 2 records in this list in order to merge them."),
                         # @ToDo: Move to CSS
                         _style="float:left;padding-right:10px;"),
                    A(T("Find more"),
                      _href=r.url(method="", id=0, component_id=0, vars={}))
                )
            else:
                output["add_btn"] = DIV(
                    SPAN(T("Select 2 records from this list, then click 'Merge'.")),
                )

            s3.dataTableID = [datatable_id]
            current.response.view = self._view(r, "list.html")

        else:
            r.error(501, current.ERROR.BAD_FORMAT)

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
        mode = post_vars.get("mode")
        selected = post_vars.get("selected", "")
        selected = selected.split(",")
        if mode == "Inclusive":
            ids = selected
        elif mode == "Exclusive":
            ids = [i for i in record_ids if i not in selected]
        else:
            # Error
            ids = []
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
            r.error(404, current.ERROR.BAD_RECORD, next = r.url(id=0, vars={}))
        original = rows[0]
        duplicate = rows[1]

        # Prepare form construction
        formfields = [f for f in table if f.readable or f.writable]

        ORIGINAL, DUPLICATE, KEEP = self.ORIGINAL, self.DUPLICATE, self.KEEP
        keep_o = KEEP.o in post_vars and post_vars[KEEP.o]
        keep_d = KEEP.d in post_vars and post_vars[KEEP.d]

        trs = []
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
                    owidget = s3_represent_value(f, value=original[f])
                except:
                    owidget = s3_unicode(original[f])
            if keep_d or not any((keep_o, keep_d)):
                dwidget = self.widget(f, duplicate[f], _name=did, _id=did)
            else:
                try:
                    dwidget = s3_represent_value(f, value=duplicate[f])
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
                r.error(404, current.ERROR.BAD_RECORD)
            except:
                import sys
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
                self.next = r.url(method="", id=0, vars={})
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

        errors = current.s3db.onvalidation(tablename, data, method="update")
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
            if isinstance(field.widget, (S3LocationSelectorWidget, S3LocationSelectorWidget2)):
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

# =============================================================================
class S3RecordMerger(object):
    """ Record Merger """

    def __init__(self, resource):
        """
            Constructor

            @param resource: the resource
        """

        self.resource = resource

    # -------------------------------------------------------------------------
    @staticmethod
    def raise_error(msg, error=RuntimeError):
        """
            Roll back the current transaction and raise an error

            @param message: error message
            @param error: exception class to raise
        """

        current.db.rollback()
        raise error(msg)

    # -------------------------------------------------------------------------
    def update_record(self, table, id, row, data):

        form = Storage(vars = Storage([(f, row[f])
                              for f in table.fields if f in row]))
        form.vars.update(data)
        try:
            current.db(table._id==row[table._id]).update(**data)
        except Exception, e:
            self.raise_error("Could not update %s.%s" %
                            (table._tablename, id))
        else:
            s3db = current.s3db
            s3db.update_super(table, form.vars)
            current.auth.s3_set_record_owner(table, row[table._id], force_update=True)
            s3db.onaccept(table, form, method="update")
        return form.vars

    # -------------------------------------------------------------------------
    def delete_record(self, table, id, replaced_by=None):

        s3db = current.s3db

        if replaced_by is not None:
            replaced_by = {str(id): replaced_by}
        resource = s3db.resource(table, id=id)
        success = resource.delete(replaced_by=replaced_by,
                                  cascade=True)
        if not success:
            self.raise_error("Could not delete %s.%s (%s)" %
                            (resource.tablename, id, resource.error))
        return success

    # -------------------------------------------------------------------------
    def merge_realms(self, table, original, duplicate):
        """
            Merge the realms of two person entities (update all
            realm_entities in all records from duplicate to original)

            @param table: the table original and duplicate belong to
            @param original: the original record
            @param duplicate: the duplicate record
        """

        if "pe_id" not in table.fields:
            return

        original_pe_id = original["pe_id"]
        duplicate_pe_id = duplicate["pe_id"]

        db = current.db

        for t in db:
            if "realm_entity" in t.fields:

                query = (t.realm_entity == duplicate_pe_id)
                if "deleted" in t.fields:
                    query &= (t.deleted != True)
                try:
                    db(query).update(realm_entity = original_pe_id)
                except:
                    db.rollback()
                    raise
        return


    # -------------------------------------------------------------------------
    def fieldname(self, key):

        fn = None
        if "." in key:
            alias, fn = key.split(".", 1)
            if alias not in ("~", self.resource.alias):
                fn = None
        elif self.main:
            fn = key
        return fn

    # -------------------------------------------------------------------------
    def merge(self,
              original_id,
              duplicate_id,
              replace=None,
              update=None,
              main=True):
        """
            Merge a duplicate record into its original and remove the
            duplicate, updating all references in the database.

            @param original_id: the ID of the original record
            @param duplicate_id: the ID of the duplicate record
            @param replace: list fields names for which to replace the
                            values in the original record with the values
                            of the duplicate
            @param update: dict of {field:value} to update the final record
            @param main: internal indicator for recursive calls

            @status: work in progress
            @todo: de-duplicate components and link table entries

            @note: virtual references (i.e. non-SQL, without foreign key
                   constraints) must be declared in the table configuration
                   of the referenced table like:

                   s3db.configure(tablename, referenced_by=[(tablename, fieldname)])

                   This does not apply for list:references which will be found
                   automatically.

            @note: this method can only be run from master resources (in order
                   to find all components). To merge component records, you have
                   to re-define the component as a master resource.

            @note: CLI calls must db.commit()
        """

        self.main = main

        db = current.db
        resource = self.resource
        table = resource.table
        tablename = resource.tablename

        # Check for master resource
        if resource.parent:
            self.raise_error("Must not merge from component", SyntaxError)

        # Check permissions
        auth = current.auth
        has_permission = auth.s3_has_permission
        permitted = has_permission("update", table,
                                   record_id = original_id) and \
                    has_permission("delete", table,
                                   record_id = duplicate_id)
        if not permitted:
            self.raise_error("Operation not permitted", auth.permission.error)

        # Load all models
        s3db = current.s3db
        if main:
            s3db.load_all_models()
        if db._lazy_tables:
            # Must roll out all lazy tables to detect dependencies
            for tn in db._LAZY_TABLES.keys():
                db[tn]

        # Get the records
        original = None
        duplicate = None
        query = table._id.belongs([original_id, duplicate_id])
        if "deleted" in table.fields:
            query &= (table.deleted != True)
        rows = db(query).select(table.ALL, limitby=(0, 2))
        for row in rows:
            record_id = row[table._id]
            if str(record_id) == str(original_id):
                original = row
                original_id = row[table._id]
            elif str(record_id) == str(duplicate_id):
                duplicate = row
                duplicate_id = row[table._id]
        msg = "Record not found: %s.%s"
        if original is None:
            self.raise_error(msg % (tablename, original_id), KeyError)
        if duplicate is None:
            self.raise_error(msg % (tablename, duplicate_id), KeyError)

        # Find all single-components
        single = Storage()
        for alias in resource.components:
            component = resource.components[alias]
            if not component.multiple:
                single[component.tablename] = component

        # Is this a super-entity?
        is_super_entity = table._id.name != "id" and \
                          "instance_type" in table.fields

        # Find all references
        referenced_by = list(table._referenced_by)

        # Append virtual references
        virtual_references = s3db.get_config(tablename, "referenced_by")
        if virtual_references:
            referenced_by.extend(virtual_references)

        # Find and append list:references
        for t in db:
            for f in t:
                ftype = str(f.type)
                if ftype[:14] == "list:reference" and \
                   ftype[15:15+len(tablename)] == tablename:
                    referenced_by.append((t._tablename, f.name))

        update_record = self.update_record
        delete_record = self.delete_record
        fieldname = self.fieldname

        # Update all references
        define_resource = s3db.resource
        for referee in referenced_by:

            if isinstance(referee, Field):
                tn, fn = referee.tablename, referee.name
            else:
                tn, fn = referee

            se = s3db.get_config(tn, "super_entity")
            if is_super_entity and \
               (isinstance(se, (list, tuple)) and tablename in se or \
                se == tablename):
                # Skip instance types of this super-entity
                continue

            # Reference field must exist
            if tn not in db or fn not in db[tn].fields:
                continue

            rtable = db[tn]
            if tn in single:
                component = single[tn]
                if component.link is not None:
                    component = component.link

                if fn == component.fkey:
                    # Single component => must reduce to one record
                    join = component.get_join()
                    pkey = component.pkey
                    lkey = component.lkey or component.fkey

                    # Get the component records
                    query = (table[pkey] == original[pkey]) & join
                    osub = db(query).select(limitby=(0, 1)).first()
                    query = (table[pkey] == duplicate[pkey]) & join
                    dsub = db(query).select(limitby=(0, 1)).first()

                    ctable = component.table

                    if dsub is None:
                        # No duplicate => skip this step
                        continue
                    elif not osub:
                        # No original => re-link the duplicate
                        dsub_id = dsub[ctable._id]
                        data = {lkey: original[pkey]}
                        success = update_record(ctable, dsub_id, dsub, data)
                    elif component.linked is not None:
                        # Duplicate link => remove it
                        dsub_id = dsub[component.table._id]
                        delete_record(ctable, dsub_id)
                    else:
                        # Two records => merge them
                        osub_id = osub[component.table._id]
                        dsub_id = dsub[component.table._id]
                        cresource = define_resource(component.tablename)
                        cresource.merge(osub_id, dsub_id,
                                        replace=replace,
                                        update=update,
                                        main=False)
                    continue

            # Find the foreign key
            rfield = rtable[fn]
            ktablename, key, multiple = s3_get_foreign_key(rfield)
            if not ktablename:
                if str(rfield.type) == "integer":
                    # Virtual reference
                    key = table._id.name
                else:
                    continue

            # Find the referencing records
            if multiple:
                query = rtable[fn].contains(duplicate[key])
            else:
                query = rtable[fn] == duplicate[key]
            rows = db(query).select(rtable._id, rtable[fn])

            # Update the referencing records
            for row in rows:
                if not multiple:
                    data = {fn:original[key]}
                else:
                    keys = [k for k in row[fn] if k != duplicate[key]]
                    if original[key] not in keys:
                        keys.append(original[key])
                    data = {fn:keys}
                update_record(rtable, row[rtable._id], row, data)

        # Merge super-entity records
        super_entities = resource.get_config("super_entity")
        if super_entities is not None:

            if not isinstance(super_entities, (list, tuple)):
                super_entities = [super_entities]

            for super_entity in super_entities:

                super_table = s3db.table(super_entity)
                if not super_table:
                    continue
                superkey = super_table._id.name

                skey_o = original[superkey]
                if not skey_o:
                    msg = "No %s found in %s.%s" % (superkey,
                                                    tablename,
                                                    original_id)
                    current.log.warning(msg)
                    s3db.update_super(table, original)
                    skey_o = original[superkey]
                if not skey_o:
                    continue
                skey_d = duplicate[superkey]
                if not skey_d:
                    msg = "No %s found in %s.%s" % (superkey,
                                                    tablename,
                                                    duplicate_id)
                    current.log.warning(msg)
                    continue

                sresource = define_resource(super_entity)
                sresource.merge(skey_o, skey_d,
                                replace=replace,
                                update=update,
                                main=False)

        # Merge and update original data
        data = Storage()
        if replace:
            for k in replace:
                fn = fieldname(k)
                if fn and fn in duplicate:
                    data[fn] = duplicate[fn]
        if update:
            for k, v in update.items():
                fn = fieldname(k)
                if fn in table.fields:
                    data[fn] = v
        if len(data):
            r = None
            p = Storage([(fn, "__deduplicate_%s__" % fn)
                         for fn in data
                         if table[fn].unique and \
                            table[fn].type == "string" and \
                            data[fn] == duplicate[fn]])
            if p:
                r = Storage([(fn, original[fn]) for fn in p])
                update_record(table, duplicate_id, duplicate, p)
            update_record(table, original_id, original, data)
            if r:
                update_record(table, duplicate_id, duplicate, r)

        # Delete the duplicate
        if not is_super_entity:
            self.merge_realms(table, original, duplicate)
            delete_record(table, duplicate_id, replaced_by=original_id)

        # Success
        return True

# END =========================================================================
