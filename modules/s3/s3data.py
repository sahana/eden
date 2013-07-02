# -*- coding: utf-8 -*-

""" S3 Data Views

    @copyright: 2009-2013 (c) Sahana Software Foundation
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

    @group Data Views: S3DataTable,
                       S3DataList,
                       S3PivotTable
"""

import datetime
import sys
import time

from itertools import product, islice

try:
    import json # try stdlib (Python 2.6)
except ImportError:
    try:
        import simplejson as json # try external module
    except:
        import gluon.contrib.simplejson as json # fallback to pure-Python module

from gluon import current
from gluon.dal import Expression, Field
from gluon.html import *
from gluon.storage import Storage
from gluon.validators import IS_EMPTY_OR, IS_IN_SET

from s3utils import s3_flatlist, s3_has_foreign_key, s3_truncate, s3_unicode, S3MarkupStripper
from s3validators import IS_NUMBER

DEBUG = False
if DEBUG:
    print >> sys.stderr, "S3 Data Representations: DEBUG MODE"
    def _debug(m):
        print >> sys.stderr, m
else:
    _debug = lambda m: None

# =============================================================================
class S3DataTable(object):
    """ Class representing a data table """

    # The dataTable id if no explicit value has been provided
    id_counter = 1
    
    # -------------------------------------------------------------------------
    # Standard API
    # -------------------------------------------------------------------------
    def __init__(self,
                 rfields,
                 data,
                 start=0,
                 limit=None,
                 filterString=None,
                 orderby=None,
                 ):
        """
            S3DataTable constructor

            @param rfields: A list of S3Resourcefield
            @param data: A list of Storages the key is of the form table.field
                         The value is the data to be displayed in the dataTable
            @param start: the first row to return from the data
            @param limit: the (maximum) number of records to return
            @param filterString: The string that was used in filtering the records
            @param orderby: the DAL orderby construct
        """

        self.data = data
        self.rfields = rfields

        colnames = []
        heading = {}
        
        append = colnames.append
        for rfield in rfields:
            colname = rfield.colname
            heading[colname] = rfield.label
            append(colname)
            
        self.colnames = colnames
        self.heading = heading
        
        max = len(data)
        if start < 0:
            start == 0
        if start > max:
            start = max
        if limit == None:
            end = max
        else:
            end = start + limit
            if end > max:
                end = max
        self.start = start
        self.end = end
        self.filterString = filterString

        if orderby:
            
            if isinstance(orderby, str):
                orderby_fields = orderby.split(",")
            elif not isinstance(orderby, (list, tuple)):
                orderby_fields = [orderby]
            else:
                orderby_fields = orderby
            orderby = []
            for orderby_field in orderby_fields:
                if type(orderby_field) is Expression:
                    f = orderby_field.first
                    if type(f) is Field and \
                       orderby_field.op == current.db._adapter.INVERT:
                        direction = "desc"
                    else:
                        continue
                    fname = str(f)
                elif type(orderby_field) is Field:
                    direction = "asc"
                    fname = str(orderby_field)
                elif isinstance(orderby_field, str):
                    fname, direction = (orderby_field.strip().split() + ["asc"])[:2]
                else:
                    continue
                idx = 0
                for rfield in rfields:
                    if rfield.colname == fname:
                        orderby.append([idx, direction])
                        break
                    idx += 1

        else:
            orderby = []
                    
        self.orderby = orderby

    # -------------------------------------------------------------------------
    def html(self,
             totalrows,
             filteredrows,
             id = None,
             sEcho = 1,
             **attr
             ):
        """
            Method to render the data into html

            @param totalrows: The total rows in the unfiltered query.
            @param filteredrows: The total rows in the filtered query.
            @param id: The id of the table these need to be unique if more
                       than one dataTable is to be rendered on the same page.
                           If this is not passed in then a unique id will be
                           generated. Regardless the id is stored in self.id
                           so it can be easily accessed after rendering.
            @param sEcho: An unaltered copy of sEcho sent from the client used
                          by dataTables as a draw count.
            @param attr: dictionary of attributes which can be passed in
        """

        flist = self.colnames

        if not id:
            id = "list_%s" % self.id_counter
            self.id_counter += 1
        self.id = id

        bulkActions = attr.get("dt_bulk_actions", None)
        bulkCol = attr.get("dt_bulk_col", 0)
        if bulkCol > len(flist):
            bulkCol = len(flist)
        action_col = attr.get("dt_action_col", 0)
        if action_col != 0:
            if action_col == -1 or action_col >= len(flist):
                action_col = len(flist) -1
                attr["dt_action_col"] = action_col
            flist = flist[1:action_col+1] + [flist[0]] + flist[action_col+1:]

        # Get the details for any bulk actions. If we have at least one bulk
        # action then a column will be added, either at the start or in the
        # column identified by dt_bulk_col
        if bulkActions:
            flist.insert(bulkCol, "BULK")
            if bulkCol <= action_col:
                action_col += 1

        pagination = attr.get("dt_pagination", "true") == "true"
        if pagination:
            real_end = self.end
            self.end = self.start + 1
        table = self.table(id, flist, action_col)
        cache = None
        if pagination:
            self.end = real_end
            aadata = self.aadata(totalrows,
                                 filteredrows,
                                 id,
                                 sEcho,
                                 flist,
                                 action_col=action_col,
                                 stringify=False,
                                 **attr)
            cache = {"iCacheLower": self.start,
                     "iCacheUpper": self.end if filteredrows > self.end else filteredrows,
                     "lastJson": aadata,
                     }

        html = self.htmlConfig(table,
                               id,
                               self.orderby,
                               self.rfields,
                               cache,
                               filteredrows,
                               **attr
                               )
        return html

    # -------------------------------------------------------------------------
    def json(self,
             totalrows,
             displayrows,
             id,
             sEcho,
             stringify=True,
             **attr
             ):
        """
            Method to render the data into a json object

            @param totalrows: The total rows in the unfiltered query.
            @param displayrows: The total rows in the filtered query.
            @param id: The id of the table for which this ajax call will
                       respond to.
            @param sEcho: An unaltered copy of sEcho sent from the client used
                          by dataTables as a draw count.
            @param attr: dictionary of attributes which can be passed in
                   dt_action_col: The column where the action buttons will be placed
                   dt_bulk_actions: list of labels for the bulk actions.
                   dt_bulk_col: The column in which the checkboxes will appear,
                                by default it will be the column immediately
                                before the first data item
                   dt_group_totals: The number of record in each group.
                                    This will be displayed in parenthesis
                                    after the group title.
        """

        flist = self.colnames
        action_col = attr.get("dt_action_col", 0)
        if action_col != 0:
            if action_col == -1 or action_col >= len(flist):
                action_col = len(flist) - 1
            flist = flist[1:action_col+1] + [flist[0]] + flist[action_col+1:]
        # Get the details for any bulk actions. If we have at least one bulk
        # action then a column will be added, either at the start or in the
        # column identified by dt_bulk_col
        bulkActions = attr.get("dt_bulk_actions", None)
        bulkCol = attr.get("dt_bulk_col", 0)
        if bulkActions:
            if bulkCol > len(flist):
                bulkCol = len(flist)
            flist.insert(bulkCol, "BULK")
            if bulkCol <= action_col:
                action_col += 1

        return self.aadata(totalrows,
                           displayrows,
                           id,
                           sEcho,
                           flist,
                           action_col=action_col,
                           stringify=stringify,
                           **attr)

    # -------------------------------------------------------------------------
    # Extended API
    # -------------------------------------------------------------------------
    @staticmethod
    def getConfigData():
        """
            Method to extract the configuration data from S3 globals and
            store them as an attr variable

            @return: dictionary of attributes which can be passed into html()

            @param attr: dictionary of attributes which can be passed in
                   dt_displayLength : The default number of records that will be shown
                   dt_pagination: Enable pagination
                   dt_pagination_type: type of pagination, either:
                                        (default) full_numbers
                                        OR two_button
                   dt_bFilter: Enable or disable filtering of data.
                   dt_group: The colum that is used to group the data
                   dt_ajax_url: The URL to be used for the Ajax call
                   dt_action_col: The column where the action buttons will be placed
                   dt_bulk_actions: list of labels for the bulk actions.
                   dt_bulk_col: The column in which the checkboxes will appear,
                                by default it will be the column immediately
                                before the first data item
                   dt_bulk_selected: A list of selected items
                   dt_actions: dictionary of actions
                   dt_styles: dictionary of styles to be applied to a list of ids
                              for example:
                              {"warning" : [1,3,6,7,9],
                               "alert" : [2,10,13]}
        """

        s3 = current.response.s3

        attr = Storage()
        if s3.datatable_ajax_source:
            attr.dt_ajax_url = s3.datatable_ajax_source
        if s3.actions:
            attr.dt_actions = s3.actions
        if s3.dataTableBulkActions:
            attr.dt_bulk_actions = s3.dataTableBulkActions
        if s3.dataTable_iDisplayLength:
            attr.dt_displayLength = s3.dataTable_iDisplayLength
        attr.dt_pagination = "false" if s3.no_sspag else "true"
        if s3.dataTable_sPaginationType:
            attr.dt_pagination_type = s3.dataTable_sPaginationType
        if s3.dataTable_group:
            attr.dt_group = s3.dataTable_group
        if s3.dataTable_NobFilter:
            attr.dt_bFilter = not s3.dataTable_NobFilter
        if s3.dataTable_sDom:
            attr.dt_sDom = s3.dataTable_sDom
        if s3.dataTableDisplay:
            attr.dt_display = s3.dataTableDisplay
        if s3.dataTableStyleDisabled or s3.dataTableStyleWarning or s3.dataTableStyleAlert:
            attr.dt_styles = {}
            if s3.dataTableStyleDisabled:
                attr.dt_styles["dtdisable"] = s3.dataTableStyleDisabled
            if s3.dataTableStyleWarning:
                attr.dt_styles["dtwarning"] = s3.dataTableStyleWarning
            if s3.dataTableStyleAlert:
                attr.dt_styles["dtalert"] = s3.dataTableStyleAlert
        return attr

    # -------------------------------------------------------------------------
    @staticmethod
    def getControlData(rfields, vars):
        """
            Method that will return the orderby and filter from the vars
            returned by the browser, from an ajax call.

            @param rfields: A list of S3Resourcefield
            @param vars: A list of variables sent from the dataTable
        """

        # @todo: does not sort properly in option fields nor FK references
        if not vars.iSortingCols:
            return (False, "")

        sort_cols = int(vars.iSortingCols)
        orderby = False
        for x in range(sort_cols):
            index = int(vars["iSortCol_%s" % x])
            f = rfields[index].field
            if vars["sSortDir_%s" % x] == "desc":
                f = ~f
            if not orderby:
                orderby = f
            else:
                orderby |= f
        # @todo: does not search properly in option fields nor FK references
        words = vars.sSearch
        if not words:
            return (orderby, "")
        words = words.split()
        query = None
        for rf in rfields:
            if rf.ftype in ("string", "text") :
                if not query:
                    query = rf.field.contains(words)
                else:
                    query |= (rf.field.contains(words))

        return (orderby, query)

    # -------------------------------------------------------------------------
    @staticmethod
    def listFormats(id, rfields=None, permalink=None):
        """
            Calculate the export formats that can be added to the table

            @param id: The unique dataTable ID
            @param rfields: optional list of rfields
        """

        T = current.T
        s3 = current.response.s3
        request = current.request

        # @todo: this needs rework
        #        - formatRequest must remove the "search" method
        #        - other data formats could have other list_fields,
        #          hence applying the datatable sorting/filters is
        #          not transparent
        if s3.datatable_ajax_source:
            end = s3.datatable_ajax_source.find(".aadata")
            default_url = s3.datatable_ajax_source[:end] # strip '.aadata' extension
        else:
            default_url = request.url

        # Keep any URL filters
        vars = request.get_vars
        if vars:
            default_url = "%s?" % default_url
            for var in vars:
                default_url = "%s%s=%s&" % (default_url, var, vars[var])

        div = DIV(_class='list_formats')
        if permalink is not None:
            link = A(T("Link to this result"),
                     _href=permalink,
                     _class="permalink")
            div.append(link)
            div.append(" | ")

        div.append("%s:" % current.T("Export to"))
        iconList = []
        formats = s3.formats
        export_formats = current.deployment_settings.get_ui_export_formats()
        EXPORT = T("Export in %(format)s format")

        # In reverse-order of appearance due to float-right
        if "map" in formats and "map" in export_formats:
            iconList.append(DIV(_class="export_map",
                                _onclick="S3.dataTables.formatRequest('map','%s','%s');" % (id, formats.map),
                                _title=T("Show on Map"),
                                ))
        if "kml" in export_formats:
            if "kml" in formats:
                iconList.append(DIV(_class="export_kml",
                                    _onclick="S3.dataTables.formatRequest('kml','%s','%s');" % (id, formats.kml),
                                    _title=EXPORT % dict(format="KML"),
                                    ))
            elif rfields:
                kml_list = ["location_id",
                            "site_id",
                            ]
                for r in rfields:
                    if r.fname in kml_list:
                        iconList.append(DIV(_class="export_kml",
                                            _onclick="S3.dataTables.formatRequest('kml','%s','%s');" % (id, default_url),
                                            _title=EXPORT % dict(format="KML"),
                                            ))
                        break
        if "have" in formats and "have" in export_formats:
            iconList.append(DIV(_class="export_have",
                                _onclick="S3.dataTables.formatRequest('have','%s','%s');" % (id, formats.have),
                                _title=EXPORT % dict(format="HAVE"),
                                ))
        if "xml" in export_formats:
            url = formats.xml if formats.xml else default_url
            iconList.append(DIV(_class="export_xml",
                                _onclick="S3.dataTables.formatRequest('xml','%s','%s');" % (id, url),
                                _title=EXPORT % dict(format="XML"),
                                ))
        if "rss" in export_formats:
            url = formats.rss if formats.rss else default_url
            iconList.append(DIV(_class="export_rss",
                                _onclick="S3.dataTables.formatRequest('rss','%s','%s');" % (id, url),
                                _title=EXPORT % dict(format="RSS"),
                                ))
        if "xls" in export_formats:
            url = formats.xls if formats.xls else default_url
            iconList.append(DIV(_class="export_xls",
                                _onclick="S3.dataTables.formatRequest('xls','%s','%s');" % (id, url),
                                _title=EXPORT % dict(format="XLS"),
                                ))
        if "pdf" in export_formats:
            url = formats.pdf if formats.pdf else default_url
            iconList.append(DIV(_class="export_pdf",
                                _onclick="S3.dataTables.formatRequest('pdf','%s','%s');" % (id, url),
                                _title=EXPORT % dict(format="PDF"),
                                ))

        for icon in iconList:
            div.append(icon)
        return div

    # -------------------------------------------------------------------------
    @staticmethod
    def defaultActionButtons(resource,
                             custom_actions=None,
                             r=None
                             ):
        """
            Configure default action buttons

            @param resource: the resource
            @param r: the request, if specified, all action buttons will
                      be linked to the controller/function of this request
                      rather than to prefix/name of the resource
            @param custom_actions: custom actions as list of dicts like
                                   {"label":label, "url":url, "_class":class},
                                   will be appended to the default actions
        """

        from s3crud import S3CRUD

        auth = current.auth
        actions = current.response.s3.actions

        table = resource.table
        actions = None
        has_permission = auth.s3_has_permission
        ownership_required = auth.permission.ownership_required

        labels = current.manager.LABEL
        args = ["[id]"]

        # Choose controller/function to link to
        if r is not None:
            c = r.controller
            f = r.function
        else:
            c = resource.prefix
            f = resource.name

        # "Open" button
        if has_permission("update", table) and \
           not ownership_required("update", table):
            update_url = URL(c=c, f=f, args=args + ["update"])
            S3CRUD.action_button(labels.UPDATE, update_url)
        else:
            read_url = URL(c=c, f=f, args=args)
            S3CRUD.action_button(labels.READ, read_url)
        # Delete action
        # @todo: does not apply selective action (renders DELETE for
        #        all items even if the user is only permitted to delete
        #        some of them) => should implement "restrict", see
        #        S3CRUD.action_buttons
        deletable = current.s3db.get_config(resource.tablename, "deletable",
                                            True)
        if deletable and \
           has_permission("delete", table) and \
           not ownership_required("delete", table):
            delete_url = URL(c=c, f=f, args = args + ["delete"])
            S3CRUD.action_button(labels.DELETE, delete_url)

        # Append custom actions
        if custom_actions:
            actions = actions + custom_actions if actions else custom_actions

    # -------------------------------------------------------------------------
    @staticmethod
    def htmlConfig(html,
                   id,
                   orderby,
                   rfields = None,
                   cache = None,
                   filteredrows = None,
                   **attr
                   ):
        """
            Method to wrap the html for a dataTable in a form, the list of formats
            used for data export and add the config details required by dataTables,

            @param html: The html table
            @param id: The id of the table
            @param orderby: the sort details see aaSort at http://datatables.net/ref
            @param rfields: The list of resource fields
            @param attr: dictionary of attributes which can be passed in
                   dt_lengthMenu: The menu options for the number of records to be shown
                   dt_displayLength : The default number of records that will be shown
                   dt_sDom : The Datatable DOM initialisation variable, describing
                             the order in which elements are displayed.
                             See http://datatables.net/ref for more details.
                   dt_pagination : Is pagination enabled, dafault 'true'
                   dt_pagination_type : How the pagination buttons are displayed
                   dt_bFilter: Enable or disable filtering of data.
                   dt_ajax_url: The URL to be used for the Ajax call
                   dt_action_col: The column where the action buttons will be placed
                   dt_bulk_actions: list of labels for the bulk actions.
                   dt_bulk_col: The column in which the checkboxes will appear,
                                by default it will be the column immediately
                                before the first data item
                   dt_group: The column(s) that is(are) used to group the data
                   dt_group_totals: The number of record in each group.
                                    This will be displayed in parenthesis
                                    after the group title.
                   dt_group_titles: The titles to be used for each group.
                                    These are a list of lists with the inner list
                                    consisting of two values, the repr from the
                                    db and the label to display. This can be more than
                                    the actual number of groups (giving an empty group).
                   dt_group_space: Insert a space between the group heading and the next group
                   dt_bulk_selected: A list of selected items
                   dt_actions: dictionary of actions
                   dt_styles: dictionary of styles to be applied to a list of ids
                              for example:
                              {"warning" : [1,3,6,7,9],
                               "alert" : [2,10,13]}
                   dt_text_maximum_len: The maximum length of text before it is condensed
                   dt_text_condense_len: The length displayed text is condensed down to
                   dt_shrink_groups: If set then the rows within a group will be hidden
                                     two types are supported, 'individulal' and 'accordion'
                   dt_group_types: The type of indicator for groups that can be 'shrunk'
                                   Permitted valies are: 'icon' (the default) 'text' and 'none'
            @global current.response.s3.actions used to get the RowActions
        """

        from gluon.serializers import json as jsons

        request = current.request
        s3 = current.response.s3

        dataTableID = s3.dataTableID
        if not dataTableID or not isinstance(dataTableID, list):
            dataTableID = s3.dataTableID = [id]
        elif id not in dataTableID:
            dataTableID.append(id)
        # The configuration parameter from the server to the client will be
        # sent in a json object stored in an hidden input field. This object
        # will then be parsed by s3.dataTable.js and the values used.
        config = Storage()
        config.id = id
        config.lengthMenu = attr.get("dt_lengthMenu",
                                     [[ 25, 50, -1], [ 25, 50, str(current.T("All"))]]
                                     )
        config.displayLength = attr.get("dt_displayLength",
                                        current.manager.ROWSPERPAGE)
        config.sDom = attr.get("dt_sDom", 'fril<"dataTable_table"t>pi')
        config.pagination = attr.get("dt_pagination", "true")
        config.paginationType = attr.get("dt_pagination_type", "full_numbers")
        config.bFilter = attr.get("dt_bFilter", "true")
        config.ajaxUrl = attr.get("dt_ajax_url", URL(c=request.controller,
                                                     f=request.function,
                                                     extension="aadata",
                                                     args=request.args,
                                                     vars=request.get_vars,
                                                     ))
        config.rowStyles = attr.get("dt_styles", [])


        rowActions = s3.actions
        if rowActions:
            config.rowActions = rowActions
        else:
            config.rowActions = []
        bulkActions = attr.get("dt_bulk_actions", None)
        if bulkActions and not isinstance(bulkActions, list):
            bulkActions = [bulkActions]
        config.bulkActions = bulkActions
        config.bulkCol = bulkCol = attr.get("dt_bulk_col", 0)
        action_col = attr.get("dt_action_col", 0)
        if bulkActions and bulkCol <= action_col:
            action_col += 1
        config.actionCol = action_col
        group_list = attr.get("dt_group", [])
        if not isinstance(group_list, list):
            group_list = [group_list]
        dt_group = []
        for group in group_list:
            if bulkActions and bulkCol <= group:
                group += 1
            if action_col >= group:
                group -= 1
            dt_group.append([group, "asc"])
        config.group = dt_group
        config.groupTotals = attr.get("dt_group_totals", [])
        config.groupTitles = attr.get("dt_group_titles", [])
        config.groupSpacing = attr.get("dt_group_space", "false")
        for order in orderby:
            if bulkActions:
                if bulkCol <= order[0]:
                    order[0] += 1
            if action_col >= order[0]:
                order[0] -= 1
        config.aaSort = orderby
        config.textMaxLength = attr.get("dt_text_maximum_len", 80)
        config.textShrinkLength = attr.get("dt_text_condense_len", 75)
        config.shrinkGroupedRows = attr.get("dt_shrink_groups", "false")
        config.groupIcon = attr.get("dt_group_types", [])
        # Wrap the table in a form and add some data in hidden fields
        form = FORM()
        if not s3.no_formats and len(html) > 0:
            permalink = attr.get("dt_permalink", None)
            form.append(S3DataTable.listFormats(id, rfields,
                                                permalink=permalink))
        form.append(html)
        # Add the configuration details for this dataTable
        form.append(INPUT(_type="hidden",
                          _id="%s_configurations" % id,
                          _name="config",
                          _value=jsons(config)))
        # If we have a cache set up then pass it in
        if cache:
            form.append(INPUT(_type="hidden",
                              _id="%s_dataTable_cache" %id,
                              _name="cache",
                              _value=jsons(cache)))
        # If we have bulk actions then add the hidden fields
        if config.bulkActions:
            form.append(INPUT(_type="hidden",
                              _id="%s_dataTable_bulkMode" % id,
                              _name="mode",
                              _value="Inclusive"))
            bulk_selected = attr.get("dt_bulk_selected", "")
            if isinstance(bulk_selected, list):
                bulk_selected = ",".join(bulk_selected)
            form.append(INPUT(_type="hidden",
                              _id="%s_dataTable_bulkSelection" % id,
                              _name="selected",
                              _value="[%s]" % bulk_selected))
        return form

    # -------------------------------------------------------------------------
    # Helper methods
    # -------------------------------------------------------------------------
    def table(self, id, flist=None, action_col=0):
        """
            Method to render the data as an html table. This is of use if
            and html table is required without the dataTable goodness. However
            if you want html for a dataTable then use the html() method

            @param id: The id of the table
            @param flist: The list of fields
            @param action_col: The column where action columns will be displayed
                               (this is required by dataTables)
        """

        data = self.data
        heading = self.heading
        start = self.start
        end = self.end
        if not flist:
            flist = self.colnames

        # Build the header row
        header = THEAD()
        tr = TR()
        for field in flist:
            if field == "BULK":
                tr.append(TH(""))
            else:
                tr.append(TH(heading[field]))
        header.append(tr)

        body = TBODY()
        if data:
            # Build the body rows (the actual data)
            rc = 0
            for i in xrange(start, end):
                row = data[i]
                if rc % 2 == 0:
                    _class = "even"
                else:
                    _class = "odd"
                rc += 1
                tr = TR(_class=_class)
                for field in flist:
                    # Insert a checkbox for bulk select
                    if field == "BULK":
                        tr.append(TD(INPUT(_id="select%s" % row[flist[action_col]],
                                           _type="checkbox",
                                           _class="bulkcheckbox",
                                           )))
                    else:
                        tr.append(TD(row[field]))
                body.append(tr)
        table = TABLE([header, body], _id=id, _class="dataTable display")
        return table

    # -------------------------------------------------------------------------
    def aadata(self,
               totalrows,
               displayrows,
               id,
               sEcho,
               flist,
               stringify=True,
               action_col=None,
               **attr
               ):
        """
            Method to render the data into a json object

            @param totalrows: The total rows in the unfiltered query.
            @param displayrows: The total rows in the filtered query.
            @param id: The id of the table for which this ajax call will
                       respond to.
            @param sEcho: An unaltered copy of sEcho sent from the client used
                          by dataTables as a draw count.
            @param flist: The list of fields
            @param attr: dictionary of attributes which can be passed in
                   dt_action_col: The column where the action buttons will be placed
                   dt_bulk_actions: list of labels for the bulk actions.
                   dt_bulk_col: The column in which the checkboxes will appear,
                                by default it will be the column immediately
                                before the first data item
                   dt_group_totals: The number of record in each group.
                                    This will be displayed in parenthesis
                                    after the group title.
        """

        data = self.data
        if not flist:
            flist = self.colnames
        start = self.start
        end = self.end
        if action_col is None:
            action_col = attr.get("dt_action_col", 0)
        structure = {}
        aadata = []
        for i in xrange(start, end):
            row = data[i]
            details = []
            for field in flist:
                if field == "BULK":
                    details.append("<INPUT id='select%s' type='checkbox' class='bulkcheckbox'>" % \
                        row[flist[action_col]])
                else:
                    details.append(s3_unicode(row[field]))
            aadata.append(details)
        structure["dataTable_id"] = id
        structure["dataTable_filter"] = self.filterString
        structure["dataTable_groupTotals"] = attr.get("dt_group_totals", [])
        structure["dataTable_sort"] = self.orderby
        structure["aaData"] = aadata
        structure["iTotalRecords"] = totalrows
        structure["iTotalDisplayRecords"] = displayrows
        structure["sEcho"] = sEcho
        if stringify:
            from gluon.serializers import json
            return json(structure)
        else:
            return structure

# =============================================================================
class S3DataList(object):
    """ Class representing a data list """

    # -------------------------------------------------------------------------
    # Standard API
    # -------------------------------------------------------------------------
    def __init__(self,
                 resource,
                 list_fields,
                 records,
                 start=None,
                 limit=None,
                 total=None,
                 listid=None,
                 layout=None,
                 row_layout=None):
        """
            Constructor

            @param resource: the S3Resource
            @param list_fields: the list fields (list of field selector strings)
            @param records: the records
            @param start: index of the first item
            @param limit: maximum number of items
            @param total: total number of available items
            @param listid: the HTML ID for this list
            @param layout: item renderer (optional) as
                           function(listid, resource, rfields, record)
            @param row_layout: row renderer (optional) as
                               function(listid, resource, rowsize, items)
        """

        self.resource = resource
        self.list_fields = list_fields
        self.records = records

        if listid is None:
            self.listid = "datalist"
        else:
            self.listid = listid

        if layout is not None:
            self.layout = layout
        else:
            self.layout = self.render
        self.row_layout = row_layout

        self.start = start if start else 0
        self.limit = limit if limit else 0
        self.total = total if total else 0

    # ---------------------------------------------------------------------
    def html(self,
             start=None,
             limit=None,
             pagesize=None,
             rowsize=None,
             ajaxurl=None):
        """
            Render list data as HTML (nested DIVs)

            @param start: index of the first item (in this page)
            @param limit: (actual) number of items (in this page)
            @param pagesize: maximum number of items per page
            @param rowsize: number of items per row
            @param ajaxurl: the URL to Ajax-update the datalist
        """

        T = current.T
        resource = self.resource
        list_fields = self.list_fields
        rfields = resource.resolve_selectors(list_fields)[0]

        listid = self.listid
        render = self.layout
        render_row = self.row_layout

        if not rowsize:
            rowsize = 1
        
        records = self.records
        if records is not None:
            items = [
                DIV(T("Total Records: %(numrows)s") % {"numrows": self.total},
                    _class="dl-header",
                    _id="%s-header" % listid)
            ]
            
            row_idx = int(self.start / rowsize) + 1
            for group in self.groups(records, rowsize):
                row = []
                col_idx = 0
                for record in group:
                    item = render(listid,
                                  resource,
                                  rfields,
                                  record)
                    if hasattr(item, "add_class"):
                        _class = "dl-item dl-%s-cols dl-col-%s" % (rowsize, col_idx)
                        item.add_class(_class)
                    row.append(item)
                    col_idx += 1

                _class = "dl-row %s" % ((row_idx % 2) and "even" or "odd")
                if render_row:
                    row = render_row(listid,
                                     resource,
                                     rowsize,
                                     row)
                    if hasattr(row, "add_class"):
                        row.add_class(_class)
                else:
                    row = DIV(row, _class=_class)

                items.append(row)
                row_idx += 1
        else:
            # template
            raise NotImplementedError

        dl = DIV(items, _class = "dl", _id = listid)

        dl_data = {"startindex": start,
                   "maxitems": limit,
                   "totalitems": self.total,
                   "pagesize": pagesize,
                   "rowsize": rowsize,
                   "ajaxurl": ajaxurl
                   }
        from gluon.serializers import json as jsons
        dl_data = jsons(dl_data)
        dl.append(DIV(
                    FORM(
                        INPUT(_type="hidden",
                              _class="dl-pagination",
                              _value=dl_data)),
                    A(T("more..."),
                      _href=ajaxurl,
                      _class="dl-pagination"),
                    _class="dl-navigation"))

        return dl

    # ---------------------------------------------------------------------
    @staticmethod
    def groups(iterable, length):
        """
            Iterator to group data list items into rows

            @param iterable: the items iterable
            @param length: the number of items per row
        """

        iterable = iter(iterable)
        group = list(islice(iterable, length))
        while group:
            yield group
            group = list(islice(iterable, length))
        raise StopIteration
            
    # ---------------------------------------------------------------------
    @staticmethod
    def render(listid, resource, rfields, record, **attr):
        """
            Default item renderer

            @param listid: the HTML ID for this list
            @param resource: the S3Resource to render
            @param rfields: the S3ResourceFields to render
            @param record: the record as dict
            @param attr: additional HTML attributes for the item
        """

        pkey = str(resource._id)

        # Construct the item ID
        if pkey in record:
            item_id = "%s-%s" % (listid, record[pkey])
        else:
            # template
            item_id = "%s-[id]" % listid

        # Add classes passed from caller (e.g. even/odd)
        item_class = "dl-item"
        caller_class = attr.get("_class", None)
        if caller_class:
            item_class = "%s %s" % (item_class, caller_class)

        # Render the item
        item = DIV(_class=item_class, _id=item_id)
        for rfield in rfields:

            if not rfield.show:
                continue

            colname = rfield.colname
            if colname == pkey or colname not in record:
                continue
            value = record[colname]
            value_id = "%s-%s" % (item_id, rfield.colname.replace(".", "_"))

            table_class = "%s-tbl-%s" % (listid, rfield.tname)
            field_class = "%s-fld-%s" % (listid, rfield.fname)

            label = LABEL("%s:" % rfield.label,
                          _for = value_id,
                          _class = "dl-field-label")
            item.append(DIV(label,
                            DIV(value,
                                _class = "dl-field-value",
                                _id = value_id),
                            _class = "dl-field %s %s" % (table_class,
                                                         field_class)))

        return item

# =============================================================================
class S3PivotTable(object):
    """ Class representing a pivot table of a resource """

    #: Supported aggregation methods
    METHODS = {"list": "List",
               "count": "Count",
               "min": "Minimum",
               "max": "Maximum",
               "sum": "Total",
               "avg": "Average",
               #"std": "Standard Deviation"
               }

    def __init__(self, resource, rows, cols, layers, strict=True):
        """
            Constructor - extracts all unique records, generates a
            pivot table from them with the given dimensions and
            computes the aggregated values for each cell.

            @param resource: the S3Resource
            @param rows: field selector for the rows dimension
            @param cols: field selector for the columns dimension
            @param layers: list of tuples of (field selector, method)
                           for the value aggregation(s)
            @param strict: filter out dimension values which don't match
                           the resource filter
        """

        # Initialize ----------------------------------------------------------
        #
        if not rows and not cols:
            raise SyntaxError("No rows or columns specified for pivot table")

        self.resource = resource

        self.lfields = None
        self.dfields = None
        self.rfields = None

        self.rows = rows
        self.cols = cols
        self.layers = layers

        # API variables -------------------------------------------------------
        #
        self.records = None
        """ All records in the pivot table as a Storage like:
                {
                 <record_id>: <Row>
                }
        """

        self.empty = False
        """ Empty-flag (True if no records could be found) """
        self.numrows = None
        """ The number of rows in the pivot table """
        self.numcols = None
        """ The number of columns in the pivot table """

        self.cell = None
        """ Array of pivot table cells in [rows[columns]]-order, each
            cell is a Storage like:
                {
                 records: <list_of_record_ids>,
                 (<fact>, <method>): <aggregated_value>, ...per layer
                }
        """
        self.row = None
        """ List of row headers, each header is a Storage like:
                {
                 value: <dimension value>,
                 records: <list_of_record_ids>,
                 (<fact>, <method>): <total value>, ...per layer
                }
        """
        self.col = None
        """ List of column headers, each header is a Storage like:
                {
                 value: <dimension value>,
                 records: <list_of_record_ids>,
                 (<fact>, <method>): <total value>, ...per layer
                }
        """
        self.totals = Storage()
        """ The grand total values for each layer, as a Storage like:
                {
                 (<fact>, <method): <total value>, ...per layer
                }
        """

        # Get the fields ------------------------------------------------------
        #
        tablename = resource.tablename

        # The "report_fields" table setting defines which additional
        # fields shall be included in the report base layer. This is
        # useful to provide easy access to the record data behind a
        # pivot table cell.
        fields = current.s3db.get_config(tablename, "report_fields", [])

        self._get_fields(fields=fields)
        rows = self.rows
        cols = self.cols

        if DEBUG:
            _start = datetime.datetime.now()
            _debug("S3PivotTable %s starting" % tablename)

        # Retrieve the records ------------------------------------------------
        #
        data = resource.fast_select(self.rfields.keys(), limit=None)
        drows = data["rows"]
        if drows:

            key = str(resource.table._id)
            records = Storage([(i[key], i) for i in drows])
                
            # Generate the data frame -----------------------------------------
            #
            gfields = self.gfields
            pkey_colname = gfields[self.pkey]
            rows_colname = gfields[rows]
            cols_colname = gfields[cols]

            if strict:
                rfields = self.rfields
                axes = (rfield
                        for rfield in (rfields[rows], rfields[cols])
                        if rfield != None)
                axisfilter = resource.axisfilter(axes)
            else:
                axisfilter = None
                
            dataframe = []
            insert = dataframe.append
            expand = self._expand

            for _id in records:
                row = records[_id]
                item = {key: _id}
                if rows_colname:
                    item[rows_colname] = row[rows_colname]
                if cols_colname:
                    item[cols_colname] = row[cols_colname]
                dataframe.extend(expand(item, axisfilter=axisfilter))
                
            self.records = records

            #if DEBUG:
                #duration = datetime.datetime.now() - _start
                #duration = '{:.2f}'.format(duration.total_seconds())
                #_debug("Dataframe complete after %s seconds" % duration)
                
            # Group the records -----------------------------------------------
            #
            matrix, rnames, cnames = self._pivot(dataframe,
                                                 pkey_colname,
                                                 rows_colname,
                                                 cols_colname)

            #if DEBUG:
                #duration = datetime.datetime.now() - _start
                #duration = '{:.2f}'.format(duration.total_seconds())
                #_debug("Pivoting complete after %s seconds" % duration)
                
            # Initialize columns and rows -------------------------------------
            #
            if cols:
                self.col = [Storage({"value": v}) for v in cnames]
                self.numcols = len(self.col)
            else:
                self.col = [Storage({"value": None})]
                self.numcols = 1

            if rows:
                self.row = [Storage({"value": v}) for v in rnames]
                self.numrows = len(self.row)
            else:
                self.row = [Storage({"value": None})]
                self.numrows = 1

            # Add the layers --------------------------------------------------
            #
            add_layer = self._add_layer
            layers = list(self.layers)
            for f, m in self.layers:
                add_layer(matrix, f, m)

            #if DEBUG:
                #duration = datetime.datetime.now() - _start
                #duration = '{:.2f}'.format(duration.total_seconds())
                #_debug("Layers complete after %s seconds" % duration)

        else:
            # No items to report on -------------------------------------------
            #
            self.empty = True

        if DEBUG:
            duration = datetime.datetime.now() - _start
            duration = '{:.2f}'.format(duration.total_seconds())
            _debug("S3PivotTable completed in %s seconds" % duration)

    # -------------------------------------------------------------------------
    # API methods
    # -------------------------------------------------------------------------
    def __len__(self):
        """ Total number of records in the report """

        items = self.records
        if items is None:
            return 0
        else:
            return len(self.records)

    # -------------------------------------------------------------------------
    def html(self,
             show_totals=True,
             url=None,
             filter_query=None,
             **attributes):
        """
            Render this pivot table as HTML

            @param show_totals: show totals for rows and columns
            @param url: link cells to this base-URL
            @param filter_query: use this S3ResourceQuery with the base-URL
            @param attributes: the HTML attributes for the table
        """

        T = current.T
        TOTAL = T("Total")

        components = []

        layers = self.layers
        resource = self.resource
        tablename = resource.tablename

        cols = self.cols
        rows = self.rows
        numcols = self.numcols
        numrows = self.numrows
        rfields = self.rfields

        get_label = self._get_field_label
        get_total = self._totals

        # Representation methods
        represent_method = self._represent_method
        cols_repr = represent_method(cols)
        rows_repr = represent_method(rows)
        layers_repr = dict([(f, represent_method(f)) for f, m in layers])

        layer_label = None
        col_titles = []
        add_col_title = col_titles.append
        col_totals = []
        add_col_total = col_totals.append
        row_titles = []
        add_row_title = row_titles.append
        row_totals = []
        add_row_total = row_totals.append

        # Layer titles:

        # Get custom labels from report options
        layer_labels = Storage()
        report_options = resource.get_config("report_options", None)
        if report_options and "fact" in report_options:
            layer_opts = report_options["fact"]
            for item in layer_opts:
                if isinstance(item, (tuple, list)) and len(item) == 3:
                    if not "." in item[0].split("$")[0]:
                        item = ("%s.%s" % (resource.alias, item[0]),
                                item[1],
                                item[2])
                    layer_labels[(item[0], item[1])] = item[2]

        labels = []
        get_mname = self._get_method_label

        for layer in layers:
            if layer in layer_labels:
                # Custom label
                label = layer_labels[layer]
                if not labels:
                    layer_label = label
                labels.append(s3_unicode(label))
            else:
                # Construct label from field-label and method
                label = get_label(rfields, layer[0], tablename, "fact")
                mname = get_mname(layer[1])
                if not labels:
                    m = layer[1] == "list" and get_mname("count") or mname
                    layer_label = "%s (%s)" % (label, m)
                labels.append("%s (%s)" % (label, mname))

        layers_title = TH(" / ".join(labels))

        # Columns field title
        if cols:
            col_label = get_label(rfields, cols, tablename, "cols")
            _colspan = numcols + 1
        else:
            col_label = ""
            _colspan = numcols
        cols_title = TH(col_label, _colspan=_colspan, _scope="col")

        titles = TR(layers_title, cols_title)

        # Sort dimensions:

        cells = self.cell

        # Sort rows
        rvals = self.row
        rows_list = []
        for i in xrange(numrows):
            row = rvals[i]
            # Add representation value of the row header
            row["text"] = rows_repr(row.value)
            rows_list.append((row, cells[i]))
        self._sortdim(rows_list, rfields[rows], 0)

        # Sort columns
        cvals = self.col
        cols_list = []
        for j in xrange(numcols):
            column = cvals[j]
            column["text"] = cols_repr(column.value)
            cols_list.append((column, j))
        self._sortdim(cols_list, rfields[cols], 0)

        # Build the column headers:

        # Header for the row-titles column
        row_label = get_label(rfields, rows, tablename, "rows")
        rows_title = TH(row_label, _scope="col")
        headers = TR(rows_title)

        add_header = headers.append

        # Headers for the cell columns
        for j in xrange(numcols):
            v = cols_list[j][0].text
            add_col_title(s3_truncate(unicode(v)))
            colhdr = TH(v, _scope="col")
            add_header(colhdr)

        # Header for the row-totals column
        if show_totals and cols is not None:
            add_header(TH(TOTAL, _class="totals_header rtotal", _scope="col"))

        thead = THEAD(titles, headers)

        # Render the table body:
        tbody = TBODY()
        add_row = tbody.append

        # Lookup table for cell list values
        cell_lookup_table = {} # {{}, {}}
        cell_vals = Storage()

        for i in xrange(numrows):

            # Initialize row
            _class = i % 2 and "odd" or "even"
            tr = TR(_class=_class)
            add_cell = tr.append

            # Row header
            row = rows_list[i][0]
            v = row["text"]
            add_row_title(s3_truncate(unicode(v)))
            rowhdr = TD(v)
            add_cell(rowhdr)

            row_cells = rows_list[i][1]

            # Result cells
            for j in xrange(numcols):

                cell_idx = cols_list[j][1]
                cell = row_cells[cell_idx]

                vals = []
                cell_ids = []
                add_value = vals.append
                for layer_idx, layer in enumerate(layers):
                    f, m = layer
                    represent = layers_repr[f]
                    value = cell[layer]
                    if m == "list":
                        if isinstance(value, list):
                            l = [represent(v) for v in value]
                        elif value is None:
                            l = ["-"]
                        else:
                            if type(value) in (int, float):
                                l = IS_NUMBER.represent(value)
                            else:
                                l = unicode(value)
                        #add_value(", ".join(l))
                        add_value(UL([LI(v) for v in l]))
                    else:
                        if type(value) in (int, float):
                            add_value(IS_NUMBER.represent(value))
                        else:
                            add_value(unicode(value))

                    layer_ids = []
                    layer_values = cell_lookup_table.get(layer_idx, {})

                    if m == "count":

                        rfield = rfields[f]
                        field = rfield.field
                        colname = rfield.colname
                        has_fk = field is not None and s3_has_foreign_key(field)
                        for id in cell.records:

                            record = self.records[id]
                            try:
                                fvalue = record[colname]
                            except AttributeError:
                                fvalue = None

                            if fvalue is not None:
                                if has_fk:
                                    if type(fvalue) is not list:
                                        fvalue = [fvalue]
                                    # list of foreign keys
                                    for fk in fvalue:
                                        if fk is not None and fk not in layer_ids:
                                            layer_ids.append(int(fk))
                                            if fk not in layer_values:
                                                layer_values[fk] = s3_unicode(field.represent(fk))
                                else:
                                    if type(fvalue) is not list:
                                        fvalue = [fvalue]
                                    for val in fvalue:
                                        if val is not None:
                                            if val not in cell_vals:
                                                next_id = len(cell_vals)
                                                cell_vals[val] = next_id
                                                layer_ids.append(next_id)
                                                layer_values[next_id] = s3_unicode(represent(val))
                                            else:
                                                prev_id = cell_vals[val]
                                                if prev_id not in layer_ids:
                                                    layer_ids.append(prev_id)
                                                    
                        layer_ids.sort(key=lambda i: layer_values[i])

                    cell_ids.append(layer_ids)
                    cell_lookup_table[layer_idx] = layer_values

                vals = [DIV(v, _class="report-cell-value") for v in vals]
                if any(cell_ids):
                    cell_attr = {"_data-records": cell_ids}
                    vals.append(DIV(_class="report-cell-zoom"))
                else:
                    cell_attr = {}
                add_cell(TD(vals, **cell_attr))

            # Row total
            totals = get_total(row, layers, append=add_row_total)
            if show_totals and cols is not None:
                add_cell(TD(totals))

            add_row(tr)

        # Table footer:
        i = numrows
        _class = i % 2 and "odd" or "even"
        _class = "%s %s" % (_class, "totals_row")
        col_total = TR(_class=_class)
        add_total = col_total.append
        add_total(TH(TOTAL, _class="totals_header", _scope="row"))

        # Column totals
        for j in xrange(numcols):
            cell_idx = cols_list[j][1]
            col = self.col[cell_idx]
            totals = get_total(col, layers, append=add_col_total)
            add_total(TD(IS_NUMBER.represent(totals)))

        # Grand total
        if cols is not None:
            grand_totals = get_total(self.totals, layers)
            add_total(TD(grand_totals))
        tfoot = TFOOT(col_total)

        # Wrap up:
        append = components.append
        append(thead)
        append(tbody)
        if show_totals:
            append(tfoot)

        # Chart data:
        layer_label = s3_unicode(layer_label)
        BY = s3_unicode(T("by"))
        row_label = "%s %s" % (BY, s3_unicode(row_label))
        if col_label:
            col_label = "%s %s" % (BY, s3_unicode(col_label))
        if filter_query and hasattr(filter_query, "serialize_url"):
            filter_vars = filter_query.serialize_url(resource=self.resource)
        else:
            filter_vars = {}
        hide_opts = current.deployment_settings.get_ui_hide_report_options()
        json_data = json.dumps(dict(t=layer_label,
                                    x=col_label,
                                    y=row_label,
                                    r=self.rows,
                                    c=self.cols,
                                    d=self.compact(maxrows=50,
                                                   maxcols=30,
                                                   represent=True),
                                    u=url,
                                    f=filter_vars,
                                    h=hide_opts,
                                    cell_lookup_table=cell_lookup_table))
        self.report_data = Storage(row_label=row_label,
                                   col_label=col_label,
                                   layer_label=layer_label,
                                   json_data=json_data)

        return TABLE(components, **attributes)

    # -------------------------------------------------------------------------
    def json(self,
             layer=None,
             maxrows=None,
             maxcols=None,
             least=False,
             url=None,
             represent=True):
        """
            Render the pivot table data as JSON-serializable dict

            @param layer: the layer
            @param maxrows: maximum number of rows (None for all)
            @param maxcols: maximum number of columns (None for all)
            @param least: render the least n rows/columns rather than
                          the top n (with maxrows/maxcols)
            @param represent: represent values

            {
                labels: {
                    layer:
                    rows:
                    cols:
                    total:
                },
                cells: [rows[cols]],
                rows: [rows[index, value, label, total]],
                cols: [cols[index, value, label, total]],
                
                total: <grand total>,
                filter: [url, rows selector, cols selector]
            }
        """

        rfields = self.rfields
        resource = self.resource

        tablename = resource.tablename

        T = current.T
        OTHER = "__other__"

        # The layer
        if layer is None:
            layer = self.layers[0]
        field, method = layer
        rows_dim = self.rows
        cols_dim = self.cols

        # The data
        orows = []
        ocols = []
        ocells = []
        lookup = {}

        if not self.empty:
            
            if method == "min":
                least = not least
            numeric = lambda x: isinstance(x, (int, long, float))

            hmethod = "sum" if method in ("list", "count") else method

            if represent:
                row_repr = self._represent_method(rows_dim)
                col_repr = self._represent_method(cols_dim)
            else:
                row_repr = col_repr = lambda v: s3_unicode(v)

            others = s3_unicode(current.T("Others"))

            irows = self.row
            icols = self.col
            rows = []
            cols = []

            rtail = (None, None)
            ctail = (None, None)
            
            # Group and sort the rows
            is_numeric = None
            for i in xrange(self.numrows):
                irow = irows[i]
                total = irow[layer]
                if is_numeric is None:
                    is_numeric = numeric(total)
                if not is_numeric:
                    total = len(irow.records)
                header = Storage(value = irow.value,
                                 text = irow.text if "text" in irow
                                                  else row_repr(irow.value))
                rows.append((i, total, header))
                
            if maxrows is not None:
                rtail = self._tail(rows, maxrows, least=least, method=hmethod)
            self._sortdim(rows, rfields[rows_dim])
            if rtail[1] is not None:
                rows.append((OTHER, rtail[1], Storage(value=None, text=others)))
            row_indices = [i[0] for i in rows]

            # Group and sort the cols
            is_numeric = None
            for i in xrange(self.numcols):
                icol = icols[i]
                total = icol[layer]
                if is_numeric is None:
                    is_numeric = numeric(total)
                if not is_numeric:
                    total = len(icol["records"])
                header = Storage(value = icol.value,
                                text = icol.text if "text" in icol
                                                 else col_repr(icol.value))
                cols.append((i, total, header))
            if maxcols is not None:
                ctail = self._tail(cols, maxcols, least=least, method=hmethod)
            self._sortdim(cols, rfields[cols_dim])
            if ctail[1] is not None:
                cols.append((OTHER, ctail[1], Storage(value=None, text=others)))
            col_indices = [i[0] for i in cols]

            rothers = rtail[0] or []
            cothers = ctail[0] or []

            # Group and sort the cells
            icell = self.cell
            cells = {}
            for i in xrange(self.numrows):
                irow = icell[i]
                ridx = (i, OTHER) if rothers and i in rothers else (i,)
                    
                for j in xrange(self.numcols):
                    cell = irow[j]
                    cidx = (j, OTHER) if cothers and j in cothers else (j,)

                    cell_records = cell["records"]
                    items = cell[layer]
                    value = items if is_numeric \
                                  else len(cell_records)
                                  
                    for ri in ridx:
                        if ri not in cells:
                            orow = cells[ri] = {}
                        else:
                            orow = cells[ri]
                        for ci in cidx:
                            if ci not in orow:
                                ocell = orow[ci] = {}
                                if OTHER in (ci, ri):
                                    ocell["value"] = [value]
                                    ocell["items"] = [items]
                                else:
                                    ocell["value"] = value
                                    ocell["items"] = items
                                ocell["records"] = cell_records
                            else:
                                ocell = orow[ci]
                                ocell["value"].append(value)
                                ocell["items"].append(items)
                                ocell["records"].extend(cell_records)

            # Aggregate the grouped values
            ctotals = True
            value_map = {}
            rappend = orows.append
            cappend = ocols.append
            for rindex, rtotal, rtitle in rows:
                orow = []
                rval = s3_unicode(rtitle.value) \
                       if rtitle.value is not None and rindex != OTHER else None
                if represent:
                    rappend((rindex,
                             rindex in rothers,
                             rtotal,
                             rval,
                             rtitle.text))
                else:
                    rappend((rindex,
                             rindex in rothers,
                             rtotal,
                             rval))
                for cindex, ctotal, ctitle in cols:
                    cell = cells[rindex][cindex]
                    items = cell["items"]
                    value = cell["value"]
                    cell_records = cell["records"]
                    if type(value) is list:
                        value = self._aggregate(value, hmethod)
                    if method == "list":
                        if type(items) is list:
                            items = [item for item in s3_flatlist(items)
                                          if item is not None]
                    else:
                        items = value
                        
                    # Build a lookup table for field values if counting
                    if method == "count":
                        keys = []
                        rfield = rfields[field]
                        f = rfield.field
                        has_fk = f is not None and s3_has_foreign_key(f)
                        if has_fk:
                            represent = f.represent
                        else:
                            represent = self._represent_method(field)
                        for record_id in cell_records:
                            record = self.records[record_id]
                            try:
                                fvalue = record[rfield.colname]
                            except AttributeError:
                                continue
                            if fvalue is None:
                                continue
                            if type(fvalue) is not list:
                                fvalue = [fvalue]
                            for v in fvalue:
                                if v is None:
                                    continue
                                if has_fk:
                                    if v not in keys:
                                        keys.append(v)
                                    if v not in lookup:
                                        lookup[v] = s3_unicode(represent(v))
                                else:
                                    if v not in value_map:
                                        next_id = len(value_map)
                                        value_map[v] = next_id
                                        keys.append(next_id)
                                        lookup[next_id] = s3_unicode(represent(v))
                                    else:
                                        prev_id = value_map[v]
                                        if prev_id not in keys:
                                            keys.append(prev_id)
                        keys.sort(key=lambda i: lookup[i])
                    else:
                        keys = None
                        
                    orow.append({"keys": keys,
                                 "items": items,
                                 "value": value})
                    if ctotals:
                        cval = s3_unicode(ctitle.value) \
                               if ctitle.value is not None and cindex != OTHER else None
                        if represent:
                            cappend((cindex,
                                     cindex in cothers,
                                     ctotal,
                                     cval,
                                     ctitle.text))
                        else:
                            cappend((cindex,
                                     cindex in cothers,
                                     ctotal,
                                     cval))
                ctotals = False
                ocells.append(orow)

        output = {"rows": orows,
                  "cols": ocols,
                  "cells": ocells,
                  "lookup": lookup if lookup else None,
                  "total": self._totals(self.totals, [layer]),
                  "nodata": None if not self.empty else str(T("No data available"))}

        # Lookup labels
        get_label = self._get_field_label
        get_mname = self._get_method_label

        labels = {
                  "total": str(T("Total")),
                  "none": str(current.messages["NONE"]),
                  "per": str(T("per")),
                  "breakdown": str(T("Breakdown")),
                 }

        # Layer title
        layer_title = None
        report_options = resource.get_config("report_options", None)

        # @todo: move this lookup into S3Report2
        if report_options and "fact" in report_options:
            # Custom label from report options?
            for item in report_options["fact"]:
                if isinstance(item, (tuple, list)) and len(item) == 3:
                    selector = item[0]
                    if not "." in selector.split("$")[0]:
                        selector = "%s.%s" % (resource.alias, item[0])
                    if selector == field and item[1] == method:
                        layer_title= item[3]
                        break
        if layer_title is None:
            # Construct label from field and method
            fname = get_label(rfields, field, tablename, "fact")
            mname = get_mname(method)
            layer_title = "%s (%s)" % (fname, mname)
        labels["layer"] = layer_title

        # Rows title
        if rows_dim:
            labels["rows"] = str(get_label(rfields,
                                           rows_dim,
                                           tablename,
                                           "rows"))
        else:
            labels["rows"] = ""

        # Columns title
        if cols_dim:
            labels["cols"] = str(get_label(rfields,
                                           cols_dim,
                                           tablename,
                                           "cols"))
        else:
            labels["cols"] = ""

        output["labels"] = labels

        # Filter-URL and axis selectors
        prefix = resource.prefix_selector
        output["filter"] = (str(url) if url else None,
                            prefix(rows_dim) if rows_dim else None,
                            prefix(cols_dim) if cols_dim else None)

        # @todo: add the record layer

        return output
        
    # -------------------------------------------------------------------------
    def compact(self,
                maxrows=50,
                maxcols=50,
                layer=None,
                least=False,
                represent=False):
        """
            Get the top/least n numeric results for a layer, used to
            generate the input data for charts.

            @param n: maximum dimension size, extracts the n-1 top/least
                      rows/cols and aggregates the rest under "__other__"
            @param layer: the layer
            @param least: use the least n instead of the top n results
            @param represent: represent the row/col dimension values as
                              strings using the respective field
                              representation
        """

        default = {"rows": [], "cols": [], "cells": []}

        if self.empty or layer and layer not in self.layers:
            return default
        elif not layer:
            layer = self.layers[0]

        method = layer[-1]
        if method == "min":
            least = not least
        numeric = lambda x: isinstance(x, (int, long, float))

        rfields = self.rfields
        OTHER = "__other__"

        if represent:
            row_repr = self._represent_method(self.rows)
            col_repr = self._represent_method(self.cols)
        else:
            row_repr = col_repr = lambda v: s3_unicode(v)

        others = s3_unicode(current.T("Others"))

        irows = self.row
        icols = self.col
        rows = []
        cols = []

        # Group and sort the rows
        is_numeric = None
        for i in xrange(self.numrows):
            r = irows[i]
            total = r[layer]
            if is_numeric is None:
                is_numeric = numeric(total)
            if not is_numeric:
                total = len(r["records"])
            header = Storage(value = r.value,
                             text = r.text
                                    if "text" in r else row_repr(r.value))
            rows.append((i, total, header))
        if maxrows is not None:
            rows = self._top(rows, maxrows,
                             least=least, method=method, other=OTHER)
        last = rows.pop(-1) if rows[-1][0] == OTHER else None
        self._sortdim(rows, rfields[self.rows])
        if last:
            last = (last[0], last[1], Storage(value=None, text=others))
            rows.append(last)
        row_indices = [i[0] for i in rows]

        # Group and sort the cols
        is_numeric = None
        for i in xrange(self.numcols):
            c = icols[i]
            total = c[layer]
            if is_numeric is None:
                is_numeric = numeric(total)
            if not is_numeric:
                total = len(c["records"])
            header = Storage(value = c.value,
                             text = c.text
                                    if "text" in c else col_repr(c.value))
            cols.append((i, total, header))
        if maxcols is not None:
            cols = self._top(cols, maxcols,
                             least=least, method=method, other=OTHER)
        last = cols.pop(-1) if cols[-1][0] == OTHER else None
        self._sortdim(cols, rfields[self.cols])
        if last:
            last = (last[0], last[1], Storage(value=None, text=others))
            cols.append(last)
        col_indices = [i[0] for i in cols]

        # Group and sort the cells
        icell = self.cell
        cells = {}
        for i in xrange(self.numrows):
            irow = icell[i]
            ridx = i if i in row_indices else OTHER
            if ridx not in cells:
                orow = cells[ridx] = {}
            else:
                orow = cells[ridx]
            for j in xrange(self.numcols):
                cell = irow[j]
                cidx = j if j in col_indices else OTHER
                value = cell[layer] if is_numeric else len(cell["records"])
                if cidx not in orow:
                    orow[cidx] = [value] if cidx == OTHER or ridx == OTHER else value
                else:
                    orow[cidx].append(value)

        # Aggregate the grouped values
        orows = []
        ocols = []
        ocells = []
        ctotals = True
        rappend = orows.append
        cappend = ocols.append
        for ri, rt, rh in rows:
            orow = []
            if represent:
                rappend((ri, s3_unicode(rh.value), rh.text, rt))
            else:
                rappend((ri, s3_unicode(rh.value), rt))
            for ci, ct, ch in cols:
                value = cells[ri][ci]
                if type(value) is list:
                    value = self._aggregate(value, method)
                orow.append(value)
                if ctotals:
                    if represent:
                        cappend((ci, s3_unicode(ch.value), ch.text, ct))
                    else:
                        cappend((ci, s3_unicode(ch.value), ct))
            ctotals = False
            ocells.append(orow)

        return {"rows": orows, "cols": ocols, "cells": ocells}

    # -------------------------------------------------------------------------
    # Internal methods
    # -------------------------------------------------------------------------
    def _pivot(self, items, pkey_colname, rows_colname, cols_colname):
        """
            2-dimensional pivoting of a list of unique items

            @param items: list of unique items as dicts
            @param pkey_colname: column name of the primary key
            @param rows_colname: column name of the row dimension
            @param cols_colname: column name of the column dimension

            @return: tuple of (cell matrix, row headers, column headers),
                     where cell matrix is a 2-dimensional array [rows[columns]]
                     and row headers and column headers each are lists (in the
                     same order as the cell matrix)
        """

        rvalues = Storage()
        cvalues = Storage()
        cells = Storage()

        # All unique rows values
        rindex = 0
        cindex = 0
        for item in items:

            rvalue = item[rows_colname] if rows_colname else None
            cvalue = item[cols_colname] if cols_colname else None

            if rvalue not in rvalues:
                r = rvalues[rvalue] = rindex
                rindex += 1
            else:
                r = rvalues[rvalue]
            if cvalue not in cvalues:
                c = cvalues[cvalue] = cindex
                cindex += 1
            else:
                c = cvalues[cvalue]

            if (r, c) not in cells:
                cells[(r, c)] = [item[pkey_colname]]
            else:
                cells[(r, c)].append(item[pkey_colname])

        matrix = []
        for r in xrange(len(rvalues)):
            row = []
            for c in xrange(len(cvalues)):
                row.append(cells[(r, c)])
            matrix.append(row)

        rnames = [None] * len(rvalues)
        for k, v in rvalues.items():
            rnames[v] = k

        cnames = [None] * len(cvalues)
        for k, v in cvalues.items():
            cnames[v] = k

        return matrix, rnames, cnames

    # -------------------------------------------------------------------------
    def _add_layer(self, matrix, fact, method):
        """
            Compute an aggregation layer, updates:

                - self.cell: the aggregated values per cell
                - self.row: the totals per row
                - self.col: the totals per column
                - self.totals: the overall totals per layer

            @param matrix: the cell matrix
            @param fact: the fact field
            @param method: the aggregation method
        """

        if method not in self.METHODS:
            raise SyntaxError("Unsupported aggregation method: %s" % method)

        items = self.records
        rfields = self.rfields
        rows = self.row
        cols = self.col
        records = self.records
        extract = self._extract
        aggregate = self._aggregate
        resource = self.resource

        RECORDS = "records"
        VALUES = "values"

        table = resource.table
        pkey = table._id.name

        if method is None:
            method = "list"
        layer = (fact, method)

        numcols = len(self.col)
        numrows = len(self.row)

        # Initialize cells
        if self.cell is None:
            self.cell = [[Storage()
                          for i in xrange(numcols)]
                         for j in xrange(numrows)]
        cells = self.cell

        all_values = []
        for r in xrange(numrows):

            # Initialize row header
            row = rows[r]
            row[RECORDS] = []
            row[VALUES] = []

            row_records = row[RECORDS]
            row_values = row[VALUES]

            for c in xrange(numcols):

                # Initialize column header
                col = cols[c]
                if RECORDS not in col:
                    col[RECORDS] = []
                col_records = col[RECORDS]
                if VALUES not in col:
                    col[VALUES] = []
                col_values = col[VALUES]

                # Get the records
                cell = cells[r][c]
                if RECORDS in cell and cell[RECORDS] is not None:
                    ids = cell[RECORDS]
                else:
                    data = matrix[r][c]
                    if data:
                        remove = data.remove
                        while None in data:
                            remove(None)
                        ids = data
                    else:
                        ids = []
                    cell[RECORDS] = ids
                row_records.extend(ids)
                col_records.extend(ids)

                # Get the values
                if fact is None:
                    fact = pkey
                    values = ids
                    row_values = row_records
                    col_values = row_records
                    all_values = records.keys()
                else:
                    values = []
                    append = values.append
                    for i in ids:
                        value = extract(records[i], fact)
                        if value is None:
                            continue
                        append(value)
                    values = list(s3_flatlist(values))
                    if method in ("list", "count"):
                        values =  list(set(values))
                    row_values.extend(values)
                    col_values.extend(values)
                    all_values.extend(values)

                # Aggregate values
                value = aggregate(values, method)
                cell[layer] = value

            # Compute row total
            row[layer] = aggregate(row_values, method)
            del row[VALUES]

        # Compute column total
        for c in xrange(numcols):
            col = cols[c]
            col[layer] = aggregate(col[VALUES], method)
            del col[VALUES]

        # Compute overall total
        self.totals[layer] = aggregate(all_values, method)
        return

    # -------------------------------------------------------------------------
    @staticmethod
    def _aggregate(values, method):
        """
            Compute an aggregation of a list of atomic values

            @param values: the values as list
            @param method: the aggregation method
        """

        if values is None:
            return None

        if method is None or method == "list":
            if values:
                return values
            else:
                return None

        elif method == "count":
            return len([v for v in values if v is not None])

        elif method == "min":
            try:
                return min(values)
            except (TypeError, ValueError):
                return None

        elif method == "max":
            try:
                return max(values)
            except (TypeError, ValueError):
                return None

        elif method == "sum":
            try:
                return sum(values)
            except (TypeError, ValueError):
                return None

        elif method in ("avg"):
            try:
                if len(values):
                    return sum(values) / float(len(values))
                else:
                    return 0.0
            except (TypeError, ValueError):
                return None

        #elif method == "std":
            #import numpy
            #if not values:
                #return 0.0
            #try:
                #return numpy.std(values)
            #except (TypeError, ValueError):
                #return None

        else:
            return None

    # -------------------------------------------------------------------------
    @staticmethod
    def _sortdim(items, rfield, index=2):
        """
            Sort a dimension (sorts items in-place)

            @param items: the items as list of tuples
                          (index, total, {value: value, text: text})
            @param rfield: the dimension (S3ResourceField)
            @param index: alternative index of the value/text dict
                          within each item
        """

        if not rfield:
            return
        ftype = rfield.ftype
        sortby = "value"
        if ftype == "integer":
            requires = rfield.requires
            if isinstance(requires, (tuple, list)):
                requires = requires[0]
            if isinstance(requires, IS_EMPTY_OR):
                requires = requires.other
            if isinstance(requires, IS_IN_SET):
                sortby = "text"
        elif ftype[:9] == "reference":
            sortby = "text"
        items.sort(key=lambda item: item[index][sortby])
        return

    # -------------------------------------------------------------------------
    def _top(self, items, length=10, least=False, method=None, other="__other__"):
        """
            Find the top/least <length> items (by total)

            @param items: the items as list of tuples
                          (index, total, {value: value, text: text})
            @param length: the number of items
            @param least: find least rather than top
        """

        try:
            if len(items) > length:
                m = length - 1
                l = list(items)
                l.sort(lambda x, y: int(y[1]-x[1]))
                if least:
                    l.reverse()
                ts = (other, self._aggregate([t[1] for t in l[m:]], method))
                l = l[:m] + [ts]
                return l
        except (TypeError, ValueError):
            pass
        return items

    # -------------------------------------------------------------------------
    @classmethod
    def _tail(cls, items, length=10, least=False, method=None):
        """
            Find the top/least <length> items (by total)

            @param items: the items as list of tuples
                          (index, total, {value: value, text: text})
            @param length: the number of items
            @param least: find least rather than top
        """

        try:
            if len(items) > length:
                l = list(items)
                l.sort(lambda x, y: int(y[1]-x[1]))
                if least:
                    l.reverse()
                tail = dict((item[0], item[1]) for item in l[length-1:])
                return (tail.keys(),
                        cls._aggregate(tail.values(), method))
        except (TypeError, ValueError):
            pass
        return (None, None)

    # -------------------------------------------------------------------------
    def _get_fields(self, fields=None):
        """
            Determine the fields needed to generate the report

            @param fields: fields to include in the report (all fields)
        """

        resource = self.resource
        table = resource.table

        # Lambda to prefix all field selectors
        alias = resource.alias
        def prefix(s):
            if isinstance(s, (tuple, list)):
                return prefix(s[-1])
            if "." not in s.split("$", 1)[0]:
                return "%s.%s" % (alias, s)
            elif s[:2] == "~.":
                return "%s.%s" % (alias, s[2:])
            else:
                return s

        self.pkey = pkey = prefix(table._id.name)
        self.rows = rows = self.rows and prefix(self.rows) or None
        self.cols = cols = self.cols and prefix(self.cols) or None

        if not fields:
            fields = []

        # dfields (data-fields): fields to generate the layers
        dfields = [prefix(s) for s in fields]
        if rows and rows not in dfields:
            dfields.append(rows)
        if cols and cols not in dfields:
            dfields.append(cols)
        if pkey not in dfields:
            dfields.append(pkey)
        for i in xrange(len(self.layers)):
            f, m = self.layers[i]
            s = prefix(f)
            self.layers[i] = (s, m)
            if s not in dfields:
                dfields.append(f)
        self.dfields = dfields

        # rfields (resource-fields): dfields resolved into a ResourceFields map
        rfields, joins, left, distinct = resource.resolve_selectors(dfields)
        rfields = Storage([(f.selector.replace("~", alias), f) for f in rfields])
        self.rfields = rfields

        # gfields (grouping-fields): fields to group the records by
        self.gfields = {pkey: rfields[pkey].colname,
                        rows: rfields[rows].colname if rows else None,
                        cols: rfields[cols].colname if cols else None}
        return

    # -------------------------------------------------------------------------
    def _represent_method(self, field):
        """
            Get the representation method for a field in the report

            @param field: the field selector
        """

        rfields = self.rfields
        default = lambda value: None

        if field and field in rfields:

            rfield = rfields[field]

            if rfield.field:
                def repr_method(value):
                    return current.manager.represent(rfield.field, value,
                                                     strip_markup=True)

            elif rfield.virtual:
                stripper = S3MarkupStripper()
                def repr_method(val):
                    if val is None:
                        return "-"
                    text = s3_unicode(val)
                    if "<" in text:
                        stripper.feed(text)
                        return stripper.stripped() # = totally naked ;)
                    else:
                        return text
            else:
                repr_method = default
        else:
            repr_method = default

        return repr_method

    # -------------------------------------------------------------------------
    @staticmethod
    def _totals(values, layers, append=None):
        """
            Get the totals of a row/column/report

            @param values: the values dictionary
            @param layers: the layers
            @param append: callback to collect the totals for JSON data
                           (currently only collects the first layer)
        """

        totals = []
        for layer in layers:
            f, m = layer
            value = values[layer]

            if m == "list":
                value = value and len(value) or 0
            if not len(totals) and append is not None:
                append(value)
            totals.append(s3_unicode(IS_NUMBER.represent(value)))
        totals = " / ".join(totals)
        return totals

    # -------------------------------------------------------------------------
    def _extract(self, row, field):
        """
            Extract a field value from a DAL row

            @param row: the row
            @param field: the fieldname (list_fields syntax)
        """

        rfields = self.rfields
        if field not in rfields:
            raise KeyError("Invalid field name: %s" % field)
        rfield = rfields[field]
        try:
            return rfield.extract(row)
        except AttributeError:
            return None

    # -------------------------------------------------------------------------
    def _expand(self, row, axisfilter=None):
        """
            Expand a data frame row into a list of rows for list:type values

            @param row: the row
            @param field: the field to expand (None for all fields)
            @param axisfilter: dict of filtered field values by column names
        """

        pairs = []
        append = pairs.append
        for colname in self.gfields.values():
            if not colname:
                continue
            else:
                value = row[colname]
            if type(value) is list:
                if axisfilter and colname in axisfilter:
                    p = [(colname, v) for v in value
                                       if v in axisfilter[colname]]
                    if not p:
                        raise RuntimeError("record does not match query")
                    else:
                        append(p)
                else:
                    append([(colname, v) for v in value])
            else:
                append([(colname, value)])
        result = [dict(i) for i in product(*pairs)]
        return result

    # -------------------------------------------------------------------------
    @staticmethod
    def _get_field_label(rfields, field, tablename, key):
        """
            Get the label for a field

            @param rfields: the list fields map
            @param key: the configuration key
        """

        DEFAULT = ""

        if field in rfields:
            rfield = rfields[field]
        else:
            return DEFAULT

        # @todo: cleanup this:
        get_config = lambda key, default, tablename=tablename: \
                     current.s3db.get_config(tablename, key, default)
        list_fields = get_config("list_fields", None)
        fields = get_config(key, list_fields)

        if fields:
            for f in fields:
                if isinstance(f, (tuple, list)) and f[1] == rfield.selector:
                    return f[0]

        if rfield:
            if rfield.ftype == "id":
                return current.T("Records")
            return rfield.label
        else:
            return DEFAULT

    # -------------------------------------------------------------------------
    @classmethod
    def _get_method_label(cls, code):
        """
            Get a label for a method

            @param code: the method code
            @return: the label (lazyT), or None for unsupported methods
        """

        methods = cls.METHODS

        if code is None:
            code = "list"
        if code in methods:
            return current.T(methods[code])
        else:
            return None

# END =========================================================================
