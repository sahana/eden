# -*- coding: utf-8 -*-

""" S3 Multi-Record Representations

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
"""

#from gluon import *
from gluon import current
from gluon.html import *
from gluon.storage import Storage
from gluon.dal import Expression, Field

from s3utils import s3_unicode

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
        lfields = []
        append = lfields.append
        heading = {}
        for field in rfields:
            selector = "%s.%s" % (field.tname, field.fname)
            append(selector)
            heading[selector] = (field.label)
        self.lfields = lfields
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

        def selectAction(orderby):
            if isinstance(orderby, tuple):
                for el in orderby:
                    selectAction(el)
            if isinstance(orderby, Field):
                extractField(orderby)
            elif isinstance(orderby, Expression):
                extractExpression(orderby)
            else:
                self.orderby.append([1, "asc"])

        def extractField(field):
            cnt = 0
            append = self.orderby.append
            s_field = str(field)
            for rfield in rfields:
                if s_field == rfield.colname:
                    append([cnt, "asc"])
                    break
                cnt += 1

        def extractExpression(exp):
            cnt = 0
            first = exp.first
            if isinstance(first, Field):
                s_first = str(first)
                op = exp.op
                INVERT = exp.db._adapter.INVERT
                append = self.orderby.append
                for rfield in rfields:
                    if s_first == rfield.colname:
                        if op == INVERT:
                            append([cnt, "desc"])
                        else:
                            append([cnt, "asc"])
                        break
                    cnt += 1
            else:
                extractExpression(first)
            if exp.second:
                selectAction(exp.second)

        self.orderby = []
        selectAction(orderby)

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

        flist = self.lfields

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
                     "lastJson": aadata}

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

        flist = self.lfields
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

            @param id: The unique dataTabel ID
            @param rfields: optional list of rfields
        """

        T = current.T
        s3 = current.response.s3
        request = current.request
        application = request.application

        # @todo: this needs rework
        #        - s3FormatRequest must remove the "search" method
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

        iconList = []
        formats = s3.formats
        export_formats = current.deployment_settings.get_ui_export_formats()
        if "pdf" in export_formats:
            url = formats.pdf if formats.pdf else default_url
            iconList.append(IMG(_src="/%s/static/img/pdficon_small.gif" % application,
                                _onclick="s3FormatRequest('pdf','%s','%s');" % (id, url),
                                _alt=T("Export in PDF format"),
                                _title=T("Export in PDF format"),
                                ))
        if "xls" in export_formats:
            url = formats.xls if formats.xls else default_url
            iconList.append(IMG(_src="/%s/static/img/icon-xls.png" % application,
                                _onclick="s3FormatRequest('xls','%s','%s');" % (id, url),
                                _alt=T("Export in XLS format"),
                                _title=T("Export in XLS format"),
                                ))
        if "rss" in export_formats:
            url = formats.rss if formats.rss else default_url
            iconList.append(IMG(_src="/%s/static/img/RSS_16.png" % application,
                                _onclick="s3FormatRequest('rss','%s','%s');" % (id, url),
                                _alt=T("Export in RSS format"),
                                _title=T("Export in RSS format"),
                                ))
        if "xml" in export_formats:
            url = formats.xml if formats.xml else default_url
            iconList.append(IMG(_src="/%s/static/img/icon-xml.png" % application,
                                _onclick="s3FormatRequest('xml','%s','%s');" % (id, url),
                                _alt=T("Export in XML format"),
                                _title=T("Export in XML format"),
                                ))

        div = DIV(_class='list_formats')
        if permalink is not None:
            link = A(T("Link to this result"),
                     _href=permalink,
                     _class="permalink")
            div.append(link)
            div.append(" | ")

        div.append(current.T("Export to:"))
        if "have" in formats and "have" in export_formats:
            iconList.append(IMG(_src="/%s/static/img/have_16.png" % application,
                                _onclick="s3FormatRequest('have','%s','%s');" % (id, formats.have),
                                _alt=T("Export in HAVE format"),
                                _title=T("Export in HAVE format"),
                                ))
        if "kml" in export_formats:
            if "kml" in formats:
                iconList.append(IMG(_src="/%s/static/img/kml_icon.png" % application,
                                    _onclick="s3FormatRequest('kml','%s','%s');" % (id, formats.kml),
                                    _alt=T("Export in KML format"),
                                    _title=T("Export in KML format"),
                                    ))
            elif rfields:
                kml_list = ["location_id",
                            "site_id",
                            ]
                for r in rfields:
                    if r.fname in kml_list:
                        iconList.append(IMG(_src="/%s/static/img/kml_icon.png" % application,
                                            _onclick="s3FormatRequest('kml','%s','%s');" % (id, default_url),
                                            _alt=T("Export in KML format"),
                                            _title=T("Export in KML format"),
                                            ))
                        break
        if "map" in formats and "map" in export_formats:
            iconList.append(IMG(_src="/%s/static/img/map_icon.png" % application,
                                _onclick="s3FormatRequest('map','%s','%s');" % (id, formats.map),
                                _alt=T("Show on map"),
                                _title=T("Show on map"),
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

        from gluon.serializers import json

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
                          _value=json(config)))
        # If we have a cache set up then pass it in
        if cache:
            form.append(INPUT(_type="hidden",
                              _id="%s_dataTable_cache" %id,
                              _name="cache",
                              _value=json(cache)))
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
            flist = self.lfields

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
            flist = self.lfields
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
    """ Class representing a data list (experimental) """

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
                 layout=None):
        """
            Constructor

            @param resource: the S3Resource
            @param list_fields: the list fields (list of field selector strings)
            @param records: the records
            @param listid: the HTML ID for this list
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

        self.start = start if start else 0
        self.limit = limit if limit else 0
        self.total = total if total else 0

    # ---------------------------------------------------------------------
    def html(self):
        """ Render list data as HTML (nested DIVs) """

        resource = self.resource
        list_fields = self.list_fields
        rfields = resource.resolve_selectors(list_fields)[0]

        render = self.layout
        
        records = self.records
        if records is not None:
            items = [
                DIV(current.T("Total Records: %(numrows)s") % {"numrows": self.total},
                    _class="dl-header",
                    _id="%s-header" % self.listid)
            ]
            for i in xrange(len(records)):
                _class = (i + self.start) % 2 and "even" or "odd"
                items.append(render(rfields, records[i], _class=_class))
        else:
            # template
            raise NotImplementedError

        listid = self.listid
        return DIV(items, _class = "dl", _id = listid)

    # ---------------------------------------------------------------------
    def json(self):
        """ Render list data as JSON (for Ajax pagination) """

        raise NotImplementedError

    # ---------------------------------------------------------------------
    def render(self, rfields, record, **attr):
        """
            Default item renderer

            @param rfields: the S3ResourceFields to render
            @param record: the record as dict
            @param attr: additional HTML attributes for the item
        """
        
        pkey = str(self.resource._id)

        # Construct the item ID
        listid = self.listid
        if pkey in record:
            item_id = "%s-%s" % (listid, record[pkey])
        else:
            # template
            item_id = "%s-[id]" % list_id

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

# END =========================================================================
