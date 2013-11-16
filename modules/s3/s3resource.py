# -*- coding: utf-8 -*-

""" S3 Data Objects API

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

    @group Resource API: S3Resource,
                         S3ResourceField,
                         S3FieldSelector
    @group Filter API: S3URLQuery,
                       S3ResourceQuery,
                       S3ResourceFilter
    @group Helper Classes: S3RecordMerger,
                           S3TypeConverter
"""

import collections
import datetime
import re
import sys
import time

from itertools import product, chain, groupby

try:
    from cStringIO import StringIO # Faster, where available
except:
    from StringIO import StringIO

try:
    from lxml import etree
except ImportError:
    print >> sys.stderr, "ERROR: lxml module needed for XML handling"
    raise

try:
    import json # try stdlib (Python 2.6)
except ImportError:
    try:
        import simplejson as json # try external module
    except:
        import gluon.contrib.simplejson as json # fallback to pure-Python module

from gluon import *
# Here are dependencies listed for reference:
#from gluon.dal import Field
#from gluon.globals import current
#from gluon.html import A, DIV, URL
#from gluon.http import HTTP, redirect
#from gluon.validators import IS_EMPTY_OR, IS_NOT_IN_DB, IS_DATE, IS_TIME
from gluon.dal import Row, Rows, Table, Field, Expression
from gluon.storage import Storage
from gluon.tools import callback

from s3data import S3DataTable, S3DataList, S3PivotTable
from s3fields import S3Represent, S3RepresentLazy, s3_all_meta_field_names
from s3utils import s3_has_foreign_key, s3_flatlist, s3_get_foreign_key, s3_unicode, S3MarkupStripper, S3TypeConverter
from s3validators import IS_ONE_OF
from s3xml import S3XMLFormat

DEBUG = False
if DEBUG:
    print >> sys.stderr, "S3Resource: DEBUG MODE"
    def _debug(m):
        print >> sys.stderr, m
else:
    _debug = lambda m: None

osetattr = object.__setattr__
ogetattr = object.__getattribute__

TEXTTYPES = ("string", "text")

# =============================================================================
class S3Resource(object):
    """
        API for resources.

        A "resource" is a set of records in a database table including their
        references in certain related resources (components). A resource can
        be defined like:

            resource = S3Resource(table)

        A resource defined like this would include all records in the table.
        Further parameters for the resource constructor as well as methods
        of the resource instance can be used to filter for particular subsets.

        This API provides extended standard methods to access and manipulate
        data in resources while respecting current authorization and other
        S3 framework rules.
    """

    def __init__(self, tablename,
                 id=None,
                 prefix=None,
                 uid=None,
                 filter=None,
                 vars=None,
                 parent=None,
                 linked=None,
                 linktable=None,
                 alias=None,
                 components=None,
                 include_deleted=False,
                 approved=True,
                 unapproved=False,
                 context=False):
        """
            Constructor

            @param tablename: tablename, Table, or an S3Resource instance
            @param prefix: prefix to use for the tablename

            @param id: record ID (or list of record IDs)
            @param uid: record UID (or list of record UIDs)

            @param filter: filter query
            @param vars: dictionary of URL query variables

            @param components: list of component aliases
                               to load for this resource

            @param alias: the alias for this resource (internal use only)
            @param parent: the parent resource (internal use only)
            @param linked: the linked resource (internal use only)
            @param linktable: the link table (internal use only)

            @param include_deleted: include deleted records (used for
                                    synchronization)

            @param approved: include approved records
            @param unapproved: include unapproved records
            @param context: apply context filters
        """

        s3db = current.s3db
        auth = current.auth
        manager = current.manager

        # Names ---------------------------------------------------------------

        self.table = None
        self._alias = None

        if prefix is None:
            if not isinstance(tablename, basestring):
                if isinstance(tablename, Table):
                    self.table = tablename
                    self._alias = self.table._tablename
                    tablename = self._alias
                elif isinstance(tablename, S3Resource):
                    self.table = tablename.table
                    self._alias = self.table._tablename
                    tablename = tablename.tablename
                else:
                    raise SyntaxError("illegal argument")
            if "_" in tablename:
                prefix, name = tablename.split("_", 1)
            else:
                raise SyntaxError("invalid tablename: %s" % tablename)
        else:
            name = tablename
            tablename = "%s_%s" % (prefix, name)

        self.prefix = prefix
        """ Module prefix of the tablename """
        self.name = name
        """ Tablename without module prefix """
        self.tablename = tablename
        """ Tablename """
        self.alias = alias or name
        """
            Alias of the resource, defaults to tablename
            without module prefix
        """

        # Table ---------------------------------------------------------------

        if self.table is None:
            try:
                self.table = s3db[tablename]
            except:
                manager.error = "Undefined table: %s" % tablename
                raise # KeyError(manager.error)
        table = self.table

        # Set default approver
        auth.permission.set_default_approver(table)

        if not self._alias:
            self._alias = tablename
            """ Table alias (the tablename used in joins/queries) """

        if parent is not None:
            if parent.tablename == self.tablename:
                alias = "%s_%s_%s" % (prefix, self.alias, name)
                pkey = table._id.name
                table = table = table.with_alias(alias)
                table._id = table[pkey]
                self._alias = alias
        self.table = table

        self.fields = table.fields
        self._id = table._id

        # Hooks ---------------------------------------------------------------

        self.ERROR = manager.ERROR

        # Authorization hooks
        self.permit = auth.s3_has_permission
        self.accessible_query = auth.s3_accessible_query

        # Filter --------------------------------------------------------------

        # Default query options
        self.include_deleted = include_deleted
        self._approved = approved
        self._unapproved = unapproved

        # Component Filter
        self.filter = None

        # Resource Filter
        self.rfilter = None
        self.fquery = None
        self.fvfltr = None

        # Rows ----------------------------------------------------------------

        self._rows = None
        self._rowindex = None
        self.rfields = None
        self.dfields = None
        self._ids = []
        self._uids = []
        self._length = None

        # Request attributes --------------------------------------------------

        self.vars = None # set during build_query
        self.lastid = None
        self.files = Storage()

        # Components ----------------------------------------------------------

        # Initialize component properties (will be set during _attach)
        self.link = None
        self.linktable = None
        self.actuate = None
        self.lkey = None
        self.rkey = None
        self.pkey = None
        self.fkey = None
        self.multiple = True

        self.parent = parent # the parent resource
        self.linked = linked # the linked resource

        self.components = Storage()
        self.links = Storage()

        if parent is None:
            # This is the master resource - attach components
            attach = self._attach
            hooks = s3db.get_components(table, names=components)
            [attach(alias, hooks[alias]) for alias in hooks]

            # Build query
            self.build_query(id=id, uid=uid, filter=filter, vars=vars)
            if context:
                self.add_filter(s3db.context)

        # Component - attach link table
        elif linktable is not None:
            # This is link-table component - attach the link table
            self.link = S3Resource(linktable,
                                   parent=self.parent,
                                   linked=self,
                                   include_deleted=self.include_deleted,
                                   approved=self._approved,
                                   unapproved=self._unapproved)

        # Export and Import ---------------------------------------------------

        # Pending Imports
        self.skip_import = False
        self.job = None
        self.mtime = None
        self.error = None
        self.error_tree = None
        self.import_count = 0
        self.import_created = []
        self.import_updated = []
        self.import_deleted = []

        # Export meta data
        self.muntil = None      # latest mtime of the exported records
        self.results = None     # number of exported records

        # Standard methods ----------------------------------------------------

        # CRUD
        self.crud = manager.crud()
        self.crud.resource = self

    # -------------------------------------------------------------------------
    def search_method(self):
        """
            Return an S3Search method
            - to be deprecated
        """

        tablename = self.tablename
        search = current.s3db.get_config(tablename, "search_method")
        if not search:
            if "name" in self.table:
                T = current.T
                search = current.manager.search(
                    name="%s_search_simple" % tablename,
                    label=T("Name"),
                    comment=T("Enter a name to search for. You may use % as wildcard. Press 'Search' without input to list all items."),
                    field=["name"])
            else:
                search = current.manager.search()

        return search

    # -------------------------------------------------------------------------
    def _attach(self, alias, hook):
        """
            Attach a component

            @param alias: the alias
            @param hook: the hook
        """
        
        if alias is not None and hook.filterby is not None:
            table_alias = "%s_%s_%s" % (hook.prefix,
                                        hook.alias,
                                        hook.name)
            table = hook.table.with_alias(table_alias)
            table._id = table[table._id.name]
            hook.table = table
        else:
            table_alias = None

        # Create as resource
        component = S3Resource(hook.table,
                               parent=self,
                               alias=alias,
                               linktable=hook.linktable,
                               include_deleted=self.include_deleted,
                               approved=self._approved,
                               unapproved=self._unapproved)

        if table_alias:
            component.tablename = hook.tablename
            component._alias = table_alias

        # Update component properties
        component.pkey = hook.pkey
        component.fkey = hook.fkey
        component.linktable = hook.linktable
        component.lkey = hook.lkey
        component.rkey = hook.rkey
        component.actuate = hook.actuate
        component.autodelete = hook.autodelete
        component.autocomplete = hook.autocomplete
        component.alias = alias
        component.multiple = hook.multiple
        component.values = hook.values

        if hook.filterby is not None:
            filterfor = hook.filterfor
            is_list = isinstance(filterfor, (tuple, list))
            if is_list and len(filterfor) == 1:
                is_list = False
                filterfor = filterfor[0]
            if not is_list:
                component.filter = (hook.table[hook.filterby] == filterfor)
            elif filterfor:
                component.filter = (hook.table[hook.filterby].belongs(filterfor))
            else:
                component.filter = None
        else:
            component.filter = None    

        # Copy properties to the link
        if component.link is not None:
            link = component.link
            link.pkey = component.pkey
            link.fkey = component.lkey
            link.actuate = component.actuate
            link.autodelete = component.autodelete
            link.multiple = component.multiple
            self.links[link.name] = link

        self.components[alias] = component
        return

    # -------------------------------------------------------------------------
    # Query handling
    # -------------------------------------------------------------------------
    def build_query(self, id=None, uid=None, filter=None, vars=None):
        """
            Query builder

            @param id: record ID or list of record IDs to include
            @param uid: record UID or list of record UIDs to include
            @param filter: filtering query (DAL only)
            @param vars: dict of URL query variables
        """

        # Reset the rows counter
        self._length = None

        self.rfilter = S3ResourceFilter(self,
                                        id=id,
                                        uid=uid,
                                        filter=filter,
                                        vars=vars)
        return self.rfilter

    # -------------------------------------------------------------------------
    def add_filter(self, f=None, c=None):
        """
            Extend the current resource filter

            @param f: a Query or a S3ResourceQuery instance
            @param c: alias of the component this filter concerns,
                      automatically adds the respective component join
                      (not needed for S3ResourceQuery instances)
        """

        if f is None:
            return
        self.clear()
        if self.rfilter is None:
            self.rfilter = S3ResourceFilter(self)
        self.rfilter.add_filter(f, component=c)

    # -------------------------------------------------------------------------
    def add_component_filter(self, alias, f=None):
        """
            Extend the resource filter of a particular component, does
            not affect the master resource filter (as opposed to add_filter)

            @param alias: the alias of the component
            @param f: a Query or a S3ResourceQuery instance
        """

        if f is None:
            return
        if self.rfilter is None:
            self.rfilter = S3ResourceFilter(self)
        self.rfilter.add_filter(f, component=alias, master=False)

    # -------------------------------------------------------------------------
    def get_query(self):
        """ Get the effective query """

        if self.rfilter is None:
            self.build_query()
        return self.rfilter.get_query()

    # -------------------------------------------------------------------------
    def get_filter(self):
        """ Get the effective virtual fields filter """

        if self.rfilter is None:
            self.build_query()
        return self.rfilter.get_filter()

    # -------------------------------------------------------------------------
    def clear_query(self):
        """ Removes the current query (does not remove the set!) """

        self.rfilter = None
        components = self.components
        if components:
            for c in components:
                components[c].clear_query()

    # -------------------------------------------------------------------------
    # Data access (new API)
    # -------------------------------------------------------------------------
    def count(self, left=None, distinct=False):
        """
            Get the total number of available records in this resource

            @param left: left outer joins, if required
            @param distinct: only count distinct rows
        """

        if self.rfilter is None:
            self.build_query()
        if self._length is None:
            self._length = self.rfilter.count(left=left,
                                              distinct=distinct)
        return self._length

    # -------------------------------------------------------------------------
    def select(self,
               fields,
               start=0,
               limit=None,
               left=None,
               orderby=None,
               groupby=None,
               distinct=False,
               virtual=True,
               count=False,
               getids=False,
               as_rows=False,
               represent=False,
               show_links=True,
               raw_data=False):
        """
            Extract data from this resource

            @param fields: the fields to extract (selector strings)
            @param start: index of the first record
            @param limit: maximum number of records
            @param left: additional left joins required for filters
            @param orderby: orderby-expression for DAL
            @param groupby: fields to group by (overrides fields!)
            @param distinct: select distinct rows
            @param virtual: include mandatory virtual fields
            @param count: include the total number of matching records
            @param getids: include the IDs of all matching records
            @param as_rows: return the rows (don't extract)
            @param represent: render field value representations
            @param raw_data: include raw data in the result
        """

        # Init
        db = current.db
        s3db = current.s3db
        table = self.table
        tablename = table._tablename
        pkey = str(table._id)
        
        query = self.get_query()
        vfltr = self.get_filter()
        
        rfilter = self.rfilter
        resolve = self.resolve_selectors

        # dict to collect accessible queries for differential
        # field authorization (each joined table is authorized separately)
        aqueries = {} 

        # Query to use for filtering
        filter_query = query

        #if DEBUG:
        #    _start = datetime.datetime.now()
        #    _debug("select of %s starting" % tablename)

        # Resolve tables, fields and joins
        joins = {}
        left_joins = S3LeftJoins(tablename)

        # Left joins from filter
        ftables = left_joins.add(rfilter.get_left_joins())

        # Left joins from caller
        qtables = left_joins.add(left)
        ftables.extend(qtables)

        # Virtual fields and extra fields required by filter
        virtual_fields = rfilter.get_fields()
        vfields, vjoins, l, d = resolve(virtual_fields, show=False)
        joins.update(vjoins)
        vtables = left_joins.extend(l)
        distinct |= d

        # Display fields (fields to include in the result)
        if fields is None:
            fields = [f.name for f in self.readable_fields()]
        dfields, djoins, l, d = resolve(fields, extra_fields=False)
        joins.update(djoins)
        dtables = left_joins.extend(l)
        distinct |= d

        # Temporarily deactivate (mandatory) virtual fields
        if not virtual:
            vf = table.virtualfields
            osetattr(table, "virtualfields", [])

        # Initialize field data and effort estimates
        field_data = {pkey: ({}, {}, False, False, False)}
        effort = {pkey: 0}
        for dfield in dfields:
            colname = dfield.colname
            effort[colname] = 0
            field_data[colname] = ({}, {},
                                   dfield.tname != self.tablename,
                                   dfield.ftype[:5] == "list:",
                                   dfield.virtual)

        # Resolve ORDERBY
        orderby_aggregate = orderby_fields = None
        
        if orderby:

            if isinstance(orderby, str):
                items = orderby.split(",")
            elif not isinstance(orderby, (list, tuple)):
                items = [orderby]
            else:
                items = orderby

            orderby = []
            orderby_fields = []

            # For GROUPBY id (which we need here for left joins), we need
            # all ORDERBY-fields to appear in an aggregation function, or
            # otherwise the ORDERBY can be ambiguous.
            orderby_aggregate = []
                
            for item in items:

                expression = None
                
                if type(item) is Expression:
                    f = item.first
                    op = item.op
                    if op == db._adapter.AGGREGATE:
                        # Already an aggregation
                        expression = item
                    elif isinstance(f, Field) and op == db._adapter.INVERT:
                        direction = "desc"
                    else:
                        # Other expression - not supported
                        continue
                elif isinstance(item, Field):
                    direction = "asc"
                    f = item
                elif isinstance(item, str):
                    fn, direction = (item.strip().split() + ["asc"])[:2]
                    tn, fn = ([table._tablename] + fn.split(".", 1))[-2:]
                    try:
                        f = db[tn][fn]
                    except (AttributeError, KeyError):
                        continue
                else:
                    continue

                fname = str(f)
                tname = fname.split(".", 1)[0]
                
                if tname != tablename:
                    if tname in left_joins:
                        ftables.append(tname)
                    elif tname in joins:
                        filter_query &= joins[tname]
                    else:
                        # No join found for this field => skip
                        continue
                    
                orderby_fields.append(f)
                if expression is None:
                    expression = f if direction == "asc" else ~f
                    orderby.append(expression)
                    direction = direction.strip().lower()[:3]
                    if fname != pkey:
                        expression = f.min() if direction == "asc" else ~(f.max())
                else:
                    orderby.append(expression)
                orderby_aggregate.append(expression)

        # Initialize master query
        master_query = filter_query
        
        # Ignore limitby if vfltr
        if vfltr is None:
            limitby = self.limitby(start=start, limit=limit)
        else:
            limitby = None
            
        # Filter Query:
        
        ids = None
        page = None
        totalrows = None

        # Get the left joins
        filter_joins = left_joins.as_list(tablenames=ftables,
                                          aqueries=aqueries)

        if getids or count or left_joins:
            if not groupby and not vfltr and \
               (count or limitby or vtables != ftables):

                if getids or left_joins:
                    field = table._id
                    fdistinct = False
                    fgroupby = field
                else:
                    field = table._id.count()
                    fdistinct = True
                    fgroupby = None

                # We don't need virtual fields here, so deactivate
                # even if virtual is True
                if virtual:
                    vf = table.virtualfields
                    osetattr(table, "virtualfields", [])

                # Retrieve the ordered record IDs (or number of rows)
                rows = db(filter_query).select(field,
                                               left=filter_joins,
                                               distinct=fdistinct,
                                               orderby=orderby_aggregate,
                                               groupby=fgroupby,
                                               cacheable=True)
                                               
                # Restore the virtual fields
                if virtual:
                    osetattr(table, "virtualfields", vf)

                if getids or left_joins:
                    ids = [row[pkey] for row in rows]
                    totalrows = len(ids)
                    if limitby:
                        page = ids[limitby[0]:limitby[1]]
                    else:
                        page = ids
                    # Use simplified master query
                    master_query = table._id.belongs(page)
                    orderby = None
                    limitby = None
                else:
                    totalrows = rows.first()[field]

        # Master Query:
        
        # Add joins for virtual fields
        for join in vjoins.values():
            master_query &= join

        # Determine fields in master query
        mfields = {}
        qfields = {}

        if groupby:
            # Only extract GROUPBY fields (as we don't support aggregates)

            if isinstance(groupby, str):
                items = groupby.split(",")
            elif not isinstance(groupby, (list, tuple)):
                items = [groupby]
            else:
                items = groupby
                
            groupby = []
            gappend = groupby.append
            for item in items:
                tname = None
                if isinstance(item, Field):
                    f = item
                elif isinstance(item, str):
                    fn = item.strip()
                    tname, fn = ([table._tablename] + fn.split(".", 1))[-2:]
                    try:
                        f = db[tname][fn]
                    except (AttributeError, KeyError):
                        continue
                else:
                    continue
                
                gappend(f)
                fname = str(f)
                qfields[fname] = f

                tnames = None
                for dfield in dfields:
                    if dfield.colname == fname:
                        tnames = dfield.left.keys()
                        break
                if not tnames:
                    if not tname:
                        tname = fname.split(".", 1)[0]
                    if tname != tablename:
                        qtables.append(tname)
                else:
                    qtables.extend([tn for tn in tnames if tn != tablename])
                    
            mfields.update(qfields)

        else:
            
            if ids is None and filter_joins:
                qtables = ftables
            qtables.extend(vtables)

            for flist in [dfields, vfields]:
                for rfield in flist:
                    tname = rfield.tname
                    if tname == tablename or as_rows or tname in qtables:
                        colname = rfield.colname
                        if rfield.show:
                            mfields[colname] = True
                        if rfield.field:
                            qfields[colname] = rfield.field
                        if as_rows and \
                           tname != tablename and \
                           tname not in qtables:
                            left = rfield.left
                            if left:
                                for tn in left:
                                    qtables.extend([j.first._tablename
                                                    for j in left[tn]])
                            else:
                                qtables.append(tname)

        if not groupby:
            if distinct and orderby:
                # With DISTINCT, if an ORDERBY-field is not in SELECT, then
                # add it (required by postgresql).
                if orderby:
                    for orderby_field in orderby_fields:
                        fn = str(orderby_field)
                        if fn not in qfields:
                            qfields[fn] = orderby_field

            # Make sure we have the primary key in SELECT
            if pkey not in qfields:
                qfields[pkey] = self._id
            has_id = True

        elif groupby:
            distinct = False
            if orderby:
                orderby = orderby_aggregate
            has_id = pkey in qfields

        # Get left joins
        master_joins = left_joins.as_list(tablenames=qtables,
                                          aqueries=aqueries)

        # Retrieve the master rows
        rows = db(master_query).select(left=master_joins,
                                       distinct=distinct,
                                       groupby=groupby,
                                       orderby=orderby,
                                       limitby=limitby,
                                       cacheable=not as_rows,
                                       *qfields.values())

        # Restore virtual fields (if they were deactivated before)
        if not virtual:
            osetattr(table, "virtualfields", vf)

        # Apply virtual fields filter :
        if rows and vfltr is not None:

            if count:
                rows = rfilter(rows)
                totalrows = len(rows)
                
                if limit and start is None:
                    start = 0
                if start is not None and limit is not None:
                    rows = Rows(db,
                                records=rows.records[start:start+limit],
                                colnames=rows.colnames,
                                compact=False)
                elif start is not None:
                    rows = Rows(db,
                                records=rows.records[start:],
                                colnames=rows.colnames,
                                compact=False)
                    
            else:
                rows = rfilter(rows, start=start, limit=limit)

            if (getids or left_joins) and has_id:
                ids = list(set([row[pkey] for row in rows]))
                totalrows = len(ids)

        # With GROUPBY, return the grouped rows here:
        if groupby or as_rows:
            return rows

        # Otherwise: initialize output
        output = {"rfields": dfields, "numrows": totalrows, "ids": ids}

        if not rows:
            output["rows"] = []
            return output

        # Extract master rows
        records = self.__extract(rows, pkey, mfields.keys(),
                                 join=hasattr(rows[0], tablename),
                                 field_data=field_data,
                                 effort=effort,
                                 represent = represent)

        # Extract the page IDs
        if page is None:
            if ids is None:
                key = self._id
                page = ids = [row[key] for row in rows]
            else:
                page = ids
                
        # Secondary Queries:

        # Always use simplified query which doesn't need left joins
        squery = table._id.belongs(page)

        # Determine tables and fields
        stables = {}
        for dfield in dfields:
            colname = dfield.colname
            if colname in qfields or dfield.tname == tablename:
                continue
            tname = dfield.tname
            if tname not in stables:
                sfields = stables[tname] = {"_left": S3LeftJoins(table)}
            else:
                sfields = stables[tname]
            if colname not in sfields:
                sfields[colname] = dfield.field
                l = dfield.left
                if l:
                    [sfields["_left"].add(l[tn]) for tn in l]

        # Retrieve + extract into records
        for tname in stables:

            stable = stables[tname]

            # Get the extra fields for subtable
            sresource = s3db.resource(tname)
            efields, ejoins, l, d = sresource.resolve_selectors([])

            # Get all left joins for subtable
            tnames = left_joins.extend(l) + stable["_left"].tables
            sjoins = left_joins.as_list(tablenames=tnames,
                                        aqueries=aqueries)
            if not sjoins:
                continue
            del stable["_left"]

            # Get all fields for subtable query
            extract = stable.keys()
            for efield in efields:
                stable[efield.colname] = efield.field
            sfields = [f for f in stable.values() if f]
            if not sfields:
                sfields.append(s3db.table(tname)._id)
            sfields.insert(0, table._id)

            # Retrieve the subtable rows
            rows = db(squery).select(left=sjoins,
                                     distinct=True,
                                     cacheable=True,
                                     *sfields)

            # Extract and merge the data
            records = self.__extract(rows,
                                     pkey,
                                     extract,
                                     records=records,
                                     join=True,
                                     field_data=field_data,
                                     effort=effort,
                                     represent=represent)

        #if DEBUG:
        #    end = datetime.datetime.now()
        #    duration = end - _start
        #    duration = '{:.4f}'.format(duration.total_seconds())
        #    _debug("All data retrieved after %s seconds" % duration)

        # Represent
        NONE = current.messages["NONE"]
        
        results = {}
        for dfield in dfields:
            
            colname = dfield.colname
            fvalues, frecords, joined, list_type, virtual = field_data[colname]

            if represent:

                # Get the renderer
                renderer = dfield.represent
                if not callable(renderer):
                    renderer = lambda v: s3_unicode(v) if v is not None else NONE

                # Deactivate linkto if so requested
                if not show_links and hasattr(renderer, "linkto"):
                    linkto = renderer.linkto
                    renderer.linkto = None
                else:
                    linkto = None

                per_row_lookup = list_type and \
                                 effort[colname] < len(fvalues) * 30

                # Render all unique values
                if hasattr(renderer, "bulk") and not list_type:
                    per_row_lookup = False
                    fvalues = renderer.bulk(fvalues.keys(), list_type = False)
                elif not per_row_lookup:
                    for value in fvalues:
                        try:
                            text = renderer(value)
                        except:
                            text = s3_unicode(value)
                        fvalues[value] = text

                # Write representations into result
                for record_id in frecords:

                    if record_id not in results:
                        results[record_id] = Storage() \
                                             if not raw_data \
                                             else Storage(_row=Storage())
                                             
                    record = frecords[record_id]
                    result = results[record_id]

                    # List type with per-row lookup?
                    if per_row_lookup:
                        value = record.keys()
                        if None in value and len(value) > 1:
                            value = [v for v in value if v is not None]
                        try:
                            text = renderer(value)
                        except:
                            text = s3_unicode(value)
                        result[colname] = text
                        if raw_data:
                            result["_row"][colname] = value

                    # Single value (master record)
                    elif len(record) == 1 or \
                         not joined and not list_type:
                        value = record.keys()[0]
                        result[colname] = fvalues[value] \
                                          if value in fvalues else NONE
                        if raw_data:
                            result["_row"][colname] = value
                        continue

                    # Multiple values (joined or list-type)
                    else:
                        vlist = []
                        for value in record:
                            if value is None and not list_type:
                                continue
                            value = fvalues[value] \
                                    if value in fvalues else NONE
                            vlist.append(value)

                        # Concatenate multiple values
                        if any([hasattr(v, "xml") for v in vlist]):
                            data = TAG[""](
                                    list(
                                        chain.from_iterable(
                                            [(v, ", ") for v in vlist])
                                        )[:-1]
                                    )
                        else:
                            data = ", ".join([s3_unicode(v) for v in vlist])

                        result[colname] = data
                        if raw_data:
                            result["_row"][colname] = record.keys()

                # Restore linkto
                if linkto is not None:
                    renderer.linkto = linkto

            else:
                for record_id in records:
                    if record_id not in results:
                        result = results[record_id] = Storage()
                    else:
                        result = results[record_id]

                    data = frecords[record_id].keys()
                    if len(data) == 1 and not list_type:
                        data = data[0]
                    result[colname] = data

        #if DEBUG:
        #    end = datetime.datetime.now()
        #    duration = end - _start
        #    duration = '{:.4f}'.format(duration.total_seconds())
        #    _debug("Representation complete after %s seconds" % duration)
        #_debug("select DONE")

        output["rows"] = [results[record_id] for record_id in page]
        return output
        
    # -------------------------------------------------------------------------
    @staticmethod
    def __extract(rows,
                  pkey,
                  columns,
                  join=True,
                  records=None,
                  field_data=None,
                  effort=None,
                  represent=False):
        """
            Helper method for select to extract data from a
            query result.

            @param rows: the rows
            @param pkey: the primary key
            @param columns: the columns to extract
            @param join: the rows are the result of a join query
            @param records: the records dict to merge the data into
            @param field_data: the cumulative field data
            @param effort: estimated effort for list:type representations
            @param represent: collect unique values per field and estimate
                              representation efforts for list:types
        """

        if records is None:
            records = {}
        
        def get(key):
            t, f = key.split(".", 1)
            if join:
                return lambda row, t=t, f=f: ogetattr(ogetattr(row, t), f)
            else:
                return lambda row, f=f: ogetattr(row, f)

        getkey = get(pkey)
        getval = [get(c) for c in columns]

        for k, g in groupby(rows, key=getkey):
            group = list(g)
            record = records.get(k, {})
            for idx, col in enumerate(columns):
                fvalues, frecords, joined, list_type, virtual = field_data[col]
                values = record.get(col, {})
                lazy = False
                for row in group:
                    try:
                        value = getval[idx](row)
                    except AttributeError:
                        _debug("Warning S3Resource.__extract: column %s not in row" % col)
                        value = None
                    if lazy or callable(value):
                        # Lazy virtual field
                        value = value()
                        lazy = True
                    if virtual and not list_type and type(value) is list:
                        # Virtual field that returns a list
                        list_type = True
                    if list_type and value is not None:
                        if represent and value:
                            effort[col] += 30 + len(value)
                        for v in value:
                            if v not in values:
                                values[v] = None
                            if represent and v not in fvalues:
                                fvalues[v] = None
                    else:
                        if value not in values:
                            values[value] = None
                        if represent and value not in fvalues:
                            fvalues[value] = None
                record[col] = values
                if k not in frecords:
                    frecords[k] = record[col]
            records[k] = record

        return records

    # -------------------------------------------------------------------------
    def insert(self, **fields):
        """
            Insert a record into this resource

            @param fields: dict of field/value pairs to insert
        """

        # Check permission
        authorised = self.permit("create", self.tablename)
        if not authorised:
            raise IOError("Operation not permitted: INSERT INTO %s" %
                            self.tablename)

        # Insert new record
        record_id = self.table.insert(**fields)

        # Audit
        if record_id:
            record = Storage(fields).update(id=record_id)
            current.audit("create", self.prefix, self.name, form=record)

        return record_id

    # -------------------------------------------------------------------------
    def update(self):

        raise NotImplementedError

    # -------------------------------------------------------------------------
    def delete(self,
               ondelete=None,
               format=None,
               cascade=False,
               replaced_by=None):
        """
            Delete all (deletable) records in this resource

            @param ondelete: on-delete callback
            @param format: the representation format of the request (optional)
            @param cascade: this is a cascade delete (prevents rollbacks/commits)
            @param replaced_by: used by record merger

            @return: number of records deleted

            @todo: Fix for Super Entities where we need row[table._id.name]
            @todo: optimize
        """

        db = current.db
        manager = current.manager
        get_session = manager.get_session
        clear_session = manager.clear_session
        DELETED = manager.DELETED

        s3db = current.s3db
        define_resource = s3db.resource
        get_config = s3db.get_config
        delete_super = s3db.delete_super

        INTEGRITY_ERROR = self.ERROR.INTEGRITY_ERROR
        permit = self.permit
        audit = current.audit
        prefix = self.prefix
        name = self.name
        tablename = self.tablename
        table = self.table
        pkey = table._id.name

        # use current.deployment_settings.get_security_archive_not_delete()?
        archive_not_delete = manager.s3.crud.archive_not_delete

        # Reset error
        manager.error = None

        # Get all rows
        if "uuid" in table.fields:
            rows = self.select([table._id.name, "uuid"], as_rows=True)
        else:
            rows = self.select([table._id.name], as_rows=True)

        if not rows:
            # No rows? => that was it already :)
            return 0

        numrows = 0
        deletable = []

        if archive_not_delete and DELETED in table:

            # Find all deletable rows
            references = table._referenced_by
            try:
                rfields = [f for f in references if f.ondelete == "RESTRICT"]
            except AttributeError:
                # older web2py
                references = [db[tn][fn] for tn, fn in references]
                rfields = [f for f in references if f.ondelete == "RESTRICT"]

            restricted = []
            ids = [row[pkey] for row in rows]
            for rfield in rfields:
                fn, tn = rfield.name, rfield.tablename
                rtable = db[tn]
                query = (rfield.belongs(ids))
                if DELETED in rtable:
                    query &= (rtable[DELETED] != True)
                rrows = db(query).select(rfield)
                restricted += [r[fn] for r in rrows if r[fn] not in restricted]
            deletable = [row[pkey] for row in rows if row[pkey] not in restricted]

            # Get custom ondelete-cascade
            ondelete_cascade = get_config(tablename, "ondelete_cascade")

            for row in rows:
                if not permit("delete", table, record_id=row[pkey]):
                    continue
                error = manager.error
                manager.error = None

                # Run custom ondelete_cascade first
                if ondelete_cascade:
                    callback(ondelete_cascade, row, tablename=tablename)
                    if manager.error:
                        # Row is not deletable (custom RESTRICT)
                        continue
                    if row[pkey] not in deletable:
                        # Check deletability again
                        restrict = False
                        for tn, fn in rfields:
                            rtable = db[tn]
                            rfield = rtable[fn]
                            query = (rfield == row[pkey])
                            if DELETED in rtable:
                                query &= (rtable[DELETED] != True)
                            rrow = db(query).select(rfield,
                                                    limitby=(0, 1)).first()
                            if rrow:
                                restrict = True
                        if not restrict:
                            deletable.append(row[pkey])

                if row[pkey] not in deletable:
                    # Row is not deletable => skip with error status
                    manager.error = INTEGRITY_ERROR
                    continue

                # Run automatic ondelete-cascade
                for rfield in references:
                    fn, tn = rfield.name, rfield.tablename
                    rtable = db[tn]
                    query = (rfield == row[pkey])
                    if rfield.ondelete == "CASCADE":
                        rresource = define_resource(tn,
                                                    filter=query,
                                                    unapproved=True)
                        rondelete = get_config(tn, "ondelete")
                        rresource.delete(ondelete=rondelete, cascade=True)
                        if manager.error:
                            break
                    elif rfield.ondelete == "SET NULL":
                        try:
                            db(query).update(**{fn:None})
                        except:
                            manager.error = INTEGRITY_ERROR
                            break
                    elif rfield.ondelete == "SET DEFAULT":
                        try:
                            db(query).update(**{fn:rfield.default})
                        except:
                            manager.error = INTEGRITY_ERROR
                            break

                if manager.error:
                    # Error in ondelete-cascade: roll back + skip row
                    if not cascade:
                        db.rollback()
                    continue
                else:
                    # Auto-delete linked records if this was the last link
                    linked = self.linked
                    if linked and self.autodelete and linked.autodelete:
                        rkey = linked.rkey
                        fkey = linked.fkey
                        if rkey in table:
                            query = (table._id == row[pkey])
                            this = db(query).select(table._id,
                                                    table[rkey],
                                                    limitby=(0, 1)).first()
                            query = (table._id != this[pkey]) & \
                                    (table[rkey] == this[rkey])
                            if DELETED in table:
                                query != (table[DELETED] != True)
                            remaining = db(query).select(table._id,
                                                         limitby=(0, 1)).first()
                            if not remaining:
                                linked_table = s3db.table(linked.tablename)
                                query = (linked_table[fkey] == this[rkey])
                                linked = define_resource(linked_table,
                                                         filter=query,
                                                         unapproved=True)
                                ondelete = get_config(linked.tablename, "ondelete")
                                linked.delete(ondelete=ondelete, cascade=True)

                    # Pull back prior error status
                    manager.error = error
                    error = None

                    # "Park" foreign keys to resolve constraints, "un-delete"
                    # would then restore any still-valid FKs from this field!
                    fields = dict(deleted=True)
                    if "deleted_fk" in table:
                        record = table[row[pkey]]
                        fk = {}
                        for f in table.fields:
                            if record[f] is not None and \
                               s3_has_foreign_key(table[f]):
                                fk[f] = record[f]
                                fields[f] = None
                            else:
                                continue
                        if fk:
                            fields.update(deleted_fk=json.dumps(fk))

                    # Annotate the replacement record
                    record_id = str(row[pkey])
                    if replaced_by and record_id in replaced_by and \
                       "deleted_rb" in table.fields:
                        fields.update(deleted_rb=replaced_by[record_id])

                    # Update the row, finally
                    db(table._id == row[pkey]).update(**fields)
                    numrows += 1
                    # Clear session
                    if get_session(prefix=prefix, name=name) == row[pkey]:
                        clear_session(prefix=prefix, name=name)
                    # Audit
                    audit("delete", prefix, name,
                          record=row[pkey], representation=format)
                    # Delete super-entity
                    delete_super(table, row)
                    # On-delete hook
                    if ondelete:
                        callback(ondelete, row)
                    # Commit after each row to not have it rolled back by
                    # subsequent cascade errors
                    if not cascade:
                        db.commit()
        else:
            # Hard delete
            for row in rows:

                # Check permission to delete this row
                if not permit("delete", table, record_id=row[pkey]):
                    continue
                try:
                    del table[row[pkey]]
                except:
                    # Row is not deletable
                    manager.error = INTEGRITY_ERROR
                    continue
                else:
                    # Successfully deleted
                    numrows += 1
                    # Clear session
                    if get_session(prefix=prefix, name=name) == row[pkey]:
                        clear_session(prefix=prefix, name=name)
                    # Audit
                    audit("delete", prefix, name,
                          record=row[pkey], representation=format)
                    # Delete super-entity
                    delete_super(table, row)
                    # On-delete hook
                    if ondelete:
                        callback(ondelete, row)
                    # Commit after each row to not have it rolled back by
                    # subsequent cascade errors
                    if not cascade:
                        db.commit()

        if numrows == 0 and not deletable:
            # No deletable rows found
            manager.error = INTEGRITY_ERROR

        return numrows

    # -------------------------------------------------------------------------
    def approve(self, components=[], approve=True):
        """
            Approve all records in this resource

            @param components: list of component aliases to include, None
                               for no components, empty list for all components
            @param approve: set to approved (False for reset to unapproved)
        """

        db = current.db
        auth = current.auth

        if auth.s3_logged_in():
            user_id = approve and auth.user.id or None
        else:
            return False

        tablename = self.tablename
        table = self.table

        records = self.select([self._id.name], limit=None)
        for record in records["rows"]:

            record_id = record[str(self._id)]

            # Forget any cached permission for this record
            auth.permission.forget(table, record_id)

            if "approved_by" in table.fields:
                dbset = db(table._id == record_id)
                success = dbset.update(approved_by = user_id)
                if not success:
                    current.db.rollback()
                    return False
                else:
                    onapprove = self.get_config("onapprove", None)
                    if onapprove is not None:
                        row = dbset.select(limitby=(0, 1)).first()
                        if row:
                            callback(onapprove, row, tablename=tablename)
            if components is None:
                continue
            for alias in self.components:
                if components and alias not in components:
                    continue
                component = self.components[alias]
                success = component.approve(components=None, approve=approve)
                if not success:
                    current.db.rollback()
                    return False

        return True

    # -------------------------------------------------------------------------
    def reject(self, cascade=False):
        """ Reject (delete) all records in this resource """

        db = current.db
        s3db = current.s3db

        manager = current.manager

        define_resource = s3db.resource
        get_session = manager.get_session
        clear_session = manager.clear_session
        DELETED = manager.DELETED

        INTEGRITY_ERROR = self.ERROR.INTEGRITY_ERROR
        permit = self.permit
        #audit = current.audit
        prefix = self.prefix
        name = self.name
        tablename = self.tablename
        table = self.table
        pkey = table._id.name

        # Get hooks configuration
        get_config = s3db.get_config
        ondelete = get_config(tablename, "ondelete")
        onreject = get_config(tablename, "onreject")
        ondelete_cascade = get_config(tablename, "ondelete_cascade")

        # Get all rows
        if "uuid" in table.fields:
            rows = self.select([table._id.name, "uuid"], as_rows=True)
        else:
            rows = self.select([table._id.name], as_rows=True)
        if not rows:
            return True

        delete_super = s3db.delete_super

        if DELETED in table:

            references = table._referenced_by

            for row in rows:

                error = manager.error
                manager.error = None

                # On-delete-cascade
                if ondelete_cascade:
                    callback(ondelete_cascade, row, tablename=tablename)

                # Automatic cascade
                for ref in references:
                    try:
                        tn, fn = ref.tablename, ref.name
                    except:
                        # old web2py < 2.0
                        tn, fn = ref
                    rtable = db[tn]
                    rfield = rtable[fn]
                    query = (rfield == row[pkey])
                    # Ignore RESTRICTs => reject anyway
                    if rfield.ondelete in ("CASCADE", "RESTRICT"):
                        rresource = define_resource(tn, filter=query, unapproved=True)
                        rresource.reject(cascade=True)
                        if manager.error:
                            break
                    elif rfield.ondelete == "SET NULL":
                        try:
                            db(query).update(**{fn:None})
                        except:
                            manager.error = INTEGRITY_ERROR
                            break
                    elif rfield.ondelete == "SET DEFAULT":
                        try:
                            db(query).update(**{fn:rfield.default})
                        except:
                            manager.error = INTEGRITY_ERROR
                            break

                if manager.error:
                    db.rollback()
                    raise RuntimeError("Reject failed for %s.%s" %
                                      (resource.tablename, row[resource.table._id]))
                else:
                    # Pull back prior error status
                    manager.error = error
                    error = None

                    # On-reject hook
                    if onreject:
                        callback(onreject, row, tablename=tablename)

                    # Park foreign keys
                    fields = dict(deleted=True)
                    if "deleted_fk" in table:
                        record = table[row[pkey]]
                        fk = {}
                        for f in table.fields:
                            if record[f] is not None and \
                               s3_has_foreign_key(table[f]):
                                fk[f] = record[f]
                                fields[f] = None
                            else:
                                continue
                        if fk:
                            fields.update(deleted_fk=json.dumps(fk))

                    # Update the row, finally
                    db(table._id == row[pkey]).update(**fields)

                    # Clear session
                    if get_session(prefix=prefix, name=name) == row[pkey]:
                        clear_session(prefix=prefix, name=name)

                    # Delete super-entity
                    delete_super(table, row)

                    # On-delete hook
                    if ondelete:
                        callback(ondelete, row, tablename=tablename)

        else:
            # Hard delete
            for row in rows:

                # On-delete-cascade
                if ondelete_cascade:
                    callback(ondelete_cascade, row, tablename=tablename)

                # On-reject
                if onreject:
                    callback(onreject, row, tablename=tablename)

                try:
                    del table[row[pkey]]
                except:
                    # Row is not deletable
                    manager.error = INTEGRITY_ERROR
                    db.rollback()
                    raise
                else:
                    # Clear session
                    if get_session(prefix=prefix, name=name) == row[pkey]:
                        clear_session(prefix=prefix, name=name)

                    # Delete super-entity
                    delete_super(table, row)

                    # On-delete
                    if ondelete:
                        callback(ondelete, row, tablename=tablename)

        return True

    # -------------------------------------------------------------------------
    def merge(self,
              original_id,
              duplicate_id,
              replace=None,
              update=None,
              main=None):
        """ Merge two records, see also S3RecordMerger.merge """

        return S3RecordMerger(self).merge(original_id,
                                          duplicate_id,
                                          replace=replace,
                                          update=update,
                                          main=main)

    # -------------------------------------------------------------------------
    # Exports
    # -------------------------------------------------------------------------
    def datatable(self,
                  fields=None,
                  start=0,
                  limit=None,
                  left=None,
                  orderby=None,
                  distinct=False,
                  getids=False):
        """
            Generate a data table of this resource

            @param fields: list of fields to include (field selector strings)
            @param start: index of the first record to include
            @param limit: maximum number of records to include
            @param left: additional left joins for DB query
            @param orderby: orderby for DB query
            @param distinct: distinct-flag for DB query
            @param getids: return the record IDs of all records matching the
                           query (used in search to create a filter)

            @return: tuple (S3DataTable, numrows, ids), where numrows represents
                     the total number of rows in the table that match the query;
                     ids is empty unless getids=True
        """

        # Choose fields
        if fields is None:
            fields = [f.name for f in self.readable_fields()]
        selectors = list(fields)

        # Automatically include the record ID
        table = self.table
        if table._id.name not in selectors:
            fields.insert(0, table._id.name)
            selectors.insert(0, table._id.name)

        # Extract the data
        data = self.select(selectors,
                           start=start,
                           limit=limit,
                           orderby=orderby,
                           left=left,
                           distinct=distinct,
                           count=True,
                           getids=getids,
                           represent=True)

        # Generate the data table
        if data["rows"]:
            rfields = data["rfields"]
            dt = S3DataTable(rfields, data["rows"], orderby=orderby)
        else:
            dt = None
        return dt, data["numrows"], data["ids"]

    # -------------------------------------------------------------------------
    def datalist(self,
                 fields=None,
                 start=0,
                 limit=None,
                 left=None,
                 orderby=None,
                 distinct=False,
                 getids=False,
                 listid=None,
                 layout=None):
        """
            Generate a data list of this resource

            @param fields: list of fields to include (field selector strings)
            @param start: index of the first record to include
            @param limit: maximum number of records to include
            @param left: additional left joins for DB query
            @param orderby: orderby for DB query
            @param distinct: distinct-flag for DB query
            @param getids: return the record IDs of all records matching the
                           query (used in search to create a filter)
            @param listid: the list identifier
            @param layout: custom renderer function (see S3DataList.render)

            @return: tuple (S3DataList, numrows, ids), where numrows represents
                     the total number of rows in the table that match the query;
                     ids is empty unless getids=True
        """

        # Choose fields
        if fields is None:
            fields = [f.name for f in self.readable_fields()]
        selectors = list(fields)

        # Automatically include the record ID
        table = self.table
        if table._id.name not in selectors:
            fields.insert(0, table._id.name)
            selectors.insert(0, table._id.name)

        # Extract the data
        data = self.select(selectors,
                           start=start,
                           limit=limit,
                           orderby=orderby,
                           left=left,
                           distinct=distinct,
                           count=True,
                           getids=getids,
                           raw_data=True,
                           represent=True)

        # Generate the data list
        numrows = data["numrows"]
        dl = S3DataList(self,
                        fields,
                        data["rows"],
                        listid=listid,
                        start=start,
                        limit=limit,
                        total=numrows,
                        layout=layout)
                        
        return dl, numrows, data["ids"]

    # -------------------------------------------------------------------------
    def pivottable(self, rows, cols, layers, strict=True):
        """
            Generate a pivot table of this resource.

            @param rows: field selector for the rows dimension
            @param cols: field selector for the columns dimension
            @param layers: list of tuples (field selector, method) for
                           the aggregation layers
            @param strict: filter out dimension values which don't match
                           the resource filter

            @return: an S3PivotTable instance

            Supported methods: see S3PivotTable
        """

        return S3PivotTable(self, rows, cols, layers, strict=strict)

    # -------------------------------------------------------------------------
    def json(self,
             fields=None,
             start=0,
             limit=None,
             left=None,
             distinct=False,
             orderby=None):
        """
            Export a JSON representation of the resource.

            @param fields: list of field selector strings
            @param start: index of the first record
            @param limit: maximum number of records
            @param left: list of (additional) left joins
            @param distinct: select only distinct rows
            @param orderby: Orderby-expression for the query

            @return: the JSON (as string), representing a list of
                     dicts with {"tablename.fieldname":"value"}
        """

        data = self.select(fields=fields,
                           start=start,
                           limit=limit,
                           orderby=orderby,
                           left=left,
                           distinct=distinct)["rows"]

        return json.dumps(data)

    # -------------------------------------------------------------------------
    # Data Object API
    # -------------------------------------------------------------------------
    def load(self,
             fields=None,
             skip=None,
             start=None,
             limit=None,
             orderby=None,
             virtual=True,
             cacheable=False):
        """
            Loads records from the resource, applying the current filters,
            and stores them in the instance.

            @param fields: list of field names to include
            @param skip: list of field names to skip
            @param start: the index of the first record to load
            @param limit: the maximum number of records to load
            @param orderby: orderby-expression for the query
            @param virtual: whether to load virtual fields or not
            @param cacheable: don't define Row actions like update_record
                              or delete_record (faster, and the record can
                              be cached)

            @return: the records as list of Rows
        """


        table = self.table
        tablename = self.tablename

        UID = current.xml.UID
        load_uids = hasattr(table, UID)

        if not skip:
            skip = tuple()

        if fields or skip:
            s3 = current.response.s3
            if "all_meta_fields" in s3:
                meta_fields = s3.all_meta_fields
            else:
                meta_fields = s3.all_meta_fields = s3_all_meta_field_names()
            s3db = current.s3db

        # Field selection
        qfields = ([table._id.name, UID])
        append = qfields.append
        for f in table.fields:
            
            if f in ("wkt", "the_geom") and \
               (tablename == "gis_location" or \
                tablename.startswith("gis_layer_shapefile_")):
                    
                # Filter out bulky Polygons
                continue

            if fields or skip:

                # Must include all meta-fields
                if f in meta_fields:
                    append(f)
                    continue

                # Must include all super-keys
                ktablename, key, multiple = s3_get_foreign_key(table[f], m2m=False)
                if ktablename:
                    ktable = s3db.table(ktablename)
                    if ktable and hasattr(ktable, "instance_type"):
                        append(f)
                        continue

            if f in skip:
                continue
            if not fields or f in fields:
                qfields.append(f)

        fields = list(set(filter(lambda f: hasattr(table, f), qfields)))

        if self._rows is not None:
            self.clear()

        rfilter = self.rfilter
        multiple = rfilter.multiple if rfilter is not None else True
        if not multiple and self.parent and self.parent.count() == 1:
            start = 0
            limit = 1

        rows = self.select(fields,
                           start=start,
                           limit=limit,
                           orderby=orderby,
                           virtual=virtual,
                           as_rows=True)

        ids = self._ids = []
        new_id = ids.append
        
        self._uids = []
        new_uid = self._uids.append
        self._rows = []
        new_row = self._rows.append
        
        if rows:
            pkey = table._id.name
            for row in rows:
                if hasattr(row, tablename):
                    _row = ogetattr(row, tablename)
                    if type(_row) is Row:
                        row = _row
                record_id = ogetattr(row, pkey)
                if record_id not in ids:
                    new_id(record_id)
                    new_row(row)
                    if load_uids:
                        new_uid(ogetattr(row, UID))
            self._length = len(self._rows)

        return self._rows

    # -------------------------------------------------------------------------
    def clear(self):
        """ Removes the records currently stored in this instance """

        self._rows = None
        self._rowindex = None
        self._length = None
        self._ids = None
        self._uids = None
        self.files = Storage()

        if self.components:
            for c in self.components:
                self.components[c].clear()

    # -------------------------------------------------------------------------
    def records(self, fields=None):
        """
            Get the current set as Rows instance

            @param fields: the fields to include (list of Fields)
        """

        if fields is None:
            if self.tablename == "gis_location":
                fields = [f for f in self.table
                          if f.name not in ("wkt", "the_geom")]
            else:
                fields = [f for f in self.table]

        if self._rows is None:
            return Rows(current.db)
        else:
            colnames = map(str, fields)
            return Rows(current.db, self._rows, colnames=colnames)

    # -------------------------------------------------------------------------
    def __getitem__(self, key):
        """
            Find a record currently stored in this instance by its record ID

            @param key: the record ID
            @return: a Row

            @raises: IndexError if the record is not currently loaded
        """

        index = self._rowindex
        if index is None:
            _id = self._id.name
            rows = self._rows
            if rows:
                index = Storage([(str(row[_id]), row) for row in rows])
            else:
                index = Storage()
            self._rowindex = index
        key = str(key)
        if key in index:
            return index[key]
        raise IndexError

    # -------------------------------------------------------------------------
    def __iter__(self):
        """
            Iterate over the records currently stored in this instance
        """

        if self._rows is None:
            self.load()
        rows = self._rows
        for i in xrange(len(rows)):
            yield rows[i]
        return

    # -------------------------------------------------------------------------
    def get(self, key, component=None):
        """
            Get component records for a record currently stored in this
            instance.

            @param key: the record ID
            @param component: the name of the component
                              (None to get the primary record)
            @return: a Row (if component is None) or a list of rows
        """

        NOT_FOUND = KeyError("Record not found")

        if not key:
            raise NOT_FOUND
        if self._rows is None:
            self.load()
        try:
            master = self[key]
        except IndexError:
            raise NOT_FOUND

        if not component:
            return master
        else:
            if component in self.components:
                c = self.components[component]
            elif component in self.links:
                c = self.links[component]
            else:
                raise AttributeError("Undefined component %s" % component)
            rows = c._rows
            if rows is None:
                rows = c.load()
            if not rows:
                return []
            pkey, fkey = c.pkey, c.fkey
            master_id = master[pkey]
            if c.link:
                lkey, rkey = c.lkey, c.rkey
                lids = [r[rkey] for r in c.link if master_id == r[lkey]]
                rows = [record for record in rows if record[fkey] in lids]
            else:
                rows = [record for record in rows if master_id == record[fkey]]
            return rows

    # -------------------------------------------------------------------------
    def get_id(self):
        """ Get the IDs of all records currently stored in this instance """

        if self._ids is None:
            self.__load_ids()

        if not self._ids:
            return None
        elif len(self._ids) == 1:
            return self._ids[0]
        else:
            return self._ids

    # -------------------------------------------------------------------------
    def get_uid(self):
        """ Get the UUIDs of all records currently stored in this instance """

        if current.xml.UID not in self.table.fields:
            return None
        if self._ids is None:
            self.__load_ids()

        if not self._uids:
            return None
        elif len(self._uids) == 1:
            return self._uids[0]
        else:
            return self._uids

    # -------------------------------------------------------------------------
    def __len__(self):
        """
            The number of currently loaded rows
        """

        if self._rows is not None:
            return len(self._rows)
        else:
            return 0

    # -------------------------------------------------------------------------
    def __load_ids(self):
        """ Loads the IDs/UIDs of all records matching the current filter """

        table = self.table
        UID = current.xml.UID

        pkey = table._id.name

        if UID in table.fields:
            has_uid = True
            fields = (pkey, UID)
        else:
            has_uid = False
            fields = (pkey, )

        rfilter = self.rfilter
        multiple = rfilter.multiple if rfilter is not None else True
        if not multiple and self.parent and self.parent.count() == 1:
            start = 0
            limit = 1
        else:
            start = limit = None

        rows = self.select(fields,
                           start=start,
                           limit=limit)["rows"]

        if rows:
            ID = str(table._id)
            self._ids = [row[ID] for row in rows]
            if has_uid:
                uid = str(table[UID])
                self._uids = [row[uid] for row in rows]
        else:
            self._ids = []

        return

    # -------------------------------------------------------------------------
    # Representation
    # -------------------------------------------------------------------------
    def __repr__(self):
        """
            String representation of this resource
        """

        pkey = self.table._id.name

        if self._rows:
            ids = [r[pkey] for r in self]
            return "<S3Resource %s %s>" % (self.tablename, ids)
        else:
            return "<S3Resource %s>" % self.tablename

    # -------------------------------------------------------------------------
    def __contains__(self, item):
        """
            Tests whether this resource contains a (real) field.

            @param item: the field selector or Field instance
        """

        fn = str(item)
        if "." in fn:
            tn, fn = fn.split(".", 1)
            if tn == self.tablename:
                item = fn
        try:
            rf = self.resolve_selector(str(item))
        except (SyntaxError, AttributeError):
            return 0
        if rf.field is not None:
            return 1
        else:
            return 0

    # -------------------------------------------------------------------------
    def __nonzero__(self):
        """
            Boolean test of this resource
        """

        return self is not None

    # -------------------------------------------------------------------------
    # XML Export
    # -------------------------------------------------------------------------
    def export_xml(self,
                   start=None,
                   limit=None,
                   msince=None,
                   fields=None,
                   dereference=True,
                   mcomponents=[],
                   rcomponents=None,
                   references=None,
                   stylesheet=None,
                   as_tree=False,
                   as_json=False,
                   maxbounds=False,
                   filters=None,
                   pretty_print=False,
                   **args):
        """
            Export this resource as S3XML

            @param start: index of the first record to export (slicing)
            @param limit: maximum number of records to export (slicing)
            @param msince: export only records which have been modified
                            after this datetime
            @param dereference: include referenced resources
            @param mcomponents: components of the master resource to
                                include (list of tablenames), empty list
                                for all
            @param rcomponents: components of referenced resources to
                                include (list of tablenames), empty list
                                for all
            @param stylesheet: path to the XSLT stylesheet (if required)
            @param as_tree: return the ElementTree (do not convert into string)
            @param as_json: represent the XML tree as JSON
            @param filters: additional URL filters (Sync), as dict
                            {tablename: {url_var: string}}
            @param pretty_print: insert newlines/indentation in the output
            @param args: dict of arguments to pass to the XSLT stylesheet
        """

        manager = current.manager
        xml = current.xml

        output = None
        args = Storage(args)

        xmlformat = S3XMLFormat(stylesheet) if stylesheet else None

        # Export as element tree
        #if DEBUG:
            #_start = datetime.datetime.now()
            #tablename = self.tablename
            #_debug("export_tree of %s starting" % tablename)
        tree = self.export_tree(start=start,
                                limit=limit,
                                msince=msince,
                                fields=fields,
                                dereference=dereference,
                                mcomponents=mcomponents,
                                rcomponents=rcomponents,
                                references=references,
                                filters=filters,
                                maxbounds=maxbounds,
                                xmlformat=xmlformat)
        #if DEBUG:
            #end = datetime.datetime.now()
            #duration = end - _start
            #duration = '{:.2f}'.format(duration.total_seconds())
            #_debug("export_tree of %s completed in %s seconds" % \
                    #(tablename, duration))

        # XSLT transformation
        if tree and xmlformat is not None:
            #if DEBUG:
            #    _start = datetime.datetime.now()
            import uuid
            tfmt = xml.ISOFORMAT
            args.update(domain=manager.domain,
                        base_url=manager.s3.base_url,
                        prefix=self.prefix,
                        name=self.name,
                        utcnow=datetime.datetime.utcnow().strftime(tfmt),
                        msguid=uuid.uuid4().urn)
            tree = xmlformat.transform(tree, **args)
            #if DEBUG:
                #end = datetime.datetime.now()
                #duration = end - _start
                #duration = '{:.2f}'.format(duration.total_seconds())
                #_debug("transform of %s using %s completed in %s seconds" % \
                        #(tablename, stylesheet, duration))

        # Convert into the requested format
        # (Content Headers are set by the calling function)
        if tree:
            if as_tree:
                output = tree
            elif as_json:
                #if DEBUG:
                    #_start = datetime.datetime.now()
                output = xml.tree2json(tree, pretty_print=pretty_print)
                #if DEBUG:
                    #end = datetime.datetime.now()
                    #duration = end - _start
                    #duration = '{:.2f}'.format(duration.total_seconds())
                    #_debug("tree2json of %s completed in %s seconds" % \
                            #(tablename, duration))
            else:
                output = xml.tostring(tree, pretty_print=pretty_print)

        return output

    # -------------------------------------------------------------------------
    def export_tree(self,
                    start=0,
                    limit=None,
                    msince=None,
                    fields=None,
                    references=None,
                    dereference=True,
                    mcomponents=None,
                    rcomponents=None,
                    filters=None,
                    maxbounds=False,
                    xmlformat=None):
        """
            Export the resource as element tree

            @param start: index of the first record to export
            @param limit: maximum number of records to export
            @param msince: minimum modification date of the records
            @param fields: data fields to include (default: all)
            @param references: foreign keys to include (default: all)
            @param dereference: also export referenced records
            @param mcomponents: components of the master resource to
                                include (list of tablenames), empty list
                                for all
            @param rcomponents: components of referenced resources to
                                include (list of tablenames), empty list
                                for all
            @param filters: additional URL filters (Sync), as dict
                            {tablename: {url_var: string}}
            @param maxbounds: include lat/lon boundaries in the top
                              level element (off by default)
        """

        xml = current.xml
        manager = current.manager

        if manager.show_urls:
            base_url = manager.s3.base_url
        else:
            base_url = None

        # Split reference/data fields
        (rfields, dfields) = self.split_fields(data=fields,
                                               references=references)

        # Filter for MCI >= 0 (setting)
        table = self.table
        if xml.filter_mci and "mci" in table.fields:
            mci_filter = (table.mci >= 0)
            self.add_filter(mci_filter)

        # Sync filters
        tablename = self.tablename
        if filters and tablename in filters:
            queries = S3URLQuery.parse(self, filters[tablename])
            [self.add_filter(q) for a in queries for q in queries[a]]

        # Total number of results
        results = self.count()

        # Initialize export metadata
        self.muntil = None
        self.results = 0

        # Load slice
        if msince is not None and "modified_on" in table.fields:
            orderby = "%s ASC" % table["modified_on"]
        else:
            orderby = None

        # Fields to load
        if xmlformat:
            include, exclude = xmlformat.get_fields(self.tablename)
        else:
            include, exclude = None, None
        self.load(fields=include,
                  skip=exclude,
                  start=start,
                  limit=limit,
                  orderby=orderby,
                  virtual=False,
                  cacheable=True)

        format = current.auth.permission.format
        if format == "geojson":
            if results > current.deployment_settings.get_gis_max_features():
                headers = {"Content-Type": "application/json"}
                message = "Too Many Records"
                status = 509
                raise HTTP(status,
                           body=xml.json_message(success=False,
                                                 statuscode=status,
                                                 message=message),
                           web2py_error=message,
                           **headers)
            # Lookups per layer not per record
            if tablename == "gis_layer_shapefile":
                # GIS Shapefile Layer
                locations = current.gis.get_shapefile_geojson(self)
            elif tablename == "gis_theme_data":
                # GIS Theme Layer
                locations = current.gis.get_theme_geojson(self)
            else:
                # e.g. GIS Feature Layer
                # e.g. Search results
                locations = current.gis.get_location_data(self)
        elif format in ("georss", "kml", "gpx"):
            locations = current.gis.get_location_data(self)
        else:
            locations = None

        # Build the tree
        #if DEBUG:
        #    _start = datetime.datetime.now()

        root = etree.Element(xml.TAG.root)
        
        export_map = Storage()
        reference_map = []
        
        prefix = self.prefix
        name = self.name
        if base_url:
            url = "%s/%s/%s" % (base_url, prefix, name)
        else:
            url = "/%s/%s" % (prefix, name)

        # Use lazy representations
        lazy = []
        current.auth_user_represent = S3Represent(lookup="auth_user",
                                                  fields=["email"])

        export_resource = self.__export_resource

        for record in self._rows:
            element = export_resource(record,
                                      rfields=rfields,
                                      dfields=dfields,
                                      parent=root,
                                      base_url=url,
                                      reference_map=reference_map,
                                      export_map=export_map,
                                      lazy=lazy,
                                      components=mcomponents,
                                      filters=filters,
                                      msince=msince,
                                      locations=locations,
                                      xmlformat=xmlformat)
            if element is None:
                results -= 1
        #if DEBUG:
        #    end = datetime.datetime.now()
        #    duration = end - _start
        #    duration = '{:.2f}'.format(duration.total_seconds())
        #    _debug("export_resource of primary resource and components completed in %s seconds" % \
        #        duration)

        # Add referenced resources to the tree
        #if DEBUG:
        #    _start = datetime.datetime.now()

        define_resource = current.s3db.resource

        depth = dereference and manager.MAX_DEPTH or 0
        while reference_map and depth:
            depth -= 1
            load_map = dict()
            get_exported = export_map.get
            for ref in reference_map:
                if "table" in ref and "id" in ref:
                    # Get tablename and IDs
                    tname = ref["table"]
                    ids = ref["id"]
                    if not isinstance(ids, list):
                        ids = [ids]

                    # Exclude records which are already in the tree
                    exported = get_exported(tname, [])
                    ids = [x for x in ids if x not in exported]
                    if not ids:
                        continue

                    # Append the new ids to load_map[tname]
                    if tname in load_map:
                        ids = [x for x in ids if x not in load_map[tname]]
                        load_map[tname] += ids
                    else:
                        load_map[tname] = ids

            reference_map = []
            REF = xml.ATTRIBUTE.ref
            for tablename in load_map:
                load_list = load_map[tablename]

                # Sync filters
                if filters:
                    filter_vars = filters.get(tablename, None)
                else:
                    filter_vars = None

                prefix, name = tablename.split("_", 1)
                rresource = define_resource(tablename,
                                            id=load_list,
                                            components=[],
                                            vars=filter_vars)
                table = rresource.table
                if manager.s3.base_url:
                    url = "%s/%s/%s" % (manager.s3.base_url, prefix, name)
                else:
                    url = "/%s/%s" % (prefix, name)
                rfields, dfields = rresource.split_fields(data=fields,
                                                          references=references)

                # Fields to load
                if xmlformat:
                    include, exclude = xmlformat.get_fields(rresource.tablename)
                else:
                    include, exclude = None, None
                rresource.load(fields=include,
                               skip=exclude,
                               limit=None,
                               virtual=False,
                               cacheable=True)

                export_resource = rresource.__export_resource
                for record in rresource:
                    element = export_resource(record,
                                              rfields=rfields,
                                              dfields=dfields,
                                              parent=root,
                                              base_url=url,
                                              reference_map=reference_map,
                                              export_map=export_map,
                                              components=rcomponents,
                                              lazy=lazy,
                                              filters=filters,
                                              master=False,
                                              locations=locations,
                                              xmlformat=xmlformat)

                    # Mark as referenced element (for XSLT)
                    if element is not None:
                        element.set(REF, "True")
        #if DEBUG:
        #    end = datetime.datetime.now()
        #    duration = end - _start
        #    duration = '{:.2f}'.format(duration.total_seconds())
        #    _debug("export_resource of referenced resources and their components completed in %s seconds" % \
        #           duration)

        # Render all pending lazy representations
        if lazy:
            for renderer, element, attr, f in lazy:
                renderer.render_node(element, attr, f)

        # Complete the tree
        tree = xml.tree(None,
                        root=root,
                        domain=manager.domain,
                        url=base_url,
                        results=results,
                        start=start,
                        limit=limit,
                        maxbounds=maxbounds)

        # Store number of results
        self.results = results

        return tree

    # -------------------------------------------------------------------------
    def __export_resource(self,
                          record,
                          rfields=[],
                          dfields=[],
                          parent=None,
                          base_url=None,
                          reference_map=None,
                          export_map=None,
                          lazy=None,
                          components=None,
                          filters=None,
                          msince=None,
                          master=True,
                          locations=None,
                          xmlformat=None):
        """
            Add a <resource> to the element tree

            @param record: the record
            @param rfields: list of reference fields to export
            @param dfields: list of data fields to export
            @param parent: the parent element
            @param base_url: the base URL of the resource
            @param reference_map: the reference map of the request
            @param export_map: the export map of the request
            @param components: list of components to include from referenced
                               resources (tablenames)
            @param filters: additional URL filters (Sync), as dict
                            {tablename: {url_var: string}}
            @param msince: the minimum update datetime for exported records
            @param master: True of this is the master resource
            @param locations: the locations for GIS encoding
        """

        xml = current.xml

        pkey = self.table._id
        action = "read"
        representation = "xml"

        # Construct the record URL
        if base_url:
            record_url = "%s/%s" % (base_url, record[pkey])
        else:
            record_url = None

        # Export the record
        add = False
        export = self._export_record
        element, rmap = export(record,
                               rfields=rfields,
                               dfields=dfields,
                               parent=parent,
                               export_map=export_map,
                               lazy=lazy,
                               url=record_url,
                               msince=msince,
                               master=master,
                               locations=locations)
                               
        if element is not None:
            add = True

        # Export components
        if components is not None:

            resource_components = self.components.values()
            unfiltered = [c for c in resource_components if c.filter is None]
            
            for component in resource_components:
                ctablename = component.tablename
                    
                # Shall this component be included?
                if components and ctablename not in components:
                    continue

                # We skip a filtered component if an unfiltered
                # component of the same table is available:
                if component.filter is not None and ctablename in unfiltered:
                    continue

                cpkey = component.table._id

                if component.link is not None:
                    c = component.link
                else:
                    c = component

                # Before loading the component: add filters
                if c._rows is None:
                    
                    # MCI filter
                    ctable = c.table
                    if xml.filter_mci and xml.MCI in ctable.fields:
                        mci_filter = S3FieldSelector(xml.MCI) >= 0
                        c.add_filter(mci_filter)

                    # Sync filters
                    ctablename = c.tablename
                    if filters and ctablename in filters:
                        queries = S3URLQuery.parse(self, filters[ctablename])
                        [c.add_filter(q) for a in queries for q in queries[a]]

                    # Fields to load
                    if xmlformat:
                        include, exclude = xmlformat.get_fields(c.tablename)
                    else:
                        include, exclude = None, None
                        
                    # Load the records
                    c.load(fields=include,
                           skip=exclude,
                           limit=None,
                           virtual=False,
                           cacheable=True)

                # Split fields
                crfields, cdfields = c.split_fields(skip=[c.fkey])

                # Construct the component base URL
                if record_url:
                    component_url = "%s/%s" % (record_url, c.alias)
                else:
                    component_url = None

                # Find related records
                crecords = self.get(record[pkey], component=c.alias)
                # @todo: load() should limit this automatically:
                if not c.multiple and len(crecords):
                    crecords = [crecords[0]]

                # Export records
                export = c._export_record
                map_record = c.__map_record
                for crecord in crecords:
                    # Construct the component record URL
                    if component_url:
                        crecord_url = "%s/%s" % (component_url, crecord[cpkey])
                    else:
                        crecord_url = None
                    # Export the component record
                    celement, crmap = export(crecord,
                                             rfields=crfields,
                                             dfields=cdfields,
                                             parent=element,
                                             export_map=export_map,
                                             lazy=lazy,
                                             url=crecord_url,
                                             msince=msince,
                                             master=False,
                                             locations=locations)
                    if celement is not None:
                        add = True # keep the parent record

                        # Update "modified until" from component
                        if not self.muntil or \
                           c.muntil and c.muntil > self.muntil:
                            self.muntil = c.muntil

                        map_record(crecord, crmap,
                                   reference_map, export_map)

        # Update reference_map and export_map
        if add:
            self.__map_record(record, rmap, reference_map, export_map)
        elif parent is not None and element is not None:
            idx = parent.index(element)
            if idx:
                del parent[idx]
            return None

        return element

    # -------------------------------------------------------------------------
    def _export_record(self,
                       record,
                       rfields=[],
                       dfields=[],
                       parent=None,
                       export_map=None,
                       lazy=None,
                       url=None,
                       msince=None,
                       master=True,
                       locations=None):
        """
            Exports a single record to the element tree.

            @param record: the record
            @param rfields: list of foreign key fields to export
            @param dfields: list of data fields to export
            @param parent: the parent element
            @param export_map: the export map of the current request
            @param url: URL of the record
            @param msince: minimum last update time
            @param master: True if this is a record in the master resource
            @param locations: the locations for GIS encoding
        """

        manager = current.manager
        xml = current.xml

        tablename = self.tablename
        table = self.table

        # Replace user ID representation by lazy method
        auth_user_represent = Storage()
        if hasattr(current, "auth_user_represent"):
            user_ids = ("created_by", "modified_by", "owned_by_user")
            for fn in user_ids:
                if hasattr(table, fn):
                    f = ogetattr(table, fn)
                    auth_user_represent[fn] = f.represent
                    f.represent = current.auth_user_represent

        #postprocess = s3db.get_config(tablename, "onexport", None)

        default = (None, None)

        # Do not export the record if it already is in the export map
        if tablename in export_map and record[table._id] in export_map[tablename]:
            return default

        # Do not export the record if it hasn't been modified since msince
        # NB This can't be moved to tree level as we do want to export records
        #    which have modified components
        MTIME = xml.MTIME
        if MTIME in record:
            if msince is not None and record[MTIME] <= msince:
                return default
            if not self.muntil or record[MTIME] > self.muntil:
                self.muntil = record[MTIME]

        # Audit read
        current.audit("read", self.prefix, self.name,
                      record=record[table._id], representation="xml")

        # Reference map for this record
        rmap = xml.rmap(table, record, rfields)

        # Use alias if distinct from resource name
        linked = self.linked
        if self.parent is not None and linked is not None:
            alias = linked.alias
            name = linked.name
        else:
            alias = self.alias
            name = self.name
        if alias == name:
            alias = None

        postprocess = self.get_config("xml_post_render")

        # Generate the element
        element = xml.resource(parent, table, record,
                               fields=dfields,
                               alias=alias,
                               lazy=lazy,
                               url=url,
                               postprocess=postprocess)

        # Add the references
        xml.add_references(element, rmap,
                           show_ids=manager.show_ids, lazy=lazy)

        # GIS-encode the element
        xml.gis_encode(self, record, element, rmap,
                       locations=locations, master=master)

        # Restore user-ID representations
        for fn in auth_user_represent:
            ogetattr(table, fn).represent = auth_user_represent[fn]

        return (element, rmap)

    # -------------------------------------------------------------------------
    def __map_record(self, record, rmap, reference_map, export_map):
        """
            Add the record to the export map, and update the
            reference map with the record's references

            @param record: the record
            @param rmap: the reference map of the record
            @param reference_map: the reference map of the request
            @param export_map: the export map of the request
        """

        tablename = self.tablename
        record_id = record[self.table._id]

        if rmap:
            reference_map.extend(rmap)
        if tablename in export_map:
            export_map[tablename].append(record_id)
        else:
            export_map[tablename] = [record_id]
        return

    # -------------------------------------------------------------------------
    # XML Import
    # -------------------------------------------------------------------------
    def import_xml(self, source,
                   files=None,
                   id=None,
                   format="xml",
                   stylesheet=None,
                   extra_data=None,
                   ignore_errors=False,
                   job_id=None,
                   commit_job=True,
                   delete_job=False,
                   strategy=None,
                   update_policy=None,
                   conflict_policy=None,
                   last_sync=None,
                   onconflict=None,
                   **args):
        """
            XML Importer

            @param source: the data source, accepts source=xxx, source=[xxx, yyy, zzz] or
                           source=[(resourcename1, xxx), (resourcename2, yyy)], where the
                           xxx has to be either an ElementTree or a file-like object
            @param files: attached files (None to read in the HTTP request)
            @param id: ID (or list of IDs) of the record(s) to update (performs only update)
            @param format: type of source = "xml", "json" or "csv"
            @param stylesheet: stylesheet to use for transformation
            @param extra_data: for CSV imports, dict of extra cols to add to each row
            @param ignore_errors: skip invalid records silently
            @param job_id: resume from previous import job_id
            @param commit_job: commit the job to the database
            @param delete_job: delete the import job from the queue
            @param strategy: tuple of allowed import methods (create/update/delete)
            @param update_policy: policy for updates (sync)
            @param conflict_policy: policy for conflict resolution (sync)
            @param last_sync: last synchronization datetime (sync)
            @param onconflict: callback hook for conflict resolution (sync)
            @param args: parameters to pass to the transformation stylesheet
        """

        manager = current.manager

        # Check permission for the resource
        permit = manager.permit
        authorised = permit("create", self.table) and \
                     permit("update", self.table)
        if not authorised:
            raise IOError("Insufficient permissions")

        xml = current.xml
        tree = None
        self.job = None

        if not job_id:

            # Resource data
            prefix = self.prefix
            name = self.name

            # Additional stylesheet parameters
            tfmt = xml.ISOFORMAT
            utcnow = datetime.datetime.utcnow().strftime(tfmt)
            domain = manager.domain
            base_url = manager.s3.base_url
            args.update(domain=domain,
                        base_url=base_url,
                        prefix=prefix,
                        name=name,
                        utcnow=utcnow)

            # Build import tree
            if not isinstance(source, (list, tuple)):
                source = [source]
            for item in source:
                if isinstance(item, (list, tuple)):
                    resourcename, s = item[:2]
                else:
                    resourcename, s = None, item
                if isinstance(s, etree._ElementTree):
                    t = s
                elif format == "json":
                    if isinstance(s, basestring):
                        source = StringIO(s)
                        t = xml.json2tree(s)
                    else:
                        t = xml.json2tree(s)
                elif format == "csv":
                    t = xml.csv2tree(s,
                                     resourcename=resourcename,
                                     extra_data=extra_data)
                elif format == "xls":
                    t = xml.xls2tree(s,
                                     resourcename=resourcename,
                                     extra_data=extra_data)
                else:
                    t = xml.parse(s)
                if not t:
                    if xml.error:
                        raise SyntaxError(xml.error)
                    else:
                        raise SyntaxError("Invalid source")

                if stylesheet is not None:
                    t = xml.transform(t, stylesheet, **args)
                    _debug(t)
                    if not t:
                        raise SyntaxError(xml.error)

                if not tree:
                    tree = t.getroot()
                else:
                    tree.extend(list(t.getroot()))

            if files is not None and isinstance(files, dict):
                self.files = Storage(files)

        else:
            # job ID given
            pass
        
        response = current.response
        # Flag to let onvalidation/onaccept know this is coming from a Bulk Import
        response.s3.bulk = True
        success = self.import_tree(id, tree,
                                   ignore_errors=ignore_errors,
                                   job_id=job_id,
                                   commit_job=commit_job,
                                   delete_job=delete_job,
                                   strategy=strategy,
                                   update_policy=update_policy,
                                   conflict_policy=conflict_policy,
                                   last_sync=last_sync,
                                   onconflict=onconflict)
        response.s3.bulk = False

        self.files = Storage()

        # Response message
        if format == "json":
            # Whilst all Responses are JSON, it's easier to debug by having the
            # response appear in the browser than launching a text editor
            response.headers["Content-Type"] = "application/json"
        if self.error_tree is not None:
            tree = xml.tree2json(self.error_tree)
        else:
            tree = None

        import_info = {"records":self.import_count}
        created = self.import_created
        if created:
            import_info["created"] = created
        updated = self.import_updated
        if updated:
            import_info["updated"] = updated
        deleted = self.import_deleted
        if deleted:
            import_info["deleted"] = deleted

        if success is True:
            return xml.json_message(message=self.error, tree=tree,
                                    **import_info)
        elif success and hasattr(success, "job_id"):
            self.job = success
            return xml.json_message(message=self.error, tree=tree,
                                    **import_info)
        else:
            return xml.json_message(False, 400,
                                    message=self.error, tree=tree)

    # -------------------------------------------------------------------------
    def import_tree(self, id, tree,
                    job_id=None,
                    ignore_errors=False,
                    delete_job=False,
                    commit_job=True,
                    strategy=None,
                    update_policy=None,
                    conflict_policy=None,
                    last_sync=None,
                    onconflict=None):
        """
            Import data from an S3XML element tree.

            @param id: record ID or list of record IDs to update
            @param tree: the element tree
            @param ignore_errors: continue at errors (=skip invalid elements)

            @param job_id: restore a job from the job table (ID or UID)
            @param delete_job: delete the import job from the job table
            @param commit_job: commit the job (default)

            @todo: update for link table support
        """

        from s3import import S3ImportJob

        db = current.db
        xml = current.xml
        auth = current.auth
        permit = auth.s3_has_permission
        tablename = self.tablename
        table = self.table

        if job_id is not None:

            # Restore a job from the job table
            self.error = None
            self.error_tree = None
            try:
                import_job = S3ImportJob(table,
                                         job_id=job_id,
                                         strategy=strategy,
                                         update_policy=update_policy,
                                         conflict_policy=conflict_policy,
                                         last_sync=last_sync,
                                         onconflict=onconflict)
            except:
                self.error = self.ERROR.BAD_SOURCE
                return False

            # Delete the job?
            if delete_job:
                import_job.delete()
                return True

            # Load all items
            job_id = import_job.job_id
            item_table = import_job.item_table
            items = db(item_table.job_id == job_id).select()
            load_item = import_job.load_item
            for item in items:
                success = load_item(item)
                if not success:
                    self.error = import_job.error
                    self.error_tree = import_job.error_tree
            import_job.restore_references()

            # this is only relevant for commit_job=True
            if commit_job:
                if self.error and not ignore_errors:
                    return False
            else:
                return import_job

            # Call the import pre-processor to prepare tables
            # and cleanup the tree as necessary
            import_prep = current.manager.import_prep
            if import_prep:
                tree = import_job.get_tree()
                callback(import_prep,
                         # takes tuple (resource, tree) as argument
                         (self, tree),
                         tablename=tablename)
                # Skip import?
                if self.skip_import:
                    _debug("Skipping import to %s" % self.tablename)
                    self.skip_import = False
                    return True

        else:
            # Create a new job from an element tree
            # Do not import into tables without "id" field
            if "id" not in table.fields:
                self.error = self.ERROR.BAD_RESOURCE
                return False

            # Reset error and error tree
            self.error = None
            self.error_tree = None

            # Call the import pre-processor to prepare tables
            # and cleanup the tree as necessary
            import_prep = current.manager.import_prep
            if import_prep:
                if not isinstance(tree, etree._ElementTree):
                    tree = etree.ElementTree(tree)
                callback(import_prep,
                         # takes tuple (resource, tree) as argument
                         (self, tree),
                         tablename=tablename)
                # Skip import?
                if self.skip_import:
                    _debug("Skipping import to %s" % self.tablename)
                    self.skip_import = False
                    return True

            # Select the elements for this table
            elements = xml.select_resources(tree, tablename)
            if not elements:
                # nothing to import => still ok
                return True

            # Find matching elements, if a target record ID is given
            UID = xml.UID
            if id and UID in table:
                if not isinstance(id, (tuple, list)):
                    query = (table._id == id)
                else:
                    query = (table._id.belongs(id))
                originals = db(query).select(table[UID])
                uids = [row[UID] for row in originals]
                matches = []
                import_uid = xml.import_uid
                append = matches.append
                for element in elements:
                    element_uid = import_uid(element.get(UID, None))
                    if not element_uid:
                        continue
                    if element_uid in uids:
                        append(element)
                if not matches:
                    first = elements[0]
                    if len(elements) and not first.get(UID, None):
                        first.set(UID, uids[0])
                        matches = [first]
                if not matches:
                    self.error = self.ERROR.NO_MATCH
                    return False
                else:
                    elements = matches

            # Import all matching elements
            import_job = S3ImportJob(table,
                                     tree=tree,
                                     files=self.files,
                                     strategy=strategy,
                                     update_policy=update_policy,
                                     conflict_policy=conflict_policy,
                                     last_sync=last_sync,
                                     onconflict=onconflict)
            add_item = import_job.add_item
            for element in elements:
                success = add_item(element=element,
                                   components=self.components)
                if not success:
                    self.error = import_job.error
                    self.error_tree = import_job.error_tree
            if self.error and not ignore_errors:
                return False

        # Commit the import job
        auth.rollback = not commit_job
        success = import_job.commit(ignore_errors=ignore_errors)
        auth.rollback = False
        self.error = import_job.error
        self.import_count += import_job.count
        self.import_created += import_job.created
        self.import_updated += import_job.updated
        self.import_deleted += import_job.deleted
        job_mtime = import_job.mtime
        if self.mtime is None or \
           job_mtime and job_mtime > self.mtime:
            self.mtime = job_mtime
        if self.error:
            if ignore_errors:
                self.error = "%s - invalid items ignored" % self.error
            self.error_tree = import_job.error_tree
        elif not success:
            # Oops - how could this happen? We can have an error
            # without failure, but not a failure without error!
            # If we ever get here, then there's a bug without a
            # chance to recover - hence let it crash:
            raise RuntimeError("Import failed without error message")
        if not success or not commit_job:
            db.rollback()
        if not commit_job:
            import_job.store()
            return import_job
        else:
            # Remove the job when committed
            if job_id is not None:
                import_job.delete()

        return self.error is None or ignore_errors

    # -------------------------------------------------------------------------
    # XML introspection
    # -------------------------------------------------------------------------
    def export_options(self,
                       component=None,
                       fields=None,
                       only_last=False,
                       show_uids=False,
                       as_json=False):
        """
            Export field options of this resource as element tree

            @param component: name of the component which the options are
                requested of, None for the primary table
            @param fields: list of names of fields for which the options
                are requested, None for all fields (which have options)
            @param as_json: convert the output into JSON
            @param only_last: Obtain the latest record (performance bug fix,
                timeout at s3_tb_refresh for non-dropdown form fields)
        """

        if component is not None:
            c = self.components.get(component, None)
            if c:
                tree = c.export_options(fields=fields,
                                        only_last=only_last,
                                        show_uids=show_uids,
                                        as_json=as_json)
                return tree
            else:
                raise AttributeError
        else:
            if as_json and only_last and len(fields) == 1:
                db = current.db
                component_tablename = "%s_%s" % (self.prefix, self.name)
                field = db[component_tablename][fields[0]]
                req = field.requires
                if isinstance(req, IS_EMPTY_OR):
                    req = req.other
                from s3validators import IS_LOCATION
                if not isinstance(req, (IS_ONE_OF, IS_LOCATION)):
                    raise RuntimeError, "not isinstance(req, IS_ONE_OF)"
                kfield = db[req.ktable][req.kfield]
                rows = db().select(kfield,
                                   orderby=~kfield,
                                   limitby=(0, 1))
                res = []
                for row in rows:
                    val = row[req.kfield]
                    represent = field.represent(val)
                    if isinstance(represent, A):
                        represent = represent.components[0]
                    res.append({"@value": val, "$": represent})
                return json.dumps({'option': res})

            xml = current.xml
            tree = xml.get_options(self.prefix,
                                   self.name,
                                   show_uids=show_uids,
                                   fields=fields)

            if as_json:
                return xml.tree2json(tree, pretty_print=False,
                                     native=True)
            else:
                return xml.tostring(tree, pretty_print=False)

    # -------------------------------------------------------------------------
    def export_fields(self, component=None, as_json=False):
        """
            Export a list of fields in the resource as element tree

            @param component: name of the component to lookup the fields
                              (None for primary table)
            @param as_json: convert the output XML into JSON
        """

        if component is not None:
            c = self.components.get(component, None)
            if c:
                tree = c.export_fields()
                return tree
            else:
                raise AttributeError
        else:
            xml = current.xml
            tree = xml.get_fields(self.prefix, self.name)
            if as_json:
                return xml.tree2json(tree, pretty_print=True)
            else:
                return xml.tostring(tree, pretty_print=True)

    # -------------------------------------------------------------------------
    def export_struct(self,
                      meta=False,
                      options=False,
                      references=False,
                      stylesheet=None,
                      as_json=False,
                      as_tree=False):
        """
            Get the structure of the resource

            @param options: include option lists in option fields
            @param references: include option lists even for reference fields
            @param stylesheet: the stylesheet to use for transformation
            @param as_json: convert into JSON after transformation
        """

        manager = current.manager
        xml = current.xml

        # Get the structure of the main resource
        root = etree.Element(xml.TAG.root)
        main = xml.get_struct(self.prefix, self.name,
                              alias=self.alias,
                              parent=root,
                              meta=meta,
                              options=options,
                              references=references)

        # Include the selected components
        for component in self.components.values():
            prefix = component.prefix
            name = component.name
            sub = xml.get_struct(prefix, name,
                                 alias=component.alias,
                                 parent=main,
                                 meta=meta,
                                 options=options,
                                 references=references)

        # Transformation
        tree = etree.ElementTree(root)
        if stylesheet is not None:
            tfmt = xml.ISOFORMAT
            args = dict(domain=manager.domain,
                        base_url=manager.s3.base_url,
                        prefix=self.prefix,
                        name=self.name,
                        utcnow=datetime.datetime.utcnow().strftime(tfmt))

            tree = xml.transform(tree, stylesheet, **args)
            if tree is None:
                return None

        # Return tree if requested
        if as_tree:
            return tree

        # Otherwise string-ify it
        if as_json:
            return xml.tree2json(tree, pretty_print=True)
        else:
            return xml.tostring(tree, pretty_print=True)

    # -------------------------------------------------------------------------
    # Data Model Helpers
    # -------------------------------------------------------------------------
    def validate(self, field, value, record=None):
        """
            Validates a value for a field

            @param fieldname: name of the field
            @param value: value to validate
            @param record: the existing database record, if available
        """

        table = self.table

        default = (value, None)

        if isinstance(field, str):
            fieldname = field
            if fieldname in table.fields:
                field = table[fieldname]
            else:
                return default
        else:
            fieldname = field.name

        self_id = None

        if record is not None:

            try:
                v = record[field]
            except KeyError:
                v = None
            if v and v == value:
                return default

            try:
                self_id = record[table._id]
            except KeyError:
                pass

        requires = field.requires

        if field.unique and not requires:
            # Prevent unique-constraint violations
            field.requires = IS_NOT_IN_DB(current.db, str(field))
            if self_id:
                field.requires.set_self_id(self_id)

        elif self_id:

            # Initialize all validators for self_id
            if not isinstance(requires, (list, tuple)):
                requires = [requires]
            for r in requires:
                if hasattr(r, "set_self_id"):
                    r.set_self_id(self_id)
                if hasattr(r, "other") and \
                    hasattr(r.other, "set_self_id"):
                    r.other.set_self_id(self_id)

        try:
            value, error = field.validate(value)
        except:
            # Oops - something went wrong in the validator:
            # write out a debug message, and continue anyway
            if current.response.s3.debug:
                from s3utils import s3_debug
                s3_debug("Validate %s: %s (ignored)" %
                         (field, sys.exc_info()[1]))
            return (None, None)
        else:
            return (value, error)

    # -------------------------------------------------------------------------
    @classmethod
    def original(cls, table, record, mandatory=None):
        """
            Find the original record for a possible duplicate:
                - if the record contains a UUID, then only that UUID is used
                  to match the record with an existing DB record
                - otherwise, if the record contains some values for unique
                  fields, all of them must match the same existing DB record

            @param table: the table
            @param record: the record as dict or S3XML Element
        """

        db = current.db
        xml = current.xml
        xml_decode = xml.xml_decode

        VALUE = xml.ATTRIBUTE["value"]
        UID = xml.UID
        ATTRIBUTES_TO_FIELDS = xml.ATTRIBUTES_TO_FIELDS

        # Get primary keys
        pkeys = [f for f in table.fields if table[f].unique]
        pvalues = Storage()

        # Get the values from record
        get = record.get
        if type(record) is etree._Element: #isinstance(record, etree._Element):
            xpath = record.xpath
            xexpr = "%s[@%s='%%s']" % (xml.TAG["data"],
                                       xml.ATTRIBUTE["field"])
            for f in pkeys:
                v = None
                if f == UID or f in ATTRIBUTES_TO_FIELDS:
                    v = get(f, None)
                else:
                    child = xpath(xexpr % f)
                    if child:
                        child = child[0]
                        v = child.get(VALUE, xml_decode(child.text))
                if v:
                    pvalues[f] = v
        elif isinstance(record, dict):
            for f in pkeys:
                v = get(f, None)
                if v:
                    pvalues[f] = v
        else:
            raise TypeError

        # Build match query
        query = None
        for f in pvalues:
            if f == UID:
                continue
            _query = (table[f] == pvalues[f])
            if query is not None:
                query = query | _query
            else:
                query = _query

        fields = cls.import_fields(table, pvalues, mandatory=mandatory)

        # Try to find exactly one match by non-UID unique keys
        if query is not None:
            original = db(query).select(limitby=(0, 2), *fields)
            if len(original) == 1:
                return original.first()

        # If no match, then try to find a UID-match
        if UID in pvalues:
            uid = xml.import_uid(pvalues[UID])
            query = (table[UID] == uid)
            original = db(query).select(limitby=(0, 1), *fields).first()
            if original:
                return original

        # No match or multiple matches
        return None

    # -------------------------------------------------------------------------
    @staticmethod
    def import_fields(table, data, mandatory=None):
        
        fnames = set(s3_all_meta_field_names())
        fnames.add(table._id.name)
        if mandatory:
            fnames |= set(mandatory)
        for fn in data:
            fnames.add(fn)
        return [table[fn] for fn in fnames if fn in table.fields]

    # -------------------------------------------------------------------------
    def readable_fields(self, subset=None):
        """
            Get a list of all readable fields in the resource table

            @param subset: list of fieldnames to limit the selection to
        """

        fkey = None
        table = self.table

        if self.parent and self.linked is None:
            component = self.parent.components.get(self.alias, None)
            if component:
                fkey = component.fkey
        elif self.linked is not None:
            component = self.linked
            if component:
                fkey = component.lkey

        if subset:
            return [ogetattr(table, f) for f in subset
                    if f in table.fields and \
                       ogetattr(table, f).readable and f != fkey]
        else:
            return [ogetattr(table, f) for f in table.fields
                    if ogetattr(table, f).readable and f != fkey]

    # -------------------------------------------------------------------------
    def resolve_selectors(self, selectors,
                          skip_components=False,
                          extra_fields=True,
                          show=True):
        """
            Resolve a list of field selectors against this resource

            @param selectors: the field selectors
            @param skip_components: skip fields in components
            @param extra_fields: automatically add extra_fields of all virtual
                                 fields in this table
            @param show: default for S3ResourceField.show

            @return: tuple of (fields, joins, left, distinct)
        """

        table = self.table

        prefix = lambda s: "~.%s" % s \
                           if "." not in s.split("$", 1)[0] else s

        # Store field selectors
        display_fields = []
        append = display_fields.append
        for _s in selectors:
            if isinstance(_s, tuple):
                s = _s[-1]
            else:
                s = _s
            if isinstance(s, S3ResourceField):
                selector = s.selector
            elif isinstance(s, S3FieldSelector):
                selector = s.name
            else:
                selector = s
            append(prefix(selector))
        slist = list(selectors)

        # Collect extra fields from virtual tables
        if extra_fields:
            append = slist.append
            extra = self.get_config("extra_fields", [])
            for selector in extra:
                s = prefix(selector)
                if s not in display_fields:
                    append(s)

        joins = Storage()
        left = Storage()

        distinct = False


        rfields = []
        columns = []
        append = rfields.append
        for s in slist:

            # Allow to override the field label
            if isinstance(s, tuple):
                label, selector = s
            else:
                label, selector = None, s

            # Resolve the selector
            if isinstance(selector, str):
                selector = prefix(selector)
                try:
                    rfield = S3ResourceField(self, selector, label=label)
                except (AttributeError, SyntaxError):
                    continue
            elif isinstance(selector, S3FieldSelector):
                try:
                    rfield = selector.resolve(self)
                except (AttributeError, SyntaxError):
                    continue
            elif isinstance(selector, S3ResourceField):
                rfield = selector
            else:
                continue

            # Unresolvable selector?
            if rfield.field is None and not rfield.virtual:
                continue

            # Replace default label
            if label is not None:
                rfield.label = label
                
            # Skip components
            if skip_components:
                head = rfield.selector.split("$", 1)[0]
                if "." in head and head.split(".")[0] not in ("~", self.alias):
                    continue

            # De-duplicate columns
            if rfield.colname in columns:
                continue
            else:
                columns.append(rfield.colname)

            # Resolve the joins
            if rfield.distinct:
                if rfield.left:
                    left.update(rfield.left)
                distinct = True
            elif rfield.join:
                joins.update(rfield.join)

            rfield.show = show and rfield.selector in display_fields
            append(rfield)

        return (rfields, joins, left, distinct)

    # -------------------------------------------------------------------------
    def resolve_selector(self, selector):
        """
            Wrapper for S3ResourceField, retained for backward compatibility
        """

        return S3ResourceField(self, selector)

    # -------------------------------------------------------------------------
    def split_fields(self, skip=[], data=None, references=None):
        """
            Split the readable fields in the resource table into
            reference and non-reference fields.

            @param skip: list of field names to skip
            @param data: data fields to include (None for all)
            @param references: foreign key fields to include (None for all)
        """

        rfields = self.rfields
        dfields = self.dfields

        if rfields is None or dfields is None:
            if self.tablename == "gis_location":
                if "wkt" not in skip:
                    # Skip Bulky WKT fields
                    skip.append("wkt")
                if current.deployment_settings.get_gis_spatialdb() and \
                   "the_geom" not in skip:
                    skip.append("the_geom")

            xml = current.xml
            UID = xml.UID
            IGNORE_FIELDS = xml.IGNORE_FIELDS
            FIELDS_TO_ATTRIBUTES = xml.FIELDS_TO_ATTRIBUTES

            show_ids = current.manager.show_ids
            rfields = []
            dfields = []
            table = self.table
            pkey = table._id.name
            for f in table.fields:
                if f == UID or \
                   f in skip or \
                   f in IGNORE_FIELDS:
                    if f != pkey or not show_ids:
                        continue
                if s3_has_foreign_key(table[f]) and \
                    f not in FIELDS_TO_ATTRIBUTES and \
                    (references is None or f in references):
                    rfields.append(f)
                elif data is None or \
                     f in data or \
                     f in FIELDS_TO_ATTRIBUTES:
                    dfields.append(f)
            self.rfields = rfields
            self.dfields = dfields

        return (rfields, dfields)

    # -------------------------------------------------------------------------
    # Utility functions
    # -------------------------------------------------------------------------
    def configure(self, **settings):
        """
            Update configuration settings for this resource

            @param settings: configuration settings for this resource
                             as keyword arguments
        """

        current.s3db.configure(self.tablename, **settings)

    # -------------------------------------------------------------------------
    def get_config(self, key, default=None):
        """
            Get a configuration setting for the current resource

            @param key: the setting key
            @param default: the default value to return if the setting
                            is not configured for this resource
        """

        return current.s3db.get_config(self.tablename, key, default=default)

    # -------------------------------------------------------------------------
    def limitby(self, start=0, limit=0):
        """
            Convert start+limit parameters into a limitby tuple
                - limit without start => start = 0
                - start without limit => limit = ROWSPERPAGE
                - limit 0 (or less)   => limit = 1
                - start less than 0   => start = 0

            @param start: index of the first record to select
            @param limit: maximum number of records to select
        """

        if limit is None:
            return None
            
        if start is None:
            start = 0
        if limit == 0:
            limit = current.manager.ROWSPERPAGE

        if limit <= 0:
            limit = 1
        if start < 0:
            start = 0

        return (start, start + limit)

    # -------------------------------------------------------------------------
    def get_join(self):
        """ Get join for this component """

        if self.parent is None:
            # This isn't a component
            return None
        else:
            ltable = self.parent.table

        rtable = self.table
        pkey = self.pkey
        fkey = self.fkey

        DELETED = current.manager.DELETED

        if self.linked:
            return self.linked.get_join()

        elif self.linktable:
            linktable = self.linktable
            lkey = self.lkey
            rkey = self.rkey
            join = ((ltable[pkey] == linktable[lkey]) &
                    (linktable[rkey] == rtable[fkey]))
            if DELETED in linktable:
                join = ((linktable[DELETED] != True) & join)

        else:
            join = (ltable[pkey] == rtable[fkey])
            if DELETED in rtable:
                join &= (rtable[DELETED] != True)

        if self.filter is not None:
            join &= self.filter

        return join

    # -------------------------------------------------------------------------
    def get_left_join(self):
        """ Get a left join for this component """

        if self.parent is None:
            # This isn't a component
            return None
        else:
            ltable = self.parent.table

        rtable = self.table
        pkey = self.pkey
        fkey = self.fkey

        DELETED = current.manager.DELETED

        if self.linked:
            return self.linked.get_left_join()

        elif self.linktable:
            linktable = self.linktable
            lkey = self.lkey
            rkey = self.rkey
            lquery = (ltable[pkey] == linktable[lkey])
            if DELETED in linktable:
                lquery &= (linktable[DELETED] != True)

            if self.filter is not None:
                rquery = (linktable[rkey] == rtable[fkey]) & self.filter
            else:    
                rquery = (linktable[rkey] == rtable[fkey])
                
            join = [linktable.on(lquery),
                    rtable.on(rquery)] 

        else:
            lquery = (ltable[pkey] == rtable[fkey])
            if DELETED in rtable:
                lquery &= (rtable[DELETED] != True)

            if self.filter is not None:
                lquery &= self.filter

            join = [rtable.on(lquery)]

        return join

    # -------------------------------------------------------------------------
    def link_id(self, master_id, component_id):
        """
            Helper method to find the link table entry ID for
            a pair of linked records.

            @param master_id: the ID of the master record
            @param component_id: the ID of the component record
        """

        if self.parent is None or self.linked is None:
            return None

        join = self.get_join()
        ltable = self.table
        mtable = self.parent.table
        ctable = self.linked.table
        query = join & \
                (mtable._id == master_id) & \
                (ctable._id == component_id)
        row = current.db(query).select(ltable._id, limitby=(0, 1)).first()
        if row:
            return row[ltable._id.name]
        else:
            return None

    # -------------------------------------------------------------------------
    def component_id(self, master_id, link_id):
        """
            Helper method to find the component record ID for
            a particular link of a particular master record

            @param link: the link (S3Resource)
            @param master_id: the ID of the master record
            @param link_id: the ID of the link table entry
        """

        if self.parent is None or self.linked is None:
            return None

        join = self.get_join()
        ltable = self.table
        mtable = self.parent.table
        ctable = self.linked.table
        query = join & (ltable._id == link_id)
        if master_id is not None:
            # master ID is redundant, but can be used to check negatives
            query &= (mtable._id == master_id)
        row = current.db(query).select(ctable._id, limitby=(0, 1)).first()
        if row:
            return row[ctable._id.name]
        else:
            return None

    # -------------------------------------------------------------------------
    def update_link(self, master, record):
        """
            Create a new link in a link table if it doesn't yet exist.
            This function is meant to also update links in "embed"
            actuation mode once this gets implemented, therefore the
            method name "update_link".

            @param master: the master record
            @param record: the new component record to be linked
        """

        if self.parent is None or self.linked is None:
            return None

        # Find the keys
        resource = self.linked
        pkey = resource.pkey
        lkey = resource.lkey
        rkey = resource.rkey
        fkey = resource.fkey
        if pkey not in master:
            return None
        _lkey = master[pkey]
        if fkey not in record:
            return None
        _rkey = record[fkey]
        if not _lkey or not _rkey:
            return None

        ltable = self.table
        ltn = ltable._tablename
        s3db = current.s3db
        onaccept = s3db.get_config(ltn, "create_onaccept",
                   s3db.get_config(ltn, "onaccept", None))

        # Create the link if it does not already exist
        query = ((ltable[lkey] == _lkey) &
                 (ltable[rkey] == _rkey))
        row = current.db(query).select(ltable._id, limitby=(0, 1)).first()
        if not row:
            form = Storage(vars=Storage({lkey:_lkey, rkey:_rkey}))
            link_id = ltable.insert(**form.vars)
            if link_id and onaccept:
                form.vars[ltable._id.name] = link_id
                callback(onaccept, form)
        else:
            link_id = row[ltable._id.name]
        return link_id

    # -------------------------------------------------------------------------
    def datatable_filter(self, fields, vars):
        """
            Parse datatable search/sort vars into a tuple of
            query, orderby and left joins

            @param fields: list of field selectors representing
                           the order of fields in the datatable (list_fields)
            @param vars: the datatable GET vars

            @return: tuple of (query, orderby, left joins)
        """

        db = current.db

        left_joins = S3LeftJoins(self.tablename)

        sSearch = "sSearch"
        iColumns = "iColumns"
        iSortingCols = "iSortingCols"

        parent = self.parent
        fkey = self.fkey

        # Skip joins for linked tables
        if self.linked is not None:
            skip = self.linked.tablename
        else:
            skip = None

        # Resolve the list fields
        rfields, j, l, d = self.resolve_selectors(fields)

        # FILTER --------------------------------------------------------------

        searchq = None
        if sSearch in vars and iColumns in vars:

            # Build filter
            text = vars[sSearch]
            words = [w for w in text.lower().split()]

            if words:
                try:
                    numcols = int(vars[iColumns])
                except ValueError:
                    numcols = 0

                flist = []
                for i in xrange(numcols):
                    try:
                        rfield = rfields[i]
                        field = rfield.field
                    except (KeyError, IndexError):
                        continue
                    if field is None:
                        continue
                    ftype = str(field.type)

                    # Add left joins
                    left_joins.extend(rfield.left)

                    if ftype[:9] == "reference" and \
                       hasattr(field, "sortby") and field.sortby:
                        # For foreign keys, we search through their sortby

                        # Get the lookup table
                        tn = ftype[10:]
                        if parent is not None and \
                           parent.tablename == tn and field.name != fkey:
                            alias = "%s_%s_%s" % (parent.prefix, "linked", parent.name)
                            ktable = db[tn].with_alias(alias)
                            ktable._id = ktable[ktable._id.name]
                            tn = alias
                        else:
                            ktable = db[tn]

                        # Add left join for lookup table
                        if tn != skip:
                            left_joins.add(ktable.on(field == ktable._id))

                        if isinstance(field.sortby, (list, tuple)):
                            flist.extend([ktable[f] for f in field.sortby
                                                    if f in ktable.fields])
                        else:
                            if field.sortby in ktable.fields:
                                flist.append(ktable[field.sortby])

                    else:
                        # Otherwise, we search through the field itself
                        flist.append(field)
                        
            # Build search query
            # @todo: migrate this to S3ResourceQuery?
            opts = Storage()
            queries = []
            for w in words:

                wqueries = []
                for field in flist:
                    query = None
                    ftype = str(field.type)
                    options = None
                    fname = str(field)
                    if fname in opts:
                        options = opts[fname]
                    elif ftype[:7] in ("integer",
                                       "list:in",
                                       "list:st",
                                       "referen",
                                       "list:re",
                                       "string"):
                        requires = field.requires
                        if not isinstance(requires, (list, tuple)):
                            requires = [requires]
                        if requires:
                            r = requires[0]
                            if isinstance(r, IS_EMPTY_OR):
                                r = r.other
                            if hasattr(r, "options"):
                                try:
                                    options = r.options()
                                except:
                                    options = []
                    if options is None and ftype in ("string", "text"):
                        wqueries.append(field.lower().like("%%%s%%" % w))
                    elif options is not None:
                        opts[fname] = options
                        vlist = [v for v, t in options
                                   if s3_unicode(t).lower().find(s3_unicode(w)) != -1]
                        if vlist:
                            wqueries.append(field.belongs(vlist))
                if len(wqueries):
                    queries.append(reduce(lambda x, y: x | y \
                                                 if x is not None else y,
                                          wqueries))
            if len(queries):
                searchq = reduce(lambda x, y: x & y \
                                        if x is not None else y, queries)

        # ORDERBY -------------------------------------------------------------

        orderby = []
        if iSortingCols in vars:

            # Sorting direction
            def direction(i):
                dir = vars["sSortDir_%s" % str(i)]
                return dir and " %s" % dir or ""

            # Get the fields to order by
            try:
                numcols = int(vars[iSortingCols])
            except:
                numcols = 0
            columns = []
            for i in xrange(numcols):
                try:
                    iSortCol = int(vars["iSortCol_%s" % i])
                    # Map sortable-column index to the real list_fields
                    # index: for every non-sortable column to the left
                    # of sortable column subtract 1
                    for j in xrange(iSortCol):
                        if vars.get("bSortable_%s" % j, "true") == "false":
                            iSortCol -= 1
                    rfield = rfields[iSortCol + 1]
                except:
                    # iSortCol_x is either not present in vars or specifies
                    # a non-existent column (i.e. iSortCol_x >= numcols) =>
                    # ignore silently
                    columns.append({"field": None})
                else:
                    columns.append(rfield)

            # Process the orderby-fields
            for i in xrange(len(columns)):
                rfield = columns[i]
                field = rfield.field
                if field is None:
                    continue
                ftype = str(field.type)

                if ftype[:9] == "reference" and \
                   hasattr(field, "sortby") and field.sortby:
                    # Foreign keys with sortby will be sorted by sortby
                    
                    # Get the lookup table
                    tn = ftype[10:]
                    if parent is not None and \
                       parent.tablename == tn and field.name != fkey:
                        alias = "%s_%s_%s" % (parent.prefix, "linked", parent.name)
                        ktable = db[tn].with_alias(alias)
                        ktable._id = ktable[ktable._id.name]
                        tn = alias
                    else:
                        ktable = db[tn]

                    # Add left joins for lookup table
                    if tn != skip:
                        left_joins.extend(rfield.left)
                        left_joins.add(ktable.on(field == ktable._id))

                    # Construct orderby from sortby
                    if not isinstance(field.sortby, (list, tuple)):
                        orderby.append("%s.%s%s" % (tn, field.sortby, direction(i)))
                    else:
                        orderby.append(", ".join(["%s.%s%s" %
                                                  (tn, fn, direction(i))
                                                  for fn in field.sortby]))

                else:
                    # Otherwise, we sort by the field itself
                    orderby.append("%s%s" % (field, direction(i)))

        if orderby:
            orderby = ", ".join(orderby)
        else:
            orderby = None

        left_joins = left_joins.as_list(tablenames=left_joins.joins.keys())
        return (searchq, orderby, left_joins)

    # -------------------------------------------------------------------------
    def axisfilter(self, axes):
        """
            Get all values for the given S3ResourceFields (axes) which
            match the resource query, used in pivot tables to filter out
            additional values where dimensions can have multiple values
            per record

            @param axes: the axis fields as list/tuple of S3ResourceFields

            @return: a dict with values per axis, only containes those
                     axes which are affected by the resource filter
        """

        axisfilter = {}

        qdict = self.get_query().as_dict(flat=True)

        for rfield in axes:
            field = rfield.field

            if field is None:
                # virtual field or unresolvable selector
                continue

            left_joins = S3LeftJoins(self.tablename)
            left_joins.extend(rfield.left)

            tablenames = left_joins.joins.keys()
            tablenames.append(self.tablename)
            af = S3AxisFilter(qdict, tablenames)

            if af.op is not None:
                query = af.query()
                left = left_joins.as_list()

                # @todo: this does not work with virtual fields: need
                # to retrieve all extra_fields for the dimension table
                # and can't groupby (=must deduplicate afterwards)
                rows = current.db(query).select(field,
                                                left=left,
                                                groupby=field)
                colname = rfield.colname
                if rfield.ftype[:5] == "list:":
                    values = []
                    vappend = values.append
                    for row in rows:
                        v = row[colname]
                        if v:
                            vappend(v)
                    values = set(chain.from_iterable(values))
                    
                    include, exclude = af.values(rfield)
                    fdict = {}
                    if include:
                        for v in values:
                            vstr = s3_unicode(v)
                            if vstr in include and vstr not in exclude:
                                fdict[v] = None
                    else:
                        fdict = dict((v, None) for v in values)
                        
                    axisfilter[colname] = fdict
                    
                else:
                    axisfilter[colname] = dict((row[colname], None)
                                               for row in rows)

        return axisfilter

    # -------------------------------------------------------------------------
    @classmethod
    def sortleft(cls, joins):
        """
            Sort a list of left-joins by their interdependency

            @param joins: the list of joins
        """

        if len(joins) <= 1:
            return joins
        r = list(joins)

        tables = current.db._adapter.tables

        append = r.append
        head = None
        for i in xrange(len(joins)):
            join = r.pop(0)
            head = join
            tablenames = tables(join.second)
            for j in r:
                try:
                    tn = j.first._tablename
                except AttributeError:
                    tn = str(j.first)
                if tn in tablenames:
                    head = None
                    break
            if head is not None:
                break
            else:
                append(join)
        if head is not None:
            return [head] + cls.sortleft(r)
        else:
            raise RuntimeError("circular left-join dependency")

    # -------------------------------------------------------------------------
    def prefix_selector(self, selector):
        """
            Helper method to ensure consistent prefixing of field selectors

            @param selector: the selector
        """

        head = selector.split("$", 1)[0]
        if "." in head:
            prefix = head.split(".", 1)[0]
            if prefix == self.alias:
                return selector.replace("%s." % prefix, "~.")
            else:
                return selector
        else:
            return "~.%s" % selector

    # -------------------------------------------------------------------------
    def list_fields(self, key="list_fields", id_column=0):
        """
            Get the list_fields for this resource

            @param key: alternative key for the table configuration
            @param id_column: True/False, whether to include the record ID
                              or not, or 0 to enforce the record ID to be
                              the first column
        """

        list_fields = self.get_config(key, None)
        if not list_fields and key != "list_fields":
            list_fields = self.get_config("list_fields", None)
        if not list_fields:
            list_fields = [f.name for f in self.readable_fields()]

        pkey = _pkey = self._id.name
        fields = []
        append = fields.append
        selectors = set()
        seen = selectors.add
        for f in list_fields:
            selector = f if type(f) is not tuple else f[1]
            if selector == _pkey and not id_column:
                pkey = f
            elif selector not in selectors:
                seen(selector)
                append(f)
        if id_column is 0:
            fields.insert(0, pkey)
        return fields
        
# =============================================================================
class S3LeftJoins(object):

    def __init__(self, tablename, joins=None):
        """
            Constructor

            @param tablename: the tablename
            @param joins: list of left joins
        """

        self.tablename = tablename
        self.joins = {}
        self.tables = []

        self.add(joins)

    # -------------------------------------------------------------------------
    def __iter__(self):

        return self.joins.__iter__()

    # -------------------------------------------------------------------------
    def __getitem__(self, key):

        return self.joins.__getitem__(key)

    # -------------------------------------------------------------------------
    def __setitem__(self, key, value):

        tablename = self.tablename
        joins = self.joins
        tables = current.db._adapter.tables

        joins[key] = value
        if len(value) > 1:
            for join in value:
                try:
                    tname = join.first._tablename
                except AttributeError:
                    tname = str(join.first)
                if tname not in joins and \
                   tablename in tables(join.second):
                    joins[tname] = [join]
        self.tables.append(key)
        return

    # -------------------------------------------------------------------------
    def keys(self):

        return self.joins.keys()

    # -------------------------------------------------------------------------
    def items(self):

        return self.joins.items()

    # -------------------------------------------------------------------------
    def values(self):

        return self.joins.values()

    # -------------------------------------------------------------------------
    def add(self, joins):

        tablenames = []
        if joins:
            if not isinstance(joins, (list, tuple)):
                joins = [joins]
            for join in joins:
                tablename = join.first._tablename
                self[tablename] = [join]
                tablenames.append(tablename)
        return tablenames

    # -------------------------------------------------------------------------
    def extend(self, other):

        if type(other) is S3LeftJoins:
            joins = self.joins
            append = self.tables.append
        else:
            joins = self
            append = None
        joins = self.joins if type(other) is S3LeftJoins else self
        tables = self.tables
        for tablename in other:
            if tablename not in self.joins:
                joins[tablename] = other[tablename]
                if append:
                    append(tablename)
        return other.keys()

    # -------------------------------------------------------------------------
    def __repr__(self):

        return "<S3LeftJoins %s>" % str([str(j) for j in self.as_list()])

    # -------------------------------------------------------------------------
    def as_list(self, tablenames=None, aqueries=None):

        s3db = current.s3db
        accessible_query = current.auth.s3_accessible_query

        if tablenames is None:
            tablenames = list(set(self.tables))
        else:
            tablenames = list(set(tablenames))

        joins = self.joins

        joins_dict = {}
        for tablename in tablenames:

            if tablename not in joins or tablename == self.tablename:
                continue
            for join in joins[tablename]:
                j = join
                table = j.first
                tname = table._tablename
                if aqueries is not None and tname in tablenames:
                    if tname not in aqueries:
                        aquery = accessible_query("read", table)
                        aqueries[tname] = aquery
                    else:
                        aquery = aqueries[tname]
                    if aquery is not None:
                        j = join.first.on(join.second & aquery)
                joins_dict[tname] = j
        try:
            return self.sort(joins_dict.values())
        except RuntimeError:
            return joins_dict.values()

    # -------------------------------------------------------------------------
    @classmethod
    def sort(cls, joins):
        """
            Sort a list of left-joins by their interdependency

            @param joins: the list of joins
        """

        if len(joins) <= 1:
            return joins
        r = list(joins)

        tables = current.db._adapter.tables

        append = r.append
        head = None
        for i in xrange(len(joins)):
            join = r.pop(0)
            head = join
            tablenames = tables(join.second)
            for j in r:
                try:
                    tn = j.first._tablename
                except AttributeError:
                    tn = str(j.first)
                if tn in tablenames:
                    head = None
                    break
            if head is not None:
                break
            else:
                append(join)
        if head is not None:
            return [head] + cls.sort(r)
        else:
            raise RuntimeError("circular left-join dependency")

# =============================================================================
class S3FieldSelector(object):
    """ Helper class to construct a resource query """

    LOWER = "lower"
    UPPER = "upper"

    OPERATORS = [LOWER, UPPER]

    def __init__(self, name, type=None):
        """ Constructor """

        if not isinstance(name, basestring) or not name:
            raise SyntaxError("name required")
        self.name = str(name)
        self.type = type

        self.op = None

    # -------------------------------------------------------------------------
    def __lt__(self, value):
        return S3ResourceQuery(S3ResourceQuery.LT, self, value)

    # -------------------------------------------------------------------------
    def __le__(self, value):
        return S3ResourceQuery(S3ResourceQuery.LE, self, value)

    # -------------------------------------------------------------------------
    def __eq__(self, value):
        return S3ResourceQuery(S3ResourceQuery.EQ, self, value)

    # -------------------------------------------------------------------------
    def __ne__(self, value):
        return S3ResourceQuery(S3ResourceQuery.NE, self, value)

    # -------------------------------------------------------------------------
    def __ge__(self, value):
        return S3ResourceQuery(S3ResourceQuery.GE, self, value)

    # -------------------------------------------------------------------------
    def __gt__(self, value):
        return S3ResourceQuery(S3ResourceQuery.GT, self, value)

    # -------------------------------------------------------------------------
    def like(self, value):
        return S3ResourceQuery(S3ResourceQuery.LIKE, self, value)

    # -------------------------------------------------------------------------
    def belongs(self, value):
        return S3ResourceQuery(S3ResourceQuery.BELONGS, self, value)

    # -------------------------------------------------------------------------
    def contains(self, value):
        return S3ResourceQuery(S3ResourceQuery.CONTAINS, self, value)

    # -------------------------------------------------------------------------
    def anyof(self, value):
        return S3ResourceQuery(S3ResourceQuery.ANYOF, self, value)

    # -------------------------------------------------------------------------
    def lower(self):
        self.op = self.LOWER
        return self

    # -------------------------------------------------------------------------
    def upper(self):
        self.op = self.UPPER
        return self

    # -------------------------------------------------------------------------
    def expr(self, val):

        if self.op and val is not None:
            if self.op == self.LOWER and \
               hasattr(val, "lower") and callable(val.lower) and \
               (not isinstance(val, Field) or val.type in TEXTTYPES):
                return val.lower()
            elif self.op == self.UPPER and \
                 hasattr(val, "upper") and callable(val.upper) and \
                 (not isinstance(val, Field) or val.type in TEXTTYPES):
                return val.upper()
        return val

    # -------------------------------------------------------------------------
    def represent(self, resource):

        try:
            rfield = S3ResourceField(resource, self.name)
        except:
            colname = None
        else:
            colname = rfield.colname
        if colname:
            if self.op is not None:
                return "%s.%s()" % (colname, self.op)
            else:
                return colname
        else:
            return "(%s?)" % self.name

    # -------------------------------------------------------------------------
    @classmethod
    def extract(cls, resource, row, field):
        """
            Extract a value from a Row

            @param resource: the resource
            @param row: the Row
            @param field: the field

            @return: field if field is not a Field/S3FieldSelector instance,
                      the value from the row otherwise
        """

        error = lambda fn: KeyError("Field not found: %s" % fn)

        t = type(field)
        
        if isinstance(field, Field):
            f = field
            colname = str(field)
            tname, fname = colname.split(".", 1)

        elif t is S3FieldSelector:
            rfield = S3ResourceField(resource, field.name)
            colname = rfield.colname
            if not colname:
                # unresolvable selector
                raise error(field.name)
            fname = rfield.fname
            f = rfield.field
            tname = rfield.tname

        elif t is S3ResourceField:
            colname = field.colname
            if not colname:
                # unresolved selector
                return None
            fname = field.fname
            f = field.field
            tname = field.tname

        else:
            return field

        if type(row) is Row:
            try:
                if tname in row.__dict__:
                    value = ogetattr(ogetattr(row, tname), fname)
                else:
                    value = ogetattr(row, fname)
            except:
                try:
                    value = row[colname]
                except (KeyError, AttributeError):
                    raise error(colname)
        elif fname in row:
            value = row[fname]
        elif colname in row:
            value = row[colname]
        elif tname is not None and \
             tname in row and fname in row[tname]:
            value = row[tname][fname]
        else:
            raise error(colname)

        if callable(value):
            # Lazy virtual field
            try:
                value = value()
            except:
                if current.response.s3.debug:
                    from s3utils import s3_debug
                    s3_debug(sys.exc_info()[1])
                value = None

        if hasattr(field, "expr"):
            return field.expr(value)
        return value

    # -------------------------------------------------------------------------
    def resolve(self, resource):
        """
            Resolve this field against a resource

            @param resource: the resource
        """
        return S3ResourceField(resource, self.name)

# =============================================================================
class S3FieldPath(object):
    """ Helper class to parse field selectors """

    # -------------------------------------------------------------------------
    @classmethod
    def resolve(cls, resource, selector, tail=None):
        """
            Resolve a selector (=field path) against a resource

            @param resource: the S3Resource to resolve against
            @param selector: the field selector string
            @param tail: tokens to append to the selector
            
            The general syntax for a selector is:

            selector = {[alias].}{[key]$}[field|selector]

            (Parts in {} are optional, | indicates alternatives)

            * Alias can be:

            ~           refers to the resource addressed by the
                        preceding parts of the selector (=last
                        resource)
            component   alias of a component of the last resource
            linktable   alias of a link table of the last resource
            table       name of a table that has a foreign key for
                        the last resource (auto-detect the key)
            key:table   same as above, but specifying the foreign key

            * Key can be:

            key         the name of a foreign key in the last resource
            context     a context expression
            
            * Field can be:

            fieldname   the name of a field or virtual field of the
                        last resource
            context     a context expression

            A "context expression" is a name enclosed in parentheses:

            (context)

            During parsing, context expressions get replaced by the
            string which has been configured for this name for the
            last resource with:

            s3db.configure(tablename, context = dict(name = "string"))

            With context expressions, the same selector can be used
            for different resources, each time resolving into the
            specific field path. However, the field addressed must
            be of the same type in all resources to form valid
            queries.
            
            If a context name can not be resolved, resolve() will
            still succeed - but the S3FieldPath returned will have
            colname=None and ftype="context" (=unresolvable context).
        """

        if not selector:
            raise SyntaxError("Invalid selector: %s" % selector)
        tokens = re.split("(\.|\$)", selector)
        if tail:
            tokens.extend(tail)
        parser = cls(resource, None, tokens)
        parser.original = selector
        return parser

    # -------------------------------------------------------------------------
    def __init__(self, resource, table, tokens):
        """
            Constructor - not to be called directly, use resolve() instead

            @param resource: the S3Resource
            @param table: the table
            @param tokens: the tokens as list
        """

        s3db = current.s3db
        
        if table is None:
            table = resource.table

        # Initialize
        self.original = None
        self.tname = table._tablename
        self.fname = None
        self.field = None
        self.ftype = None
        self.virtual = False
        self.colname = None
        self.left = Storage()
        self.join = Storage()

        self.distinct = False
        self.multiple = True

        head = tokens.pop(0)
        tail = None

        field_not_found = lambda f: AttributeError("Field not found: %s" % f)

        if head and head[0] == "(" and head[-1] == ")":

            # Context expression
            head = head.strip("()")
            self.fname = head
            self.ftype = "context"

            if not resource:
                resource = s3db.resource(table, components=[])
            context = resource.get_config("context")
            if context and head in context:
                tail = self.resolve(resource, context[head], tail=tokens)
            else:
                # unresolvable
                pass

        elif tokens:

            # Resolve the tail
            op = tokens.pop(0)
            if tokens:
                if op == ".":
                    # head is a component or linktable alias, and tokens is
                    # a field expression in the component/linked table
                    if not resource:
                        resource = s3db.resource(table, components=[])
                    ktable, j, l, m, d = self._resolve_alias(resource, head)
                    if j is not None and l is not None:
                        self.join[ktable._tablename] = j
                        self.left[ktable._tablename] = l
                    self.multiple = m
                    self.distinct = d
                    tail = S3FieldPath(None, ktable, tokens)

                else:
                    # head is a foreign key in the current table and tokens is
                    # a field expression in the referenced table
                    ktable, join, left = self._resolve_key(table, head)
                    if join is not None and left is not None:
                        self.join[ktable._tablename] = join
                        self.left[ktable._tablename] = left
                    tail = S3FieldPath(None, ktable, tokens)
                    self.distinct = True
            else:
                raise SyntaxError("trailing operator")

        if tail is None:

            # End of the expression
            if self.ftype != "context":
                # Expression is resolved, head is a field name:
                self.field = self._resolve_field(table, head)
                if not self.field:
                    self.virtual = True
                    self.ftype = "virtual"
                else:
                    self.virtual = False
                    self.ftype = str(self.field.type)
                self.fname = head
                self.colname = "%s.%s" % (self.tname, self.fname)

        else:

            # Read field data from tail
            self.tname = tail.tname
            self.fname = tail.fname
            self.field = tail.field
            self.ftype = tail.ftype
            self.virtual = tail.virtual
            self.colname = tail.colname
            
            self.distinct |= tail.distinct
            self.multiple |= tail.multiple

            self.join.update(tail.join)
            self.left.update(tail.left)

    # -------------------------------------------------------------------------
    @staticmethod
    def _resolve_field(table, fieldname):
        """
            Resolve a field name against the table, recognizes "id" as
            table._id.name, and "uid" as current.xml.UID.

            @param table: the Table
            @param fieldname: the field name

            @return: the Field
        """

        if fieldname == "uid":
            fieldname == current.xml.UID
        if fieldname == "id":
            field = table._id
        elif fieldname in table.fields:
            field = ogetattr(table, fieldname)
        else:
            field = None
        return field

    # -------------------------------------------------------------------------
    @staticmethod
    def _resolve_key(table, fieldname):
        """
            Resolve a foreign key into the referenced table and the
            join and left join between the current table and the
            referenced table

            @param table: the current Table
            @param fieldname: the fieldname of the foreign key

            @return: tuple of (referenced table, join, left join)
            @raise: AttributeError is either the field or
                    the referended table are not found
            @raise: SyntaxError if the field is not a foreign key
        """

        if fieldname in table.fields:
            f = table[fieldname]
        else:
            raise AttributeError("key not found: %s" % fieldname)

        ktablename, pkey, multiple = s3_get_foreign_key(f, m2m=False)

        if not ktablename:
            raise SyntaxError("%s is not a foreign key" % f)

        ktable = current.s3db.table(ktablename,
                                    AttributeError("undefined table %s" % ktablename),
                                    db_only=True)

        pkey = ktable[pkey] if pkey else ktable._id

        join = (f == pkey)
        left = [ktable.on(join)]

        return ktable, join, left

    # -------------------------------------------------------------------------
    @staticmethod
    def _resolve_alias(resource, alias):
        """
            Resolve a table alias into the linked table (component, linktable
            or free join), and the joins and left joins between the current
            resource and the linked table.

            @param resource: the current S3Resource
            @param alias: the alias

            @return: tuple of (linked table, joins, left joins, multiple,
                     distinct), the two latter being flags to indicate
                     possible ambiguous query results (needed by the query
                     builder)
            @raise: AttributeError if one of the key fields or tables
                    can not be found
            @raise: SyntaxError if the alias can not be resolved (e.g.
                    because on of the keys isn't a foreign key, points
                    to the wrong table or is ambiguous)
        """

        # Alias for this resource?
        if alias in ("~", resource.alias):
            return resource.table, None, None, False, False

        multiple = True
        s3db = current.s3db

        tablename = resource.tablename

        # Try to attach the component
        if alias not in resource.components and \
           alias not in resource.links:
            _alias = alias
            hook = s3db.get_component(tablename, alias)
            if not hook:
                _alias = s3db.get_alias(tablename, alias)
                if _alias:
                    hook = s3db.get_component(tablename, _alias)
            if hook:
                resource._attach(_alias, hook)

        components = resource.components
        links = resource.links

        if alias in components:

            # Is a component
            component = components[alias]

            ktable = component.table
            join = component.get_join()
            left = component.get_left_join()
            multiple = component.multiple

        elif alias in links:

            # Is a linktable
            link = links[alias]

            ktable = link.table
            join = link.get_join()
            left = link.get_left_join()

        elif "_" in alias:

            # Is a free join
            DELETED = current.manager.DELETED

            table = resource.table
            tablename = resource.tablename

            pkey = fkey = None

            # Find the table
            fkey, kname = (alias.split(":") + [None])[:2]
            if not kname:
                fkey, kname = kname, fkey

            ktable = s3db.table(kname,
                                AttributeError("table not found: %s" % kname),
                                db_only=True)

            if fkey is None:

                # Autodetect left key
                for fname in ktable.fields:
                    tn, key, m = s3_get_foreign_key(ktable[fname], m2m=False)
                    if not tn:
                        continue
                    if tn == tablename:
                        if fkey is not None:
                            raise SyntaxError("ambiguous foreign key in %s" %
                                              alias)
                        else:
                            fkey = fname
                            if key:
                                pkey = key
                if fkey is None:
                    raise SyntaxError("no foreign key for %s in %s" %
                                      (tablename, kname))

            else:

                # Check left key
                if fkey not in ktable.fields:
                    raise AttributeError("no field %s in %s" % (fkey, kname))
                
                tn, pkey, m = s3_get_foreign_key(ktable[fkey], m2m=False)
                if tn and tn != tablename:
                    raise SyntaxError("%s.%s is not a foreign key for %s" %
                                      (kname, fkey, tablename))
                elif not tn:
                    raise SyntaxError("%s.%s is not a foreign key" %
                                      (kname, fkey))

            # Default primary key
            if pkey is None:
                pkey = table._id.name
                    
            # Build join
            join = (table[pkey] == ktable[fkey])
            if DELETED in ktable.fields:
                join &= ktable[DELETED] != True
            left = [ktable.on(join)]

        else:
            raise SyntaxError("Invalid tablename: %s" % alias)

        return ktable, join, left, multiple, True

# =============================================================================
class S3ResourceField(object):
    """ Helper class to resolve a field selector against a resource """

    # -------------------------------------------------------------------------
    def __init__(self, resource, selector, label=None):
        """
            Constructor

            @param resource: the resource
            @param selector: the field selector (string)
        """

        self.resource = resource
        self.selector = selector

        lf = S3FieldPath.resolve(resource, selector)

        self.tname = lf.tname
        self.fname = lf.fname
        self.colname = lf.colname

        self.join = lf.join
        self.left = lf.left
        self.distinct = lf.distinct
        self.multiple = lf.multiple

        self.field = lf.field

        self.virtual = False
        self.represent = s3_unicode
        self.requires = None

        if self.field is not None:
            field = self.field
            self.ftype = str(field.type)
            if resource.linked is not None and self.ftype == "id":
                # Always represent the link-table's ID as the
                # linked record's ID => needed for data tables
                self.represent = lambda i, resource=resource: \
                                           resource.component_id(None, i)
            else:
                self.represent = field.represent
            self.requires = field.requires
        elif self.colname:
            self.virtual = True
            self.ftype = "virtual"
        else:
            self.ftype = "context"

        # Fall back to the field label
        if label is None:
            fname = self.fname
            if fname in ["L1", "L2", "L3", "L3", "L4", "L5"]:
                try:
                    label = current.gis.get_location_hierarchy(fname)
                except:
                    label = None
            elif fname == "L0":
                label = current.messages.COUNTRY
            if label is None:
                f = self.field
                if f:
                    label = f.label
                elif fname:
                    label = " ".join([s.strip().capitalize()
                                      for s in fname.split("_") if s])
                else:
                    label = None

        self.label = label
        self.show = True

    # -------------------------------------------------------------------------
    def __repr__(self):
        """ String representation of this instance """

        return "<S3ResourceField " \
               "selector='%s' " \
               "label='%s' " \
               "table='%s' " \
               "field='%s' " \
               "type='%s'>" % \
               (self.selector, self.label, self.tname, self.fname, self.ftype)

    # -------------------------------------------------------------------------
    def extract(self, row, represent=False, lazy=False):
        """
            Extract the value for this field from a row

            @param row: the Row
            @param represent: render a text representation for the value
            @param lazy: return a lazy representation handle if available
        """

        field = self.field
        tname = self.tname
        fname = self.fname
        colname = self.colname
        error = "Field not found in Row: %s" % colname

        if type(row) is Row:
            try:
                if tname in row.__dict__:
                    value = ogetattr(ogetattr(row, tname), fname)
                else:
                    value = ogetattr(row, fname)
            except:
                try:
                    value = row[colname]
                except (KeyError, AttributeError):
                    raise KeyError(error)
        elif fname in row:
            value = row[fname]
        elif colname in row:
            value = row[colname]
        elif tname is not None and \
             tname in row and fname in row[tname]:
            value = row[tname][fname]
        else:
            raise KeyError(error)

        if callable(value):
            # Lazy virtual field
            try:
                value = value()
            except:
                if current.response.s3.debug:
                    from s3utils import s3_debug
                    s3_debug(sys.exc_info()[1])
                value = None

        if represent:
            renderer = self.represent
            if callable(renderer):
                if lazy and hasattr(renderer, "bulk"):
                    return S3RepresentLazy(value, renderer)
                else:
                    return renderer(value)
            else:
                return s3_unicode(value)
        else:
            return value

# =============================================================================
class S3ResourceQuery(object):
    """
        Helper class representing a resource query
        - unlike DAL Query objects, these can be converted to/from URL filters
    """

    # Supported operators
    NOT = "not"
    AND = "and"
    OR = "or"
    LT = "lt"
    LE = "le"
    EQ = "eq"
    NE = "ne"
    GE = "ge"
    GT = "gt"
    LIKE = "like"
    BELONGS = "belongs"
    CONTAINS = "contains"
    ANYOF = "anyof"

    OPERATORS = [NOT, AND, OR,
                 LT, LE, EQ, NE, GE, GT,
                 LIKE, BELONGS, CONTAINS, ANYOF]

    # -------------------------------------------------------------------------
    def __init__(self, op, left=None, right=None):
        """ Constructor """

        if op not in self.OPERATORS:
            raise SyntaxError("Invalid operator: %s" % op)

        self.op = op

        self.left = left
        self.right = right

    # -------------------------------------------------------------------------
    def __and__(self, other):
        """ AND """

        return S3ResourceQuery(self.AND, self, other)

    # -------------------------------------------------------------------------
    def __or__(self, other):
        """ OR """

        return S3ResourceQuery(self.OR, self, other)

    # -------------------------------------------------------------------------
    def __invert__(self):
        """ NOT """

        if self.op == self.NOT:
            return self.left
        else:
            return S3ResourceQuery(self.NOT, self)

    # -------------------------------------------------------------------------
    def joins(self, resource, left=False):
        """
            Get a Storage {tablename: join} for this query.

            @param resource: the resource to resolve the query against
            @param left: get left joins rather than inner joins
        """

        op = self.op
        l = self.left
        r = self.right
        distinct = False

        if op in (self.AND, self.OR):
            ljoins, ld = l.joins(resource, left=left)
            rjoins, rd = r.joins(resource, left=left)
            ljoins = Storage(ljoins)
            ljoins.update(rjoins)
            return (ljoins, ld or rd)
        elif op == self.NOT:
            return l.joins(resource, left=left)
        if isinstance(l, S3FieldSelector):
            try:
                rfield = l.resolve(resource)
            except:
                return (Storage(), False)
            if rfield.distinct:
                if left:
                    return (rfield.left, True)
                else:
                    return (Storage(), True)
            else:
                if left:
                    return (Storage(), False)
                else:
                    return (rfield.join, False)
        return(Storage(), False)

    # -------------------------------------------------------------------------
    def fields(self):
        """ Get all field selectors involved with this query """

        op = self.op
        l = self.left
        r = self.right

        if op in (self.AND, self.OR):
            lf = l.fields()
            rf = r.fields()
            return lf + rf
        elif op == self.NOT:
            return l.fields()
        elif isinstance(l, S3FieldSelector):
            return [l.name]
        else:
            return []

    # -------------------------------------------------------------------------
    def split(self, resource):
        """
            Split this query into a real query and a virtual one (AND)

            @param resource: the S3Resource
            @return: tuple (DAL-translatable sub-query, virtual filter),
                     both S3ResourceQuery instances
        """

        op = self.op
        l = self.left
        r = self.right

        if op == self.AND:
            lq, lf = l.split(resource)
            rq, rf = r.split(resource)
            q = lq
            if rq is not None:
                if q is not None:
                    q &= rq
                else:
                    q = rq
            f = lf
            if rf is not None:
                if f is not None:
                    f &= rf
                else:
                    f = rf
            return q, f
        elif op == self.OR:
            lq, lf = l.split(resource)
            rq, rf = r.split(resource)
            if lf is not None or rf is not None:
                return None, self
            else:
                q = lq
                if rq is not None:
                    if q is not None:
                        q |= rq
                    else:
                        q = rq
                return q, None
        elif op == self.NOT:
            if l.op == self.OR:
                i = (~(l.left)) & (~(l.right))
                return i.split(resource)
            else:
                q, f = l.split(resource)
                if q is not None and f is not None:
                    return None, self
                elif q is not None:
                    return ~q, None
                elif f is not None:
                    return None, ~f

        l = self.left
        try:
            if isinstance(l, S3FieldSelector):
                lfield = l.resolve(resource)
            else:
                lfield = S3ResourceField(resource, l)
        except:
            lfield = None
        if not lfield or lfield.field is None:
            return None, self
        else:
            return self, None

    # -------------------------------------------------------------------------
    def transform(self, resource):
        """
            Placeholder for transformation method

            @param resource: the S3Resource
        """

        # @todo: implement
        return self
        
    # -------------------------------------------------------------------------
    def query(self, resource):
        """
            Convert this S3ResourceQuery into a DAL query, ignoring virtual
            fields (the necessary joins for this query can be constructed
            with the joins() method)

            @param resource: the resource to resolve the query against
        """

        op = self.op
        l = self.left
        r = self.right

        # Resolve query components
        if op == self.AND:
            l = l.query(resource)
            r = r.query(resource)
            if l is None or r is None:
                return None
            elif l is False or r is False:
                return l if r is False else r if l is False else False
            else:
                return l & r
        elif op == self.OR:
            l = l.query(resource)
            r = r.query(resource)
            if l is None or r is None:
                return None
            elif l is False or r is False:
                return l if r is False else r if l is False else False
            else:
                return l | r
        elif op == self.NOT:
            l = l.query(resource)
            if l is None:
                return None
            elif l is False:
                return False
            else:
                return ~l

        # Resolve the fields
        if isinstance(l, S3FieldSelector):
            try:
                rfield = S3ResourceField(resource, l.name)
            except:
                return None
            if rfield.virtual:
                return None
            elif not rfield.field:
                return False
            lfield = l.expr(rfield.field)
        elif isinstance(l, Field):
            lfield = l
        else:
            return None # not a field at all
        if isinstance(r, S3FieldSelector):
            try:
                rfield = S3ResourceField(resource, r.name)
            except:
                return None
            rfield = rfield.field
            if rfield.virtual:
                return None
            elif not rfield.field:
                return False
            rfield = r.expr(rfield.field)
        else:
            rfield = r

        # Resolve the operator
        invert = False
        query_bare = self._query_bare
        ftype = str(lfield.type)
        if isinstance(rfield, (list, tuple)) and ftype[:4] != "list":
            if op == self.EQ:
                op = self.BELONGS
            elif op == self.NE:
                op = self.BELONGS
                invert = True
            elif op != self.BELONGS:
                query = None
                for v in rfield:
                    q = query_bare(op, lfield, v)
                    if q is not None:
                        if query is None:
                            query = q
                        else:
                            query |= q
                return query

        # Convert date(time) strings
        if ftype  == "datetime" and \
           isinstance(rfield, basestring):
            rfield = S3TypeConverter.convert(datetime.datetime, rfield)
        elif ftype  == "date" and \
             isinstance(rfield, basestring):
            rfield = S3TypeConverter.convert(datetime.date, rfield)
            
        query = query_bare(op, lfield, rfield)
        if invert:
            query = ~(query)
        return query

    # -------------------------------------------------------------------------
    def _query_bare(self, op, l, r):
        """
            Translate a filter expression into a DAL query

            @param op: the operator
            @param l: the left operand
            @param r: the right operand
        """

        if op == self.CONTAINS:
            q = l.contains(r, all=True)
        elif op == self.ANYOF:
            q = l.contains(r, all=False)
        elif op == self.BELONGS:
            if type(r) is not list:
                r = [r]
            if None in r:
                _r = [item for item in r if item is not None]
                q = ((l.belongs(_r)) | (l == None))
            else:
                q = l.belongs(r)
        elif op == self.LIKE:
            # Fixed in web2py trunk by:
            # https://github.com/web2py/web2py/commit/7b4a0515becf3a6b7ffd145d7a1e00c11ede9b91
            # for earlier versions, use this instead as a workaround:
            #if isinstance(l, Field) and l.type not in TEXTTYPES:
                #q = (l == s3_unicode(r).replace("%", ""))
            #else:
                #q = l.like(s3_unicode(r))
            q = l.like(s3_unicode(r))
        elif op == self.LT:
            q = l < r
        elif op == self.LE:
            q = l <= r
        elif op == self.EQ:
            q = l == r
        elif op == self.NE:
            q = l != r
        elif op == self.GE:
            q = l >= r
        elif op == self.GT:
            q = l > r
        else:
            q = None
        return q

    # -------------------------------------------------------------------------
    def __call__(self, resource, row, virtual=True):
        """
            Probe whether the row matches the query

            @param resource: the resource to resolve the query against
            @param row: the DB row
            @param virtual: execute only virtual queries
        """

        if self.op == self.AND:
            l = self.left(resource, row, virtual=False)
            r = self.right(resource, row, virtual=False)
            if l is None:
                return r
            if r is None:
                return l
            return l and r
        elif self.op == self.OR:
            l = self.left(resource, row, virtual=False)
            r = self.right(resource, row, virtual=False)
            if l is None:
                return r
            if r is None:
                return l
            return l or r
        elif self.op == self.NOT:
            l = self.left(resource, row)
            if l is None:
                return None
            else:
                return not l

        real = False
        left = self.left
        if isinstance(left, S3FieldSelector):
            try:
                lfield = left.resolve(resource)
            except (AttributeError, KeyError, SyntaxError):
                return None
            if lfield.field is not None:
                real = True
            elif not lfield.virtual:
                # Unresolvable expression => skip
                return None
        else:
            lfield = left
            if isinstance(left, Field):
                real = True
        right = self.right
        if isinstance(right, S3FieldSelector):
            try:
                rfield = right.resolve(resource)
            except (AttributeError, KeyError, SyntaxError):
                return None
            if rfield.virtual:
                real = False
            elif rfield.field is None:
                # Unresolvable expression => skip
                return None
        else:
            rfield = right
        if virtual and real:
            return None

        extract = lambda f: S3FieldSelector.extract(resource, row, f)
        try:
            l = extract(lfield)
            r = extract(rfield)
        except (KeyError, SyntaxError):
            if current.response.s3.debug:
                from s3utils import s3_debug
                s3_debug(sys.exc_info()[1])
            return None

        if isinstance(left, S3FieldSelector):
            l = left.expr(l)
        if isinstance(right, S3FieldSelector):
            r = right.expr(r)

        op = self.op
        invert = False
        probe = self._probe
        if isinstance(rfield, (list, tuple)) and \
           not isinstance(lfield, (list, tuple)):
            if op == self.EQ:
                op = self.BELONGS
            elif op == self.NE:
                op = self.BELONGS
                invert = True
            elif op != self.BELONGS:
                for v in r:
                    try:
                        r = probe(op, l, v)
                    except (TypeError, ValueError):
                        r = False
                    if r:
                        return True
                return False
        try:
            r = probe(op, l, r)
        except (TypeError, ValueError):
            return False
        if invert and r is not None:
            return not r
        else:
            return r

    # -------------------------------------------------------------------------
    def _probe(self, op, l, r):
        """
            Probe whether the value pair matches the query

            @param l: the left value
            @param r: the right value
        """

        result = False

        contains = self._contains
        convert = S3TypeConverter.convert
        if op == self.CONTAINS:
            r = convert(l, r)
            result = contains(l, r)
        elif op == self.ANYOF:
            if not isinstance(r, (list, tuple)):
                r = [r]
            for v in r:
                if isinstance(l, (list, tuple, basestring)):
                    if contains(l, r):
                        return True
                elif l == r:
                    return True
            return False
        elif op == self.BELONGS:
            if not isinstance(r, (list, tuple)):
                r = [r]
            r = convert(l, r)
            result = contains(r, l)
        elif op == self.LIKE:
            pattern = re.escape(str(r)).replace("\\%", ".*").replace(".*.*", "\\%")
            return re.match(pattern, str(l)) is not None
        else:
            r = convert(l, r)
            if op == self.LT:
                result = l < r
            elif op == self.LE:
                result = l <= r
            elif op == self.EQ:
                result = l == r
            elif op == self.NE:
                result = l != r
            elif op == self.GE:
                result = l >= r
            elif op == self.GT:
                result = l > r
        return result

    # -------------------------------------------------------------------------
    @staticmethod
    def _contains(a, b):
        """
            Probe whether a contains b
        """

        if a is None:
            return False
        try:
            if isinstance(a, basestring):
                return str(b) in a
            elif isinstance(a, (list, tuple)):
                if isinstance(b, (list, tuple)):
                    convert = S3TypeConverter.convert
                    found = True
                    for _b in b:
                        if _b not in a:
                            found = False
                            for _a in a:
                                try:
                                    if convert(_a, _b) == _a:
                                        found = True
                                        break
                                except (TypeError, ValueError):
                                    continue
                        if not found:
                            break
                    return found
                else:
                    return b in a
            else:
                return str(b) in str(a)
        except:
            return False

    # -------------------------------------------------------------------------
    def represent(self, resource):
        """
            Represent this query as a human-readable string.

            @param resource: the resource to resolve the query against
        """

        op = self.op
        l = self.left
        r = self.right
        if op == self.AND:
            l = l.represent(resource)
            r = r.represent(resource)
            return "(%s and %s)" % (l, r)
        elif op == self.OR:
            l = l.represent(resource)
            r = r.represent(resource)
            return "(%s or %s)" % (l, r)
        elif op == self.NOT:
            l = l.represent(resource)
            return "(not %s)" % l
        else:
            if isinstance(l, S3FieldSelector):
                l = l.represent(resource)
            elif isinstance(l, basestring):
                l = '"%s"' % l
            if isinstance(r, S3FieldSelector):
                r = r.represent(resource)
            elif isinstance(r, basestring):
                r = '"%s"' % r
            if op == self.CONTAINS:
                return "(%s in %s)" % (r, l)
            elif op == self.BELONGS:
                return "(%s in %s)" % (l, r)
            elif op == self.ANYOF:
                return "(%s contains any of %s)" % (l, r)
            elif op == self.LIKE:
                return "(%s like %s)" % (l, r)
            elif op == self.LT:
                return "(%s < %s)" % (l, r)
            elif op == self.LE:
                return "(%s <= %s)" % (l, r)
            elif op == self.EQ:
                return "(%s == %s)" % (l, r)
            elif op == self.NE:
                return "(%s != %s)" % (l, r)
            elif op == self.GE:
                return "(%s >= %s)" % (l, r)
            elif op == self.GT:
                return "(%s > %s)" % (l, r)
            else:
                return "(%s ?%s? %s)" % (l, op, r)

    # -------------------------------------------------------------------------
    def serialize_url(self, resource=None):
        """
            Serialize this query as URL query

            @return: a Storage of URL variables
        """

        op = self.op
        l = self.left
        r = self.right

        url_query = Storage()
        def _serialize(n, o, v, invert):
            try:
                quote = lambda s: s if "," not in s else '"%s"' % s
                if isinstance(v, list):
                    v = ",".join([quote(S3TypeConverter.convert(str, val))
                                  for val in v])
                else:
                    v = quote(S3TypeConverter.convert(str, v))
            except:
                return
            if "." not in n:
                if resource is not None:
                    n = "~.%s" % n
                else:
                    return url_query
            if o == self.LIKE:
                v = v.replace("%", "*")
            if o == self.EQ:
                operator = ""
            else:
                operator = "__%s" % o
            if invert:
                operator = "%s!" % operator
            key = "%s%s" % (n, operator)
            if key in url_query:
                url_query[key] = "%s,%s" % (url_query[key], v)
            else:
                url_query[key] = v
            return url_query
        if op == self.AND:
            lu = l.serialize_url(resource=resource)
            url_query.update(lu)
            ru = r.serialize_url(resource=resource)
            url_query.update(ru)
        elif op == self.OR:
            sub = self._or()
            if sub is None:
                # This OR-subtree is not serializable
                return url_query
            n, o, v, invert = sub
            _serialize(n, o, v, invert)
        elif op == self.NOT:
            lu = l.serialize_url(resource=resource)
            for k in lu:
                url_query["%s!" % k] = lu[k]
        elif isinstance(l, S3FieldSelector):
            _serialize(l.name, op, r, False)
        return url_query

    # -------------------------------------------------------------------------
    def _or(self):
        """
            Helper method to URL-serialize an OR-subtree in a query in
            alternative field selector syntax if they all use the same
            operator and value (this is needed to URL-serialize an
            S3SearchSimpleWidget query).
        """

        op = self.op
        l = self.left
        r = self.right

        if self.op == self.AND:
            return None
        elif self.op == self.NOT:
            lname, lop, lval, linv = l._or()
            return (lname, lop, lval, not linv)
        elif self.op == self.OR:
            lvars = l._or()
            rvars = r._or()
            if lvars is None or rvars is None:
                return None
            lname, lop, lval, linv = lvars
            rname, rop, rval, rinv = rvars
            if lop != rop or linv != rinv:
                return None
            if lname == rname:
                return (lname, lop, [lval, rval], linv)
            elif lval == rval:
                return ("%s|%s" % (lname, rname), lop, lval, linv)
            else:
                return None
        else:
            return (self.left.name, self.op, self.right, False)

# =============================================================================
class S3AxisFilter(object):
    """
        Experimental: helper class to extract filter values for pivot
        table axis fields
    """

    # -------------------------------------------------------------------------
    def __init__(self, qdict, tablenames):
        """
            Constructor, recursively introspect the query dict and extract
            all relevant subqueries.

            @param qdict: the query dict (from Query.as_dict(flat=True))
            @param tablenames: the names of the relevant tables
        """

        self.l = None
        self.r = None
        self.op = None

        self.tablename = None
        self.fieldname = None

        if not qdict:
            return

        l = qdict["first"]
        if "second" in qdict:
            r = qdict["second"]
        else:
            r = None

        op = qdict["op"]
        
        if "tablename" in l:
            if l["tablename"] in tablenames:
                self.tablename = l["tablename"]
                self.fieldname = l["fieldname"]
                if isinstance(r, dict):
                    self.op = None
                else:
                    self.op = op
                    self.r = r

        elif op == "AND":
            self.l = S3AxisFilter(l, tablenames)
            self.r = S3AxisFilter(r, tablenames)
            if self.l.op or self.r.op:
                self.op = op

        elif op == "OR":
            self.l = S3AxisFilter(l, tablenames)
            self.r = S3AxisFilter(r, tablenames)
            if self.l.op and self.r.op:
                self.op = op

        elif op == "NOT":
            self.l = S3AxisFilter(l, tablenames)
            self.op = op

        else:
            self.l = S3AxisFilter(l, tablenames)
            if self.l.op:
                self.op = op

    # -------------------------------------------------------------------------
    def query(self):
        """ Reconstruct the query from this filter """

        op = self.op
        if op is None:
            return None

        if self.tablename and self.fieldname:
            l = current.s3db[self.tablename][self.fieldname]
        elif self.l:
            l = self.l.query()
        else:
            l = None

        r = self.r
        if op in ("AND", "OR", "NOT"):
            r = r.query() if r else True

        if op == "AND":
            if l is not None and r is not None:
                return l & r
            elif r is not None:
                return r
            else:
                return l
        elif op == "OR":
            if l is not None and r is not None:
                return l | r
            else:
                return None
        elif op == "NOT":
            if l is not None:
                return ~l
            else:
                return None
        elif l is None:
            return None

        if isinstance(r, S3AxisFilter):
            r = r.query()
        if r is None:
            return None

        if op == "LOWER":
            return l.lower()
        elif op == "UPPER":
            return l.upper()
        elif op == "EQ":
            return l == r
        elif op == "NE":
            return l != r
        elif op == "LT":
            return l < r
        elif op == "LE":
            return l <= r
        elif op == "GE":
            return l >= r
        elif op == "GT":
            return l > r
        elif op == "BELONGS":
            return l.belongs(r)
        elif op == "CONTAINS":
            return l.contains(r)
        else:
            return None

    # -------------------------------------------------------------------------
    def values(self, rfield):
        """
            Helper method to filter list:type axis values

            @param rfield: the axis field

            @return: pair of value lists [include], [exclude]
        """

        op = self.op
        tablename = self.tablename
        fieldname = self.fieldname

        if tablename == rfield.tname and \
           fieldname == rfield.fname:
            value = self.r
            if isinstance(value, (list, tuple)):
                value = [s3_unicode(v) for v in value]
            else:
                value = [s3_unicode(value)]
            if op == "CONTAINS":
                return value, []
            elif op == "EQ":
                return value, []
            elif op == "NE":
                return [], value
        elif op == "AND":
            li, le = self.l.values(rfield)
            ri, re = self.r.values(rfield)
            return [v for v in li + ri if v not in le + re], []
        elif op == "OR":
            li, le = self.l.values(rfield)
            ri, re = self.r.values(rfield)
            return [v for v in li + ri], []
        if op == "NOT":
            li, le = self.l.values(rfield)
            return [], li
        return [], []
        
# =============================================================================
class S3URLQuery(object):
    """ URL Query Parser """

    # -------------------------------------------------------------------------
    @classmethod
    def parse(cls, resource, vars):
        """
            Construct a Storage of S3ResourceQuery from a Storage of get_vars

            @param resource: the S3Resource
            @param vars: the get_vars
            @return: Storage of S3ResourceQuery like {alias: query}, where
                     alias is the alias of the component the query concerns
        """

        query = Storage()

        if resource is None:
            return query
        if not vars:
            return query

        subquery = cls._subquery
        allof = lambda l, r: l if r is None else r if l is None else r & l
            
        for key, value in vars.iteritems():

            if not("." in key or key[0] == "(" and ")" in key):
                continue

            selectors, op, invert = cls.parse_expression(key)

            if type(value) is list:
                # Multiple queries with the same selector (AND)
                q = reduce(allof,
                           [subquery(selectors, op, invert, v) for v in value],
                           None)
            else:
                q = subquery(selectors, op, invert, value)

            if q is None:
                continue

            # Append to query
            if len(selectors) > 1:
                alias = resource.alias
            else:
                alias = selectors[0].split(".", 1)[0]
            if alias == "~":
                alias = resource.alias
            if alias not in query:
                query[alias] = [q]
            else:
                query[alias].append(q)

        return query

    # -------------------------------------------------------------------------
    @staticmethod
    def parse_url(url):
        """
            Parse a URL query into get_vars

            @param query: the URL query string
            @return: the get_vars (Storage)
        """

        if not url:
            return Storage()
        elif "?" in url:
            query = url.split("?", 1)[1]
        elif "=" in url:
            query = url
        else:
            return Storage()

        import cgi
        dget = cgi.parse_qsl(query, keep_blank_values=1)
            
        get_vars = Storage()
        for (key, value) in dget:
            if key in get_vars:
                if type(get_vars[key]) is list:
                    get_vars[key].append(value)
                else:
                    get_vars[key] = [get_vars[key], value]
            else:
                get_vars[key] = value
        return get_vars

    # -------------------------------------------------------------------------
    @staticmethod
    def parse_expression(key):
        """
            Parse a URL expression

            @param key: the key for the URL variable
            @return: tuple (selectors, operator, invert)
        """

        if key[-1] == "!":
            invert = True
        else:
            invert = False
        fs = key.rstrip("!")
        op = None
        if "__" in fs:
            fs, op = fs.split("__", 1)
            op = op.strip("_")
        if not op:
            op = "eq"
        if "|" in fs:
            selectors = [s for s in fs.split("|") if s]
        else:
            selectors = [fs]
        return selectors, op, invert

    # -------------------------------------------------------------------------
    @staticmethod
    def parse_value(value):
        """
            Parse a URL query value

            @param value: the value
            @return: the parsed value
        """

        uquote = lambda w: w.replace('\\"', '\\"\\') \
                            .strip('"') \
                            .replace('\\"\\', '"')
        NONE = ("NONE", "None")
        if type(value) is not list:
            value = [value]
        vlist = []
        for item in value:
            w = ""
            quote = False
            ignore_quote = False
            for c in item:
                if c == '"' and not ignore_quote:
                    w += c
                    quote = not quote
                elif c == "," and not quote:
                    if w in NONE:
                        w = None
                    else:
                        w = uquote(w)
                    vlist.append(w)
                    w = ""
                else:
                    w += c
                if c == "\\":
                    ignore_quote = True
                else:
                    ignore_quote = False
            if w in NONE:
                w = None
            else:
                w = uquote(w)
            vlist.append(w)
        if len(vlist) == 1:
            return vlist[0]
        return vlist
        
    # -------------------------------------------------------------------------
    @classmethod
    def _subquery(cls, selectors, op, invert, value):
        """
            Construct a sub-query from URL selectors, operator and value

            @param selectors: the selector(s)
            @param op: the operator
            @param invert: invert the query
            @param value: the value
        """

        v = cls.parse_value(value)

        q = None
        for fs in selectors:

            if op == S3ResourceQuery.LIKE:
                # Auto-lowercase and replace wildcard
                f = S3FieldSelector(fs).lower()
                if isinstance(v, basestring):
                    v = v.replace("*", "%").lower()
                elif isinstance(v, list):
                    v = [x.replace("*", "%").lower() for x in v if x is not None]
            else:
                f = S3FieldSelector(fs)

            rquery = None
            try:
                rquery = S3ResourceQuery(op, f, v)
            except SyntaxError:
                if current.response.s3.debug:
                    from s3utils import s3_debug
                    s3_debug("Invalid URL query operator: %s (sub-query ignored)" % op)
                q = None
                break

            # Invert operation
            if invert:
                rquery = ~rquery

            # Add to subquery
            if q is None:
                q = rquery
            elif invert:
                q &= rquery
            else:
                q |= rquery
                
        return q

# =============================================================================
class S3ResourceFilter(object):
    """ Class representing a resource filter """

    def __init__(self, resource, id=None, uid=None, filter=None, vars=None):
        """
            Constructor

            @param resource: the S3Resource
            @param id: the record ID (or list of record IDs)
            @param uid: the record UID (or list of record UIDs)
            @param filter: a filter query (Query or S3ResourceQuery)
            @param vars: the dict of GET vars (URL filters)
        """

        self.resource = resource

        # Init
        self.queries = []
        self.filters = []
        self.cqueries = Storage()
        self.cfilters = Storage()
        
        self.query = None
        self.rfltr = None
        self.vfltr = None
        
        self.transformed = None
        
        self.multiple = True
        self.distinct = False

        self.joins = Storage()

        table = resource.table

        # Accessible/available query
        if resource.accessible_query is not None:
            method = []
            if resource._approved:
                method.append("read")
            if resource._unapproved:
                method.append("review")
            mquery = resource.accessible_query(method, table)
        else:
            mquery = (table._id > 0)

        # Deletion status
        DELETED = current.xml.DELETED
        if DELETED in table.fields and not resource.include_deleted:
            remaining = (table[DELETED] != True)
            mquery = remaining & mquery

        # ID query
        if id is not None:
            if not isinstance(id, (list, tuple)):
                self.multiple = False
                mquery = mquery & (table._id == id)
            else:
                mquery = mquery & (table._id.belongs(id))

        # UID query
        UID = current.xml.UID
        if uid is not None and UID in table:
            if not isinstance(uid, (list, tuple)):
                self.multiple = False
                mquery = mquery & (table[UID] == uid)
            else:
                mquery = mquery & (table[UID].belongs(uid))

        parent = resource.parent
        if not parent:
            # Standard master query
            self.mquery = mquery

            # URL queries
            if vars:
                resource.vars = Storage(vars)

                # BBox
                bbox = self.parse_bbox_query(resource, vars)
                if bbox is not None:
                    self.queries.append(bbox)

                # Filters
                add_filter = self.add_filter
                queries = S3URLQuery.parse(resource, vars)
                [add_filter(q) for alias in queries
                               for q in queries[alias]]
                self.cfilters = queries
        else:
            # Parent filter
            pf = parent.rfilter
            if not pf:
                pf = parent.build_query()
                
            # Extended master query
            self.mquery = mquery & pf.get_query() & resource.get_join()

            # Component/link-table specific filters
            add_filter = self.add_filter
            aliases = [resource.alias]
            if resource.link is not None:
                aliases.append(resource.link.alias)
            elif resource.linked is not None:
                aliases.append(resource.linked.alias)
            for alias in aliases:
                for filter_set in (pf.cqueries, pf.cfilters):
                    if alias in filter_set:
                        [add_filter(q) for q in filter_set[alias]]

        # Additional filters
        if filter is not None:
            self.add_filter(filter)

    # -------------------------------------------------------------------------
    def add_filter(self, query, component=None, master=True):
        """
            Extend this filter

            @param query: a Query or S3ResourceQuery object
            @param component: alias of the component the filter shall be
                              added to (None for master)
            @param master: False to filter only component
        """

        alias = None
        if not master:
            if not component:
                return
            if component != self.resource.alias:
                alias = component

        if isinstance(query, S3ResourceQuery):
            self.transformed = None
            filters = self.filters
            cfilters = self.cfilters

            joins, distinct = query.joins(self.resource)
            for tn in joins:
                join = joins[tn]
                if alias not in self.joins:
                    self.joins[alias] = Storage()
                self.joins[alias][tn] = join
                self.add_filter(join, component=component, master=master)
            self.distinct |= distinct

        else:
            # DAL Query
            filters = self.queries
            cfilters = self.cqueries

        self.query = None
        if alias:
            if alias in self.cfilters:
                cfilters[alias].append(query)
            else:
                cfilters[alias] = [query]
        else:
            filters.append(query)
        return

    # -------------------------------------------------------------------------
    def get_query(self):
        """ Get the effective DAL query """

        if self.query is not None:
            return self.query
            
        resource = self.resource
        
        query = reduce(lambda x, y: x & y, self.queries, self.mquery)
        if self.filters:
            if self.transformed is None:

                # Combine all filters
                filters = reduce(lambda x, y: x & y, self.filters)

                # Transform with external search engine
                transformed = filters.transform(resource)
                self.transformed = transformed

                # Split DAL and virtual filters
                self.rfltr, self.vfltr = transformed.split(resource)
                
            if self.rfltr:
                # Add to query
                query &= self.rfltr.query(self.resource)

        # Add cross-component joins if required
        parent = resource.parent
        if parent:
            pf = parent.rfilter
            if pf is None:
                pf = parent.build_query()
            left = pf.get_left_joins(as_list=False)
            tablename = resource._alias
            if left:
                for tn in left:
                    if tn != tablename:
                        for join in left[tn]:
                            query &= join.second
                
        self.query = query
        return query

    # -------------------------------------------------------------------------
    def get_filter(self):
        """ Get the effective virtual filter """

        if self.query is None:
            self.get_query()
        return self.vfltr

    # -------------------------------------------------------------------------
    def get_left_joins(self, as_list=True):
        """
            Get all left joins for this filter

            @param as_list: return a flat list rather than a nested dict
        """

        if self.query is None:
            self.get_query()

        left = Storage()
        resource = self.resource
        for q in self.filters:
            joins, distinct = q.joins(resource, left=True)
            left.update(joins)

        if as_list:
            return [j for tablename in left for j in left[tablename]]
        else:
            return left

    # -------------------------------------------------------------------------
    def get_fields(self):
        """ Get all field selectors in this filter """

        if self.query is None:
            self.get_query()
            
        if self.vfltr:
            return self.vfltr.fields()
        else:
            return []

    # -------------------------------------------------------------------------
    @staticmethod
    def parse_bbox_query(resource, get_vars):
        """
            Generate a Query from a URL boundary box query; supports multiple
            bboxes, but optimised for the usual case of just 1

            @param resource: the resource
            @param get_vars: the URL GET vars
        """

        tablenames = ("gis_location",
                      "gis_feature_query",
                      "gis_layer_shapefile")

        POLYGON = "POLYGON((%s %s, %s %s, %s %s, %s %s, %s %s))"

        bbox_query = None
        if get_vars:
            for k, v in get_vars.items():
                if k[:4] == "bbox":
                    table = resource.table
                    tablename = resource.tablename
                    fields = table.fields

                    fname = None
                    if k.find(".") != -1:
                        fname = k.split(".")[1]
                    elif tablename not in tablenames:
                        for f in fields:
                            if str(table[f].type) == "reference gis_location":
                                fname = f
                                break
                    if fname is not None and fname not in fields:
                        # Field not found - ignore
                        continue
                    try:
                        minLon, minLat, maxLon, maxLat = v.split(",")
                    except:
                        # Badly-formed bbox - ignore
                        continue
                    else:
                        bbox_filter = None
                        if tablename in ("gis_location", "gis_feature_query"):
                            gtable = table
                        elif tablename == "gis_layer_shapefile":
                            gtable = resource.components.items()[0][1].table
                        else:
                            gtable = current.s3db.gis_location
                            if current.deployment_settings.get_gis_spatialdb():
                                # Use the Spatial Database
                                minLon = float(minLon)
                                maxLon = float(maxLon)
                                minLat = float(minLat)
                                maxLat = float(maxLat)
                                bbox = POLYGON % (minLon, minLat,
                                                  minLon, maxLat,
                                                  maxLon, maxLat,
                                                  maxLon, minLat,
                                                  minLon, minLat)
                                try:
                                    # Spatial DAL & Database
                                    bbox_filter = gtable.the_geom \
                                                        .st_intersects(bbox)
                                except:
                                    # Old DAL or non-spatial database
                                    pass
                        if not bbox_filter:
                            bbox_filter = (gtable.lon > float(minLon)) & \
                                          (gtable.lon < float(maxLon)) & \
                                          (gtable.lat > float(minLat)) & \
                                          (gtable.lat < float(maxLat))
                        if fname is not None:
                            # Need a join
                            join = (gtable.id == table[fname])
                            bbox = (join & bbox_filter)
                        else:
                            bbox = bbox_filter
                    if bbox_query is None:
                        bbox_query = bbox
                    else:
                        # Merge with the previous BBOX
                        bbox_query = bbox_query & bbox
        return bbox_query

    # -------------------------------------------------------------------------
    def __call__(self, rows, start=None, limit=None):
        """
            Filter a set of rows by the effective virtual filter

            @param rows: a Rows object
            @param start: index of the first matching record to select
            @param limit: maximum number of records to select
        """

        vfltr = self.get_filter()
        
        if rows is None or vfltr is None:
            return rows
        resource = self.resource
        if start is None:
            start = 0
        first = start
        if limit is not None:
            last = start + limit
            if last < first:
                first, last = last, first
            if first < 0:
                first = 0
            if last < 0:
                last = 0
        else:
            last = None
        i = 0
        result = []
        append = result.append
        for row in rows:
            if last is not None and i >= last:
                break
            success = vfltr(resource, row, virtual=True)
            if success or success is None:
                if i >= first:
                    append(row)
                i += 1
        return Rows(rows.db, result,
                    colnames=rows.colnames, compact=False)

    # -------------------------------------------------------------------------
    def count(self, left=None, distinct=False):
        """
            Get the total number of matching records

            @param left: left outer joins
            @param distinct: count only distinct rows
        """

        distinct |= self.distinct

        resource = self.resource
        if resource is None:
            return 0

        table = resource.table
        tablename = resource.tablename

        vfltr = self.get_filter()

        if vfltr is None and not distinct:

            left_joins = S3LeftJoins(resource.tablename, left)
            left_joins.add(self.get_left_joins())
            left = left_joins.as_list()

            cnt = table[table._id.name].count()

            row = current.db(self.query).select(cnt, left=left).first()
            if row:
                return row[cnt]
            else:
                return 0

        else:
            data = resource.select([table._id.name],
                                   # We don't really want to retrieve
                                   # any rows but just count, hence:
                                   limit=1,
                                   count=True)
            return data["numrows"]

    # -------------------------------------------------------------------------
    def __repr__(self):
        """ String representation of the instance """

        resource = self.resource

        left_joins = self.get_left_joins()
        if left_joins:
            try:
                left_joins = resource.sortleft(left_joins)
            except:
                pass
            left = left_joins
            joins = ", ".join([str(j) for j in left_joins])
        else:
            left = None
            joins = None

        vfltr = self.get_filter()
        if vfltr:
            vfltr = vfltr.represent(resource)
        else:
            vfltr = None

        represent = "<S3ResourceFilter %s, " \
                    "query=%s, " \
                    "left=[%s], " \
                    "distinct=%s, " \
                    "filter=%s>" % (
                        resource.tablename,
                        self.get_query(),
                        joins,
                        self.distinct,
                        vfltr
                    )

        return represent

    # -------------------------------------------------------------------------
    def serialize_url(self):
        """
            Serialize this filter as URL query

            @return: a Storage of URL GET variables
        """
        
        resource = self.resource
        url_vars = Storage()
        for f in self.filters:
            sub = f.serialize_url(resource=resource)
            url_vars.update(sub)
        return url_vars

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
            current.s3db.update_super(table, form.vars)
            current.auth.s3_set_record_owner(table, row[table._id], force_update=True)
            current.manager.onaccept(table, form, method="update")
        return form.vars

    # -------------------------------------------------------------------------
    def delete_record(self, table, id, replaced_by=None):

        s3db = current.s3db

        if replaced_by is not None:
            replaced_by = {str(id): replaced_by}
        resource = s3db.resource(table, id=id)
        ondelete = s3db.get_config(resource.tablename, "ondelete")
        success = resource.delete(ondelete=ondelete,
                                  replaced_by=replaced_by,
                                  cascade=True)
        if not success:
            self.raise_error("Could not delete %s.%s (%s)" %
                            (resource.tablename, id, manager.error))
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
        elif self.main is None:
            fn = key
        return fn

    # -------------------------------------------------------------------------
    def merge(self,
              original_id,
              duplicate_id,
              replace=None,
              update=None,
              main=None):
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
        if main is None:
            s3db.load_all_models()

        # Get the records
        original = None
        duplicate = None
        query = table._id.belongs([original_id, duplicate_id])
        if "deleted" in table.fields:
            query &= table.deleted != True
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
                                        main=resource)
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
        se = s3db.get_config(tablename, "super_entity")
        if se is not None:
            if not isinstance(se, (list, tuple)):
                se = [se]
            for entity in se:
                supertable = s3db[entity]
                # Get the super-keys
                superkey = supertable._id.name
                skey_o = original[superkey]
                skey_d = duplicate[superkey]
                # Merge the super-records
                sresource = define_resource(entity)
                sresource.merge(skey_o, skey_d,
                                replace=replace,
                                update=update,
                                main=resource)

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
