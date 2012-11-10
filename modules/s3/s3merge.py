# -*- coding: utf-8 -*-

""" S3 Record Merger

    @requires: U{B{I{gluon}} <http://web2py.com>}

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

__all__ = ["S3Merge"]

from gluon import *
from gluon.storage import Storage
from s3rest import S3Method
from s3resource import S3FieldSelector
from s3utils import S3DataTable

# =============================================================================
class S3Merge(S3Method):
    """ Interactive Record Merger """

    DEDUPLICATE = "deduplicate"

    # -------------------------------------------------------------------------
    def apply_method(self, r, **attr):
        """
            Apply Merge methods

            @param r: the S3Request
            @param attr: dictionary of parameters for the method handler

            @returns: output object to send to the view
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
                    output = self.mark(r, **attr)
                else:
                    output = self.duplicates(r, **attr)
            elif r.http == "DELETE":
                output = self.unmark(r, **attr)
            else:
                r.error(405, r.ERROR.BAD_METHOD)
        #elif r.method == "merge":
            #if r.http in ("GET", "POST"):
                #output = self.merge(r, **attr)
            #else:
                #r.error(405, r.ERROR.BAD_METHOD)
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

        auth = current.auth
        system_roles = auth.get_system_roles()
        if not auth.s3_has_role(system_roles.ADMIN):
            return ""

        s3 = current.session.s3
        DEDUPLICATE = cls.DEDUPLICATE

        remove = DEDUPLICATE in s3 and \
                 tablename in s3[DEDUPLICATE] and \
                 str(record_id) in s3[DEDUPLICATE][tablename] and \
                 True or False

        mark = "mark-deduplicate action-btn"
        unmark = "unmark-deduplicate action-btn"

        if remove:
            mark += " hide"
        else:
            unmark += " hide"

        T = current.T
        link = DIV(A(T("Add to deduplication list"),
                       _class=mark),
                   A(T("Remove from deduplication list"),
                       _class=unmark),
                   A("",
                     _href=r.url(method="deduplicate",
                                 vars={}),
                     _id="markDuplicateURL",
                     _class="hide"),
                   _id="markDuplicate")

        return link

    # -------------------------------------------------------------------------
    def duplicates(self, r, **attr):
        # Get a list of all bookmarked records for this resource

        s3 = current.session.s3
        DEDUPLICATE = self.DEDUPLICATE

        output = dict()

        resource = self.resource
        tablename = self.tablename
        record_ids = []

        representation = r.representation

        if DEDUPLICATE in s3:
            bookmarks = s3[DEDUPLICATE]
            if tablename in bookmarks:
                record_ids = bookmarks[tablename]

        if r.http == "POST" and "selected" in r.post_vars:
            return self.merge(r, **attr)

        # Bookmarks
        query = S3FieldSelector(resource._id.name).belongs(record_ids)
        resource.add_filter(query)

        # List fields
        list_fields = self._config("list_fields", None)
        if not list_fields:
            list_fields = [f.name for f in resource.readable_fields()]
        #if list_fields[0] != self.table.fields[0]:
            #list_fields.insert(0, table.fields[0])

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
        totalrows = displayrows = resource.count()
        if representation == "aadata":
            searchq, orderby, left = resource.datatable_filter(list_fields,
                                                               vars)
            if searchq is not None:
                resource.add_filter(searchq)
                displayrows = resource.count(left=left, distinct=True)
        else:
            orderby, left = None, None

        # Retrieve the items
        rows = resource.select(list_fields,
                               start=start,
                               limit=limit,
                               orderby=orderby,
                               left=left)

        # Extract the data
        data = resource.extract(rows, list_fields, represent=True)

        # Generate a datatable
        rfields = resource.resolve_selectors(list_fields)[0]
        dt = S3DataTable(rfields, data)
        datatable_id = "s3merge_1"
        response = current.response

        if representation == "aadata":

            output = dt.json(totalrows,
                             displayrows,
                             datatable_id,
                             sEcho,
                             dt_bulk_actions = [(current.T("Merge"), "merge", "pair-action")])

        elif representation == "html":
            # Initial HTML response
            url = "/%s/%s/%s/deduplicate.aadata" % (r.application,
                                                  r.controller,
                                                  r.function)
            items =  dt.html(totalrows,
                             displayrows,
                             datatable_id,
                             dt_ajax_url=url,
                             dt_displayLength=display_length,
                             dt_bulk_actions = [(current.T("Merge"), "merge", "pair-action")])

            output["items"] = items

            response.s3.dataTableID = [datatable_id]
            response.view = self._view(r, "list.html")

        else:
            r.error(501, r.ERROR.BAD_FORMAT)

        return output

    # -------------------------------------------------------------------------
    def merge(self, r, **attr):

        if DEDUPLICATE in s3:
            bookmarks = s3[DEDUPLICATE]
            if tablename in bookmarks:
                record_ids = bookmarks[tablename]

        # Get/process the merge form for two records
        if "mode" in vars:
            mode = vars["mode"]

            if "selected" in vars:
                selected = vars["selected"]
            else:
                selected = []

            if mode == "Inclusive":
                items = selected
                print type(items)
            elif mode == "Exclusive":
                items = [i for i in record_ids if i not in selected]
            print "Get merge form for: %s" % str(items)
        else:
            # POST of the merge form
            print "Merge form submitted"

        return dict()

# END =========================================================================
