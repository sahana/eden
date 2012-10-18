# -*- coding: utf-8 -*-

""" S3 Data Objects API

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

import re
import sys
import datetime
import time
try:
    from cStringIO import StringIO    # Faster, where available
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
from gluon.dal import Row, Rows, Table
from gluon.languages import lazyT
from gluon.storage import Storage
from gluon.tools import callback

from s3utils import s3_has_foreign_key, s3_get_foreign_key, s3_unicode, S3DataTable
from s3validators import IS_ONE_OF

DEBUG = False
if DEBUG:
    print >> sys.stderr, "S3Resource: DEBUG MODE"
    def _debug(m):
        print >> sys.stderr, m
else:
    _debug = lambda m: None

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

    def __init__(self, table,
                 name=None,
                 id=None,
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
                 unapproved=False):
        """
            Constructor

            @param table: The table, tablename, a resource
                          or the prefix of the table name (=module name)
            @param name: name of the resource (without prefix),
                         required if "table" is a table name prefix

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

            @note: instead of prefix/name it is also possible to specify
                   the tablename, i.e. S3Resource("prefix_name") instead
                   of S3Resource("prefix", "name").

            @note: instead of prefix/name it is also possible to specify
                   a table or a resource as first parameter.
        """

        s3db = current.s3db
        auth = current.auth
        manager = current.manager

        # Names ---------------------------------------------------------------

        self.table = None
        if id is None and \
           (isinstance(name, (int, long, list, tuple)) or \
            isinstance(name, str) and name.isdigit()):
            id, name = name, id
        if name is None:
            if isinstance(table, Table):
                self.table = table
                tablename = table._tablename
            elif isinstance(table, S3Resource):
                self.table = table.table
                tablename = table.tablename
            else:
                tablename = table
            if "_" in tablename:
                prefix, name = tablename.split("_", 1)
            else:
                prefix, name = None, tablename
        else:
            prefix = table
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

        #self.has_permission = lambda m, r=None, c=None, f=None: \
                              #auth.s3_has_permission(m, table, record_id=r, c=c, f=f)
        #self.accessible_query = lambda m, c=None, f=None: \
                                #auth.s3_accessible_query(m, table, c=c, f=f)

        # Audit hook
        self.audit = current.s3_audit

        # Filter --------------------------------------------------------------

        # Default query options
        self.include_deleted = include_deleted
        self._approved = approved
        self._unapproved = unapproved

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

        # Search
        self.search = s3db.get_config(self.tablename, "search_method", None)
        if not self.search:
            if "name" in self.table:
                T = current.T
                self.search = manager.search(
                                name="search_simple",
                                label=T("Name"),
                                comment=T("Enter a name to search for. You may use % as wildcard. Press 'Search' without input to list all items."),
                                field=["name"])
            else:
                self.search = manager.search()

    # -------------------------------------------------------------------------
    def _attach(self, alias, hook):
        """
            Attach a component

            @param alias: the alias
            @param hook: the hook
        """

        # Create as resource
        component = S3Resource(hook.table,
                               parent=self,
                               alias=alias,
                               linktable=hook.linktable,
                               include_deleted=self.include_deleted,
                               approved=self._approved,
                               unapproved=self._unapproved)

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
               fields=None,
               start=0,
               limit=None,
               left=None,
               orderby=None,
               groupby=None,
               distinct=False,
               virtual=True):
        """
            Select records from this resource, applying the current filters.

            @param fields: list of field selectors
            @param start: index of the first record
            @param limit: maximum number of records
            @param left: left joins
            @param orderby: SQL orderby
            @param groupby: SQL groupby (make sure all groupby-fields are selected!)
            @param distinct: SQL distinct
            @param virtual: False to turn off computation of virtual fields
        """

        db = current.db
        table = self.table

        # Get the query and filters
        query = self.get_query()
        vfltr = self.get_filter()
        rfilter = self.rfilter

        # Handle distinct-attribute (must respect rfilter.distinct)
        distinct = self.rfilter.distinct | distinct

        # Fields to select
        if fields is None:
            fields = [f.name for f in self.readable_fields()]
        else:
            fields = list(fields)
        # Add fields needed for filters
        for f in rfilter.get_fields():
            if f not in fields:
                fields.append(f)
        # Resolve all field selectors
        lfields, joins, ljoins, d = self.resolve_selectors(fields,
                                                           skip_components=False)

        distinct = distinct | d
        attributes = {"distinct":distinct}

        # Left joins
        left_joins = left
        if left_joins is None:
            left_joins = []
        elif not isinstance(left, list):
            left_joins = [left_joins]
        joined_tables = [str(join.first) for join in left_joins]

        # Add the left joins from the field query
        ljoins = [j for tablename in ljoins for j in ljoins[tablename]]
        for join in ljoins:
            tn = str(join.first)
            if tn not in joined_tables:
                joined_tables.append(str(join.first))
                left_joins.append(join)

        # Add the left joins from the filter
        fjoins = rfilter.get_left_joins()
        for join in fjoins:
            tn = str(join.first)
            if tn not in joined_tables:
                joined_tables.append(str(join.first))
                left_joins.append(join)

        # Sort left joins and add to attributes
        if left_joins:
            try:
                left_joins.sort(self.sortleft)
            except:
                pass
            attributes["left"] = left_joins

        # Joins
        for join in joins.values():
            if str(join) not in str(query):
                query &= join

        # Orderby
        if orderby is not None:
            attributes["orderby"] = orderby

        # Limitby
        if vfltr is None:
            limitby = self.limitby(start=start, limit=limit)
            if limitby is not None:
                attributes["limitby"] = limitby
        else:
            # Retrieve all records when filtering for virtual fields
            # => apply start/limit in vfltr instead
            limitby = None

        # Column names and headers
        colnames = [f.colname for f in lfields]
        headers = dict(map(lambda f: (f.colname, f.label), lfields))

        # Fields in the query
        load = current.s3db.table
        qfields = []
        qtables = []
        gfields = [str(g) for g in groupby] \
                  if isinstance(groupby, (list, tuple)) else str(groupby)
        for f in lfields:
            field = f.field
            tname = f.tname
            if field is None:
                continue
            qtable = load(tname)
            if qtable is None:
                continue
            if tname not in qtables:
                # Make sure the primary key of the table this field
                # belongs to is included in the SELECT
                qtables.append(tname)
                pkey = qtable._id
                if not groupby:
                    qfields.append(pkey)
                if str(field) == str(pkey):
                    continue
            if not groupby or str(field) in gfields:
                qfields.append(field)

        # Add orderby fields which are not in qfields
        # @todo: this could need some cleanup/optimization
        if distinct:
            if orderby is not None:
                qf = [str(f) for f in qfields]
                if isinstance(orderby, str):
                    of = orderby.split(",")
                elif not isinstance(orderby, (list, tuple)):
                    of = [orderby]
                else:
                    of = orderby
                for e in of:
                    if isinstance(e, Field) and str(e) not in qf:
                        qfields.append(e)
                        qf.append(str(e))
                    elif isinstance(e, str):
                        fn = e.strip().split()[0].split(".", 1)
                        tn, fn = ([table._tablename] + fn)[-2:]
                        try:
                            t = db[tn]
                            f = t[fn]
                        except:
                            continue
                        if str(f) not in qf:
                            qfields.append(f)
                            qf.append(str(e))
            else:
                # default ORDERBY needed with postgresql and DISTINCT,
                # otherwise DAL will add an ORDERBY for any primary keys
                # in the join, which could render DISTINCT meaningless here.
                if str(self._id) not in [str(f) for f in qfields]:
                    qfields.insert(0, self._id)
                attributes["orderby"] = self._id

        if groupby:
            attributes["groupby"] = groupby

        # Temporarily deactivate virtual fields
        osetattr = object.__setattr__
        if not virtual:
            vf = table.virtualfields
            osetattr(table, "virtualfields", [])
        # Retrieve the rows
        rows = db(query).select(*qfields, **attributes)
        # Restore virtual fields
        if not virtual:
            osetattr(table, "virtualfields", vf)

        # Apply virtual fields filter
        if rows and vfltr is not None:
            rows = rfilter(rows, start=start, limit=limit)

        return rows

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
            self.audit("create", self.prefix, self.name, form=record)

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

            @returns: number of records deleted

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
        audit = self.audit
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
            rows = self._load(table._id, table.uuid)
        else:
            rows = self._load(table._id)

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
                                query = linked.table[fkey] == this[rkey]
                                linked = define_resource(linked.table,
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

        auth = current.auth

        if auth.s3_logged_in():
            user_id = approve and auth.user.id or None
        else:
            return False

        tablename = self.tablename
        table = self.table

        for record in self.select():

            record_id = record[table._id]

            # Forget any cached permission for this record
            auth.permission.forget(table, record_id)

            if "approved_by" in table.fields:
                success = record.update_record(approved_by=user_id)
                if not success:
                    current.db.rollback()
                    return False
                else:
                    onapprove = self.get_config("onapprove", None)
                    if onapprove is not None:
                        callback(onapprove, record, tablename=tablename)
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
        audit = self.audit
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
            rows = self._load(table._id, table.uuid)
        else:
            rows = self._load(table._id)
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
                  distinct=False):
        """
            Generate a data table of this resource

            @param fields: list of fields to include (field selector strings)
            @param start: index of the first record to include
            @param limit: maximum number of records to include
            @param left: additional left joins for DB query
            @param orderby: orderby for DB query
            @param distinct: distinct-flag for DB query

            @returns: an S3DataTable instance
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

        # Resolve the selectors
        rfields = self.resolve_selectors(fields,
                                         skip_components=False,
                                         extra_fields=False)[0]

        # Retrieve the rows
        rows = self.select(fields=selectors,
                           start=start,
                           limit=limit,
                           orderby=orderby,
                           left=left,
                           distinct=distinct)

        # Generate the data table
        if rows:
            data = self.extract(rows,
                                selectors,
                                represent=True)
            return S3DataTable(rfields, data)
        else:
            return None

    # -------------------------------------------------------------------------
    def pivottable(self, rows, cols, layers):
        """
            Generate a pivot table of this resource.

            @param rows: field selector for the rows dimension
            @param cols: field selector for the columns dimension
            @param layers: list of tuples (field selector, method) for
                           the aggregation layers

            @returns: an S3Pivottable instance

            Supported methods: see S3Pivottable
        """

        return S3Pivottable(self, rows, cols, layers)

    # -------------------------------------------------------------------------
    def json(self,
             fields=None,
             start=0,
             limit=None,
             left=None,
             distinct=False,
             orderby=None):
        """
            Export a JSON representation of the records, the JSON would be
            a list of dicts with {"tablename.fieldname":"value"}.

            @param fields: list of field selector strings
            @param start: index of the first record
            @param limit: maximum number of records
            @param left: list of (additional) left joins
            @param distinct: select only distinct rows
            @param orderby: Orderby-expression for the query

            @returns: the JSON
        """

        # Choose fields
        if fields is None:
            fields = [f.name for f in self.readable_fields()]
        selectors = list(fields)

        # Retrieve the rows
        rows = self.select(fields=selectors,
                           start=start,
                           limit=limit,
                           orderby=orderby,
                           left=left,
                           distinct=distinct)

        # Generate the JSON
        if rows:
            return json.dumps(self.extract(rows, fields))
        else:
            return "[]"

    # -------------------------------------------------------------------------
    # Deprecated API methods (retained for backward-compatiblity)
    # -------------------------------------------------------------------------
    def _load(self, *fields, **attributes):
        """
            Select records with the current query

            @param fields: fields to select
            @param attributes: select attributes

            @status: deprecated, use select() instead
        """

        attr = Storage(attributes)
        rfilter = self.rfilter

        if rfilter is None:
            rfilter = self.build_query()
        query = rfilter.get_query()
        vfltr = rfilter.get_filter()

        distinct = attr.pop("distinct", False) and True or False
        distinct = rfilter.distinct or distinct
        attr["distinct"] = distinct

        # Add the left joins from the filter
        left_joins = []
        joined_tables = []
        fjoins = rfilter.get_left_joins()
        for join in fjoins:
            tn = str(join.first)
            if tn not in joined_tables:
                joined_tables.append(str(join.first))
                left_joins.append(join)
        if left_joins:
            try:
                left_joins.sort(self.sortleft)
            except:
                pass
            left = left_joins
            attr["left"] = left

        if vfltr is not None:
            if "limitby" in attr:
                limitby = attr["limitby"]
                start = limitby[0]
                limit = limitby[1]
                if limit is not None:
                    limit = limit - start
                del attr["limitby"]
            else:
                start = limit = None
            # @todo: override fields => needed for vfilter

        # Get the rows
        rows = current.db(query).select(*fields, **attr)
        if vfltr is not None:
            rows = rfilter(rows, start=start, limit=limit)

        # Audit
        current.manager.audit("list", self.prefix, self.name)

        # Keep the rows for later access
        self._rows = rows
        return rows

    # -------------------------------------------------------------------------
    # Data Object API
    # -------------------------------------------------------------------------
    def load(self, start=None, limit=None, orderby=None):
        """
            Loads records from the resource, applying the current filters,
            and stores them in the instance.

            @param start: the index of the first record to load
            @param limit: the maximum number of records to load
            @param orderby: orderby-expression for the query

            @returns: the records as list of Rows
        """

        table = self.table

        if self.tablename == "gis_location":
            # Filter out bulky Polygons
            fields = [f for f in table.fields if f not in ("wkt", "the_geom")]
        else:
            fields = [f for f in table.fields]

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
                           orderby=orderby)

        self._ids = []
        self._rows = []

        if rows:
            pkey = table._id.name
            tablename = self.tablename

            for row in rows:
                if tablename in row and isinstance(row[tablename], Row):
                    record = row[tablename]
                else:
                    record = row
                record_id = record[table._id.name]
                if record_id not in self._ids:
                    self._ids.append(record_id)
                    self._rows.append(record)
            uid = current.xml.UID
            if uid in table.fields:
                self._uids = [row[table[uid]] for row in self._rows]
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
            @returns: a Row

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
            @returns: a Row (if component is None) or a list of rows
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
                           limit=limit)

        if rows:
            records = self.extract(rows, fields)
            self._ids = [record[str(table._id)] for record in records]
            if has_uid:
                self._uids = [record[str(table[UID])] for record in records]
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
                   pretty_print=False, **args):
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
            @param pretty_print: insert newlines/indentation in the output
            @param args: dict of arguments to pass to the XSLT stylesheet
        """

        manager = current.manager
        xml = current.xml

        output = None
        args = Storage(args)

        # Export as element tree
        if DEBUG:
            _start = datetime.datetime.now()
            tablename = self.tablename
            _debug("export_tree of %s starting" % tablename)
        tree = self.export_tree(start=start,
                                limit=limit,
                                msince=msince,
                                fields=fields,
                                dereference=dereference,
                                mcomponents=mcomponents,
                                rcomponents=rcomponents,
                                references=references,
                                maxbounds=maxbounds)
        if DEBUG:
            end = datetime.datetime.now()
            duration = end - _start
            duration = '{:.2f}'.format(duration.total_seconds())
            _debug("export_tree of %s completed in %s seconds" % \
                    (tablename, duration))

        # XSLT transformation
        if tree and stylesheet is not None:
            if DEBUG:
                _start = datetime.datetime.now()
            import uuid
            tfmt = xml.ISOFORMAT
            args.update(domain=manager.domain,
                        base_url=manager.s3.base_url,
                        prefix=self.prefix,
                        name=self.name,
                        utcnow=datetime.datetime.utcnow().strftime(tfmt),
                        msguid=uuid.uuid4().urn)
            tree = xml.transform(tree, stylesheet, **args)
            if DEBUG:
                end = datetime.datetime.now()
                duration = end - _start
                duration = '{:.2f}'.format(duration.total_seconds())
                _debug("transform of %s using %s completed in %s seconds" % \
                        (tablename, stylesheet, duration))

        # Convert into the requested format
        # (Content Headers are set by the calling function)
        if tree:
            if as_tree:
                output = tree
            elif as_json:
                if DEBUG:
                    _start = datetime.datetime.now()
                output = xml.tree2json(tree, pretty_print=pretty_print)
                if DEBUG:
                    end = datetime.datetime.now()
                    duration = end - _start
                    duration = '{:.2f}'.format(duration.total_seconds())
                    _debug("tree2json of %s completed in %s seconds" % \
                            (tablename, duration))
            else:
                output = xml.tostring(tree, pretty_print=pretty_print)

        return output

    # -------------------------------------------------------------------------
    def export_tree(self,
                    start=0,
                    limit=None,
                    msince=None,
                    fields=None,
                    skip=[],
                    references=None,
                    dereference=True,
                    mcomponents=None,
                    rcomponents=None,
                    maxbounds=False):
        """
            Export the resource as element tree

            @param start: index of the first record to export
            @param limit: maximum number of records to export
            @param msince: minimum modification date of the records
            @param fields: data fields to include (default: all)
            @param skip: list of fieldnames to skip
            @param references: foreign keys to include (default: all)
            @param dereference: also export referenced records
            @param mcomponents: components of the master resource to
                                include (list of tablenames), empty list
                                for all
            @param rcomponents: components of referenced resources to
                                include (list of tablenames), empty list
                                for all
            @param maxbounds: include lat/lon boundaries in the top
                              level element (off by default)

        """

        define_resource = current.s3db.resource

        manager = current.manager
        xml = current.xml

        if manager.show_urls:
            base_url = manager.s3.base_url
        else:
            base_url = None

        # Split reference/data fields
        (rfields, dfields) = self.split_fields(skip=skip,
                                               data=fields,
                                               references=references)

        # Filter for MCI >= 0 (setting)
        table = self.table
        if xml.filter_mci and "mci" in table.fields:
            mci_filter = (table.mci >= 0)
            self.add_filter(mci_filter)

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

        self.load(start=start, limit=limit, orderby=orderby)

        format = current.auth.permission.format
        request = current.request
        if format == "geojson":
            # Marker will be added in show_map()
            marker = None
            # Lookups per layer not per record
            _vars = request.get_vars
            layer_id = _vars.get("layer", None)
            if layer_id:
                # GIS Feature Layer
                locations = current.gis.get_locations_and_popups(self, layer_id)
            elif self.tablename == "gis_theme_data":
                # GIS Theme Layer
                locations = current.gis.get_theme_geojson(self)
            else:
                # e.g. Search results
                locations = current.gis.get_locations_and_popups(self)
        elif format == "georss" or \
             format == "kml":
            gis = current.gis
            marker = gis.get_marker(request.controller,
                                    request.function)
            locations = gis.get_locations_and_popups(self)
        else:
            marker = current.gis.get_marker(request.controller,
                                            request.function)
            locations = None

        # Build the tree
        if DEBUG:
            _start = datetime.datetime.now()
        root = etree.Element(xml.TAG.root)
        export_map = Storage()
        reference_map = []
        prefix = self.prefix
        name = self.name
        if base_url:
            url = "%s/%s/%s" % (base_url, prefix, name)
        else:
            url = "/%s/%s" % (prefix, name)
        export_resource = self.__export_resource
        for record in self._rows:
            element = export_resource(record,
                                      rfields=rfields,
                                      dfields=dfields,
                                      parent=root,
                                      base_url=url,
                                      reference_map=reference_map,
                                      export_map=export_map,
                                      components=mcomponents,
                                      skip=skip,
                                      msince=msince,
                                      marker=marker,
                                      locations=locations)
            if element is None:
                results -= 1
        if DEBUG:
            end = datetime.datetime.now()
            duration = end - _start
            duration = '{:.2f}'.format(duration.total_seconds())
            _debug("export_resource of primary resource and components completed in %s seconds" % \
                duration)

        # Add referenced resources to the tree
        if DEBUG:
            _start = datetime.datetime.now()
        depth = dereference and manager.MAX_DEPTH or 0
        while reference_map and depth:
            depth -= 1
            load_map = dict()
            get_exported = export_map.get
            for ref in reference_map:
                if "table" in ref and "id" in ref:
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
                prefix, name = tablename.split("_", 1)
                rresource = define_resource(tablename,
                                            id=load_list,
                                            components=[])
                table = rresource.table
                if manager.s3.base_url:
                    url = "%s/%s/%s" % (manager.s3.base_url, prefix, name)
                else:
                    url = "/%s/%s" % (prefix, name)
                rfields, dfields = rresource.split_fields(skip=skip,
                                                          data=fields,
                                                          references=references)
                rresource.load()
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
                                              skip=skip,
                                              master=False,
                                              marker=marker,
                                              locations=locations)

                    # Mark as referenced element (for XSLT)
                    if element is not None:
                        element.set(REF, "True")
        if DEBUG:
            end = datetime.datetime.now()
            duration = end - _start
            duration = '{:.2f}'.format(duration.total_seconds())
            _debug("export_resource of referenced resources and their components completed in %s seconds" % \
                   duration)

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
                          components=None,
                          skip=[],
                          msince=None,
                          master=True,
                          marker=None,
                          locations=None):
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
            @param skip: fields to skip
            @param msince: the minimum update datetime for exported records
            @param master: True of this is the master resource
            @param marker: the marker for GIS encoding
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
        export = self.__export_record
        element, rmap = export(record,
                               rfields=rfields,
                               dfields=dfields,
                               parent=parent,
                               export_map=export_map,
                               url=record_url,
                               msince=msince,
                               master=master,
                               marker=marker,
                               locations=locations)
        if element is not None:
            add = True

        # Export components
        if components is not None:
            for component in self.components.values():

                # Shall this component be included?
                if components and component.tablename not in components:
                    continue

                cpkey = component.table._id

                if component.link is not None:
                    c = component.link
                else:
                    c = component

                # Add MCI filter to component
                ctable = c.table
                if xml.filter_mci and xml.MCI in ctable.fields:
                    mci_filter = (ctable[xml.MCI] >= 0)
                    c.add_filter(mci_filter)

                # Split fields
                _skip = skip+[c.fkey]
                crfields, cdfields = c.split_fields(skip=_skip)

                # Construct the component base URL
                if record_url:
                    component_url = "%s/%s" % (record_url, c.alias)
                else:
                    component_url = None

                # Find related records
                crecords = self.get(record[pkey], component=c.alias)
                if not c.multiple and len(crecords):
                    crecords = [crecords[0]]

                # Export records
                export = c.__export_record
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
                                             url=crecord_url,
                                             msince=msince,
                                             master=False)
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
    def __export_record(self,
                        record,
                        rfields=[],
                        dfields=[],
                        parent=None,
                        export_map=None,
                        url=None,
                        msince=None,
                        master=True,
                        marker=None,
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
            @param marker: the marker for GIS encoding
            @param locations: the locations for GIS encoding
        """

        s3db = current.s3db
        manager = current.manager
        xml = current.xml

        tablename = self.tablename
        table = self.table

        postprocess = s3db.get_config(tablename, "onexport", None)

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
        prefix = self.prefix
        name = self.name
        audit = manager.audit
        if audit:
            audit("read", prefix, name,
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

        # Generate the element
        element = xml.resource(parent, table, record,
                               fields=dfields,
                               alias=alias,
                               postprocess=postprocess,
                               url=url)
        # Add the references
        xml.add_references(element, rmap,
                           show_ids=manager.show_ids)

        # GIS-encode the element
        xml.gis_encode(self, record, element, rmap,
                       marker=marker, locations=locations, master=master)

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
        xml = current.xml
        permit = manager.permit

        tree = None

        self.job = None

        # Check permission for the resource
        authorised = permit("create", self.table) and \
                     permit("update", self.table)
        if not authorised:
            raise IOError("Insufficient permissions")

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

        self.files = Storage()

        # Response message
        if format == "json":
            # Whilst all Responses are JSON, it's easier to debug by having the
            # response appear in the browser than launching a text editor
            current.response.headers["Content-Type"] = "application/json"
        if self.error_tree is not None:
            tree = xml.tree2json(self.error_tree)
        else:
            tree = None

        import_info = {"records":self.import_count}
        created=self.import_created
        if created:
            import_info["created"] = created
        updated=self.import_updated
        if updated:
            import_info["updated"] = updated
        deleted=self.import_deleted
        if deleted:
            import_info["deleted"] = deleted

        if success is True:
            return xml.json_message(message=self.error, tree=tree, **import_info)
        elif success and hasattr(success, "job_id"):
            self.job = success
            return xml.json_message(message=self.error, tree=tree, **import_info)
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

        manager = current.manager
        db = current.db
        xml = current.xml
        permit = manager.auth.s3_has_permission
        audit = manager.audit
        tablename = self.tablename
        table = self.table

        if job_id is not None:

            # Restore a job from the job table
            self.error = None
            self.error_tree = None
            try:
                import_job = S3ImportJob(manager, table,
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
            if manager.import_prep:
                tree = import_job.get_tree()
                callback(manager.import_prep,
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
            if manager.import_prep:
                if not isinstance(tree, etree._ElementTree):
                    tree = etree.ElementTree(tree)
                callback(manager.import_prep,
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
            import_job = S3ImportJob(manager, table,
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
        import_job.commit(ignore_errors=ignore_errors)
        self.error = import_job.error
        self.import_count += import_job.count
        self.import_created += import_job.created
        self.import_updated += import_job.updated
        self.import_deleted += import_job.deleted
        if self.mtime is None or import_job.mtime > self.mtime:
            self.mtime = import_job.mtime
        if self.error:
            if ignore_errors:
                self.error = "%s - invalid items ignored" % self.error
            self.error_tree = import_job.error_tree
        if not commit_job:
            db.rollback()
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
                if not isinstance(req, IS_ONE_OF):
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
                              parent=root,
                              meta=meta,
                              options=options,
                              references=references)

        # Include the selected components
        for component in self.components.values():
            prefix = component.prefix
            name = component.name
            sub = xml.get_struct(prefix, name,
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
    @staticmethod
    def original(table, record):
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

        VALUE = xml.ATTRIBUTE.value
        UID = xml.UID
        ATTRIBUTES_TO_FIELDS = xml.ATTRIBUTES_TO_FIELDS

        # Get primary keys
        pkeys = [f for f in table.fields if table[f].unique]
        pvalues = Storage()

        # Get the values from record
        get = record.get
        if isinstance(record, etree._Element):
            xpath = record.xpath
            xexpr = "%s[@%s='%%s']" % (xml.TAG.data, xml.ATTRIBUTE.field)
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

        # Try to find exactly one match by non-UID unique keys
        if query:
            original = db(query).select(table.ALL, limitby=(0, 2))
            if len(original) == 1:
                return original.first()

        # If no match, then try to find a UID-match
        if UID in pvalues:
            uid = xml.import_uid(pvalues[UID])
            query = (table[UID] == uid)
            original = db(query).select(table.ALL, limitby=(0, 1)).first()
            if original:
                return original

        # No match or multiple matches
        return None

    # -------------------------------------------------------------------------
    def extract(self, rows, fields, represent=False):
        """
            Extract the fields corresponding to fields from the given
            rows and return them as a list of Storages, with ambiguous
            rows collapsed and the original order retained.

            @param rows: the Rows
            @param fields: list of fields

            @returns: list of dicts of {"tablename.fieldname":value}
        """

        pkey = self.table._id

        if not rows:
            return []

        rfields = []
        for i in fields:
            if isinstance(i, tuple) and len(i) > 1:
                f = i[-1]
            else:
                f = i
            if isinstance(f, S3ResourceField):
                rfields.append(f)
            elif isinstance(f, str):
                try:
                    rfield = S3ResourceField(self, f)
                except:
                    continue
                else:
                    rfields.append(rfield)
            elif isinstance(f, S3FieldSelector):
                try:
                    rfield = f.resolve(resource)
                    rfield.op = f.op
                except:
                    continue
                else:
                    rfields.append(rfield)
            else:
                raise SyntaxError("Invalid field: %s" % str(f))

        ids = []
        duplicates = []
        records = []
        for row in rows:
            _id = row[pkey]
            if _id in ids:
                idx = ids.index(_id)
                data = records[idx]
                for rfield in rfields:
                    if rfield.tname != self.tablename and rfield.distinct:
                        key = rfield.colname
                        try:
                            value = rfield.extract(row, represent=represent)
                        except KeyError:
                            if represent:
                                value = ""
                            else:
                                value = None
                        if represent:
                            data[key] = ", ".join([s3_unicode(data[key]),
                                                   s3_unicode(value)])
                        else:
                            if _id in duplicates:
                                data[key].append(value)
                            else:
                                data[key] = [data[key], value]
                duplicates.append(_id)
            else:
                data = Storage()
                for rfield in rfields:
                    try:
                        value = rfield.extract(row, represent=represent)
                    except KeyError:
                        if represent:
                            value = ""
                        else:
                            value = None
                    data[rfield.colname] = value
                ids.append(_id)
                records.append(data)
        return records

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
            return [table[f] for f in subset
                    if f in table.fields and table[f].readable and f != fkey]
        else:
            return [table[f] for f in table.fields
                    if table[f].readable and f != fkey]

    # -------------------------------------------------------------------------
    def resolve_selectors(self, selectors,
                          skip_components=True,
                          extra_fields=True):
        """
            Resolve a list of field selectors against this resource

            @param selectors: the field selectors
            @param skip_components: skip fields in components (component fields
                                    are currently not supported by list_fields)
            @param extra_fields: automatically add extra_fields of all virtual
                                 fields in this table

            @returns: tuple of (fields, joins, left, distinct)
        """

        table = self.table

        prefix = lambda s: "%s.%s" % (self.alias, s) \
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
            for vtable in table.virtualfields:
                if hasattr(vtable, "extra_fields"):
                    for selector in vtable.extra_fields:
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

            selector = prefix(selector)

            # Resolve the selector
            try:
                if isinstance(selector, str):
                    rfield = S3ResourceField(self, selector, label=label)
                elif isinstance(selector, S3FieldSelector):
                    rfield = selector.resolve(self)
                    if label is not None:
                        rfield.label = label
                elif isinstance(selector, S3ResourceField):
                    rfield = selector
                    if label is not None:
                        rfield.label = label
                else:
                    continue
            except (AttributeError, SyntaxError):
                continue

            # Skip components
            if skip_components:
                head = rfield.selector.split("$", 1)[0]
                if "." in head and head.split(".")[0] != self.alias:
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

            rfield.show = rfield.selector in display_fields
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
    def limitby(self, start=None, limit=None):
        """
            Convert start+limit parameters into a limitby tuple
                - limit without start => start = 0
                - start without limit => limit = ROWSPERPAGE
                - limit 0 (or less)   => limit = 1
                - start less than 0   => start = 0

            @param start: index of the first record to select
            @param limit: maximum number of records to select
        """

        if start is None:
            if not limit:
                return None
            else:
                start = 0

        if not limit:
            limit = current.manager.ROWSPERPAGE
            if limit is None:
                return None

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
            return self.linked.get_join()

        elif self.linktable:
            linktable = self.linktable
            lkey = self.lkey
            rkey = self.rkey
            lquery = (ltable[pkey] == linktable[lkey])
            if DELETED in linktable:
                lquery &= (linktable[DELETED] != True)
            join = [linktable.on(lquery),
                    rtable.on(linktable[rkey] == rtable[fkey])]

        else:
            lquery = (ltable[pkey] == rtable[fkey])
            if DELETED in rtable:
                lquery &= (rtable[DELETED] != True)
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

            @returns: tuple of (query, orderby, left joins)
        """

        db = current.db

        left = []

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
        rfields, joins, ljoins, distinct = self.resolve_selectors(fields)

        # FILTER --------------------------------------------------------------

        searchq = None
        if sSearch in vars and iColumns in vars:

            # Build filter
            search_text = vars[sSearch]
            search_like = "%%%s%%" % search_text.lower()

            try:
                numcols = int(vars[iColumns])
            except:
                numcols = 0

            flist = []
            for i in xrange(numcols):
                try:
                    field = rfields[i].field
                except KeyError:
                    continue
                if field is None:
                    continue
                ftype = str(field.type)

                # For foreign keys, we search through their sortby
                if ftype[:9] == "reference" and \
                    hasattr(field, "sortby") and field.sortby:
                    tn = ftype[10:]
                    if parent is not None and \
                       parent.tablename == tn and field.name != fkey:
                        alias = "%s_%s_%s" % (parent.prefix, "linked", parent.name)
                        ktable = db[tn].with_alias(alias)
                        ktable._id = ktable[ktable._id.name]
                        tn = alias
                    else:
                        ktable = db[tn]
                    if tn != skip:
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

                # Otherwise, we search through the field itself
                else:
                    flist.append(field)

            # Build search query
            for field in flist:
                query = None

                ftype = str(field.type)

                # Check whether this type has options
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
                        if hasattr(r, "options"):
                            try:
                                options = r.options()
                            except:
                                continue
                        else:
                            continue

                        vlist = []
                        for (value, text) in options:
                            if str(text).lower().find(search_text.lower()) != -1:
                                vlist.append(value)
                        if vlist:
                            query = field.belongs(vlist)
                    else:
                        continue

                # ...or is string/text
                elif str(field.type) in ("string", "text"):
                    query = field.lower().like(search_like)

                if searchq is None and query:
                    searchq = query
                elif query:
                    searchq = searchq | query

            # Append all joins
            # (is this really necessary => rfields joins would be added anyway?)
            #for j in joins.values():
                #for q in j:
                    #if searchq is None:
                        #searchq = q
                    #elif str(q) not in str(searchq):
                        #searchq &= q

        else:
            searchq = None

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
                    rfield = rfields[int(vars["iSortCol_%s" % i])]
                except:
                    columns.append(None)
                else:
                    columns.append(rfield.field)

            # Process the orderby-fields
            for i in xrange(len(columns)):
                field = columns[i]
                if field is None:
                    continue
                ftype = str(field.type)

                # Foreign keys with sortby will be ordered by sortby
                if ftype[:9] == "reference" and \
                   hasattr(field, "sortby") and field.sortby:

                    # Get the key table
                    tn = ftype[10:]
                    if parent is not None and \
                       parent.tablename == tn and field.name != fkey:
                        alias = "%s_%s_%s" % (parent.prefix, "linked", parent.name)
                        ktable = db[tn].with_alias(alias)
                        ktable._id = ktable[ktable._id.name]
                        tn = alias
                    else:
                        ktable = db[tn]

                    # Add left join (except for linked table)
                    if tn != skip:
                        q = (field == ktable._id)
                        join = [j for j in left if j.first._tablename == tn]
                        if not join:
                            left.append(ktable.on(q))

                    # Construct orderby from sortby
                    if not isinstance(field.sortby, (list, tuple)):
                        orderby.append("%s.%s%s" % (tn, field.sortby, direction(i)))
                    else:
                        orderby.append(", ".join(["%s.%s%s" %
                                                  (tn, fn, direction(i))
                                                  for fn in field.sortby]))

                # otherwise, order by the field itself
                else:
                    orderby.append("%s%s" % (field, direction(i)))

        if orderby:
            orderby = ", ".join(orderby)
        else:
            orderby = None

        return (searchq, orderby, left)

    # -------------------------------------------------------------------------
    @staticmethod
    def sortleft(x, y):
        """ Sort left joins after their dependency """

        tx, qx = str(x.first), str(x.second)
        ty, qy = str(y.first), str(y.second)
        if "%s." % tx in qy:
            return -1
        if "%s." % ty in qx:
            return 1
        return 0

# =============================================================================
class S3FieldSelector:
    """ Helper class to construct a resource query """

    LOWER = "lower"
    UPPER = "upper"

    OPERATORS = [LOWER, UPPER]

    def __init__(self, name, type=None):
        """ Constructor """

        if not isinstance(name, str) or not name:
            raise SyntaxError("name required")
        self.name = name
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
        if not self.op:
            return val
        elif val is not None:
            if self.op == self.LOWER and \
               hasattr(val, "lower") and callable(val.lower):
                return val.lower()
            elif self.op == self.UPPER and \
                 hasattr(val, "upper") and callable(val.upper):
                return val.upper()
        return val

    # -------------------------------------------------------------------------
    def represent(self, resource):

        try:
            lfield = S3ResourceField(resource, self.name)
        except:
            return "#undef#_%s" % self.name
        if self.op is not None:
            return "%s.%s()" % (lfield.colname, self.op)
        return lfield.colname

    # -------------------------------------------------------------------------
    @classmethod
    def extract(cls, resource, row, field):
        """
            Extract a value from a Row

            @param resource: the resource
            @param row: the Row
            @param field: the field

            @returns: field if field is not a Field/S3FieldSelector instance,
                      the value from the row otherwise
        """

        if isinstance(field, Field):
            f = field
            colname = str(field)
        elif isinstance(field, S3FieldSelector):
            rfield = S3ResourceField(resource, field)
            f = rfield.field
            tname = rfield.tname
            fname = rfield.fname
            colname = rfield.colname
        elif isinstance(field, S3ResourceField):
            f = field.field
            tname = field.tname
            fname = field.fname
            if not fname:
                return None
            colname = field.colname
        else:
            return field
        if f is not None and isinstance(row, Row):
            try:
                return row[f]
            except (KeyError, AttributeError):
                raise KeyError("Field not found: %s" % colname)
        elif fname in row:
            value = row[fname]
        elif colname in row:
            value = row[colname]
        elif tname is not None and \
             tname in row and fname in row[tname]:
            value = row[tname][fname]
        else:
            raise KeyError("Field not found: %s" % colname)
        if isinstance(field, S3FieldSelector):
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

        lf = self.resolve(resource, selector)

        self.tname = lf.tname
        self.fname = lf.fname
        self.colname = lf.colname

        self.join = lf.join
        self.left = lf.left
        self.distinct = lf.distinct

        self.field = lf.field

        if self.field is not None:
            self.virtual = False
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
        else:
            self.virtual = True
            self.ftype = "virtual"
            self.represent = s3_unicode
            self.requires = None

        # Fall back to the field label
        if label is None:
            fname = self.fname
            if fname in ["L1", "L2", "L3", "L3", "L4", "L5"]:
                try:
                    label = current.gis.get_location_hierarchy(fname)
                except:
                    label = None
            if label is None:
                f = self.field
                if f:
                    label = f.label
                else:
                    label = " ".join([s.strip().capitalize()
                                      for s in fname.split("_") if s])
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
    @staticmethod
    def resolve(resource, selector, join=None, left=None):
        """ Resolve a field selector against a resource """

        s3db = current.s3db
        manager = current.manager

        distinct = False

        original = selector
        tablename = resource._alias

        if join is None:
            join = Storage()
        if left is None:
            left = Storage()

        if "$" in selector:
            selector, tail = selector.split("$", 1)
            distinct = True
        else:
            tail = None
        if "." in selector:
            tn, fn = selector.split(".", 1)
        else:
            tn = None
            fn = selector

        if tn and tn != resource.alias:
            # Field in a component
            if tn not in resource.components:
                hook = s3db.get_component(resource.tablename, tn)
                if hook:
                    resource._attach(tn, hook)
            if tn in resource.components:
                c = resource.components[tn]
                distinct = c.link is not None or c.multiple
                j = c.get_join()
                l = c.get_left_join()
                tn = c._alias
                join[tn] = j
                left[tn] = l
                table = c.table
            else:
                raise AttributeError("%s is not a component of %s" % (tn, tablename))
        else:
            # Field in the master table
            tn = tablename
            if tail:
                original = "%s$%s" % (fn, tail)
            else:
                original = fn
            table = resource.table

        if table is None:
            raise AttributeError("undefined table %s" % tn)
        else:
            # Resolve the field name
            if fn == "uid":
                fn = current.xml.UID
            if fn == "id":
                f = table._id
            elif fn in table.fields:
                f = table[fn]
            else:
                f = None

        if tail:
            # Field in a referenced table
            ktablename = None
            if not f:
                # Link table reference
                # table <-- pkey -- lkey -- ltable -- rkey -- fkey --> ktable

                # Find the link table name
                LSEP = ":"
                lname = lkey = rkey = fkey = None
                if LSEP in fn:
                    lname, rkey = fn.rsplit(LSEP, 1)
                    if LSEP in lname:
                        lkey, lname = lname.split(LSEP, 1)
                    ltable = s3db.table(lname)
                    if not ltable and lkey is None:
                        (lkey, lname, rkey) = (lname, rkey, lkey)
                else:
                    ltable = None
                    lname = fn

                if ltable is None:
                    ltable = s3db.table(lname,
                                        SyntaxError("%s.%s is not a foreign key" % (tn, fn)),
                                        db_only=True)

                # Get the primary key
                pkey = table._id.name

                # Check the left key
                if lkey is None:
                    search_lkey = True
                else:
                    if lkey not in ltable.fields:
                        raise AttributeError("No field %s in %s" % (lkey, lname))
                    lkey_field = ltable[lkey]
                    _tn, pkey, multiple = s3_get_foreign_key(lkey_field, m2m=False)
                    if _tn and _tn != tn:
                        raise SyntaxError("Invalid link: %s.%s is not a foreign key for %s" % (lname, lkey, tn))
                    elif not _tn:
                        raise SyntaxError("%s.%s is not a foreign key" % (lname, lkey))
                    search_lkey = False

                # Check the right key
                if rkey is None:
                    search_rkey = True
                else:
                    if rkey not in ltable.fields:
                        raise AttributeError("No field %s in %s" % (rkey, lname))
                    rkey_field = ltable[rkey]
                    ktablename, fkey, multiple = s3_get_foreign_key(rkey_field, m2m=False)
                    if not ktablename:
                        raise SyntaxError("%s.%s is not a foreign key" % (lname, lkey))
                    search_rkey = False

                # Key search
                if search_lkey or search_rkey:
                    for fname in ltable.fields:
                        ktn, key, multiple = s3_get_foreign_key(ltable[fname], m2m=False)
                        if not ktn:
                            continue
                        if search_lkey and ktn == tn:
                            if lkey is not None:
                                raise SyntaxError("Ambiguous link: please specify left key in %s" % tn)
                            else:
                                lkey = fname
                                if key:
                                    pkey = key
                        if search_rkey and ktn != tn:
                            if rkey is not None:
                                raise SyntaxError("Ambiguous link: please specify right key in %s" % tn)
                            else:
                                ktablename = ktn
                                rkey = fname
                                fkey = key
                    if lkey is None:
                        raise SyntaxError("Invalid link: no foreign key for %s in %s" % (tn, lname))
                    else:
                        lkey_field = ltable[lkey]
                    if rkey is None:
                        raise SyntaxError("Invalid link: no foreign key found in" % lname)
                    else:
                        rkey_field = ltable[rkey]

                # Load the referenced table
                ktable = s3db.table(ktablename,
                                    AttributeError("Undefined table: %s" % ktablename),
                                    db_only=True)

                # Resolve fkey, if still unknown
                if not fkey:
                    fkey = ktable._id.name

                # Construct the joins
                lq = (table[pkey] == ltable[lkey])
                DELETED = manager.DELETED
                if DELETED in ltable.fields:
                    lq &= ltable[DELETED] != True
                rq = (ltable[rkey] == ktable[fkey])
                distinct = True
                join[ktablename] = lq & rq
                left[ktablename] = [ltable.on(lq), ktable.on(rq)]

            else:
                # Simple forward reference
                # table -- f -- pkey --> ktable

                # Find the referenced table
                ktablename, pkey, multiple = s3_get_foreign_key(f, m2m=False)
                if not ktablename:
                    raise SyntaxError("%s is not a foreign key" % f)

                ktable = s3db.table(ktablename,
                                    AttributeError("Undefined table %s" % ktablename),
                                    db_only=True)
                if pkey is None:
                    pkey = ktable._id
                else:
                    pkey = ktable[pkey]

                # Construct the joins
                j = (f == pkey)
                join[ktablename] = j
                left[ktablename] = [ktable.on(j)]

            # Resolve the tail
            kresource = s3db.resource(ktablename, vars=[])
            field = S3ResourceField.resolve(kresource, tail, join=join, left=left)
            field.update(selector=original,
                         distinct=field.distinct or distinct)
            return field

        else:
            # Done, return the field
            field = Storage(selector=original,
                            tname = tn,
                            fname = fn,
                            colname = "%s.%s" % (tn, fn),
                            field=f,
                            join=join,
                            left=left,
                            distinct=distinct)
            return field

    # -------------------------------------------------------------------------
    def extract(self, row, represent=False):
        """
            Extract the value for this field from a row

            @param row: the Row
        """

        field = self.field
        tname = self.tname
        fname = self.fname
        colname = self.colname

        error = "Field not found in row: %s" % colname

        if field is not None and isinstance(row, Row):
            try:
                value = row[field]
            except KeyError:
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
        if represent:
            if self.represent is not None:
                return self.represent(value)
            else:
                return s3_unicode(value)
        else:
            return value

# =============================================================================
class S3ResourceQuery:
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
            else:
                return l & r
        elif op == self.OR:
            l = l.query(resource)
            r = r.query(resource)
            if l is None or r is None:
                return None
            else:
                return l | r
        elif op == self.NOT:
            l = l.query(resource)
            if l is None:
                return None
            else:
                return ~l

        # Resolve the fields
        if isinstance(l, S3FieldSelector):
            try:
                rfield = S3ResourceField(resource, l.name)
            except:
                return None
            lfield = rfield.field
            if lfield is None:
                return None # virtual field
            lfield = l.expr(lfield)
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
            if rfield is None:
                return None # virtual field
            rfield = r.expr(rfield)
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
            q = l.like(str(r))
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
            if rfield.field is None:
                real = False
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
                    l = [item for item in b if item not in a]
                    if l:
                        return False
                    return True
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

            @returns: a Storage of URL variables
        """

        op = self.op
        l = self.left
        r = self.right

        url_query = Storage()
        def _serialize(n, o, v, invert):
            try:
                if isinstance(v, list):
                    v = ",".join([S3TypeConverter.convert(str, val) for val in v])
                else:
                    v = S3TypeConverter.convert(str, v)
            except:
                return
            if "." not in n:
                if resource is not None:
                    n = "%s.%s" % (resource.alias, n)
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
class S3ResourceFilter:
    """ Class representing a resource filter """

    def __init__(self, resource, id=None, uid=None, filter=None, vars=None):
        """
            Constructor

            @param resource: the S3Resource
            @param id: the record ID (or list of record IDs)
            @param uid: the record UID (or list of record UIDs)
            @param filter: a filter query (Query or S3ResourceQuery)
            @param vars: the dict of URL query parameters
        """

        self.resource = resource

        self.mquery = None      # Master query
        self.mvfltr = None      # Master virtual filter

        self.cquery = Storage() # Component queries
        self.cvfltr = Storage() # Component virtual filters

        self.joins = Storage()  # Joins
        self.left = Storage()   # Left Joins

        self.query = None       # Effective query
        self.vfltr = None       # Effective virtual filter

        # cardinality, multiple results expected by default
        self.multiple = True

        # Distinct: needed if this filter contains multiple-joins
        self.distinct = False

        andq = self._andq
        andf = self._andf

        manager = current.manager

        parent = resource.parent
        name = resource.name
        table = resource.table
        tablename = resource.tablename

        # Master query --------------------------------------------------------
        #
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
        DELETED = manager.DELETED
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

        self.mquery = mquery

        # Component or link table query ---------------------------------------
        if parent:

            pf = parent.rfilter
            alias = resource.alias

            # Use the master virtual filter
            mvfltr = pf.mvfltr

            # Use the master query of the parent plus the component join
            mquery &= pf.get_query()
            mquery = self._andq(mquery, resource.get_join())

            self.mquery = mquery
            self.query = mquery

            # Add the sub-joins for this component
            joins = pf.joins
            if alias in joins:
                subjoins = joins[alias]
                for tn in subjoins:
                    self._add_query(subjoins[tn])

            # Add the left joins of the parent resource
            left = pf.left[parent.alias]
            if left:
                [self._add_query(join.second)
                 for tn in left if tn != resource._alias
                 for join in left[tn]]

            self.mvfltr = mvfltr
            self.vfltr = mvfltr

            cquery = pf.cquery
            cvfltr = pf.cvfltr

            # Add the subqueries and filters for this component
            if alias in cquery:
                [self.add_filter(q) for q in cquery[alias]]
            if alias in cvfltr:
                [self.add_filter(f) for f in cvfltr[alias]]

            if resource.link is not None:
                # If this component has a link table, add the subqueries
                # and filters for the link table
                lname = resource.link.alias
                if lname in cquery:
                    [self.add_filter(q) for q in cquery[lname]]
                if lname in cvfltr:
                    [self.add_filter(f) for f in cvfltr[lname]]

            elif resource.linked is not None:
                # Otherwise, if this is a linktable, add the subqueries
                # and filters for the linked table
                cname = resource.linked.alias
                if cname in cquery:
                    [self.add_filter(q) for q in cquery[cname]]
                if cname in cvfltr:
                    [self.add_filter(f) for f in cvfltr[cname]]

        # Master resource query -----------------------------------------------
        else:
            self.query = self.mquery
            self.vfltr = self.mvfltr

            # URL queries
            if vars:
                resource.vars = Storage(vars)

                # BBox
                bbox = self.parse_bbox_query(resource, vars)
                if bbox is not None:
                    self.mquery &= bbox

                # Filters
                queries = self.parse_url_query(resource, vars)
                [self.add_filter(q)
                    for alias in queries
                        for q in queries[alias]]
                self.cvfltr = queries

        # Add additional filters
        if filter is not None:
            self.add_filter(filter)
        if resource.fquery is not None:
            self._add_query(resource.fquery)
        if resource.fvfltr is not None:
            self._add_vfltr(resource.fvfltr)

        _debug(self)

    # -------------------------------------------------------------------------
    def add_filter(self, f, component=None, master=True):
        """
            Extend this filter

            @param f: a Query or S3ResourceQuery object
            @param component: component this filter concerns
            @param master: filter both master and component
        """

        if isinstance(f, S3ResourceQuery):

            q = f.query(self.resource)
            if q is not None:
                self._add_query(q, component=component, master=master)
            else:
                self._add_vfltr(f, component=component, master=master)

            skip_master = False
            alias = self.resource.alias
            if not master and component and component != alias:
                alias = component
                skip_master = True
            if alias in self.cvfltr:
                # simply append the query -> the risk for and the impact
                # of a possible query duplication is smaller (by orders
                # of magnitude!) than the necessary effort for query
                # de-duplication
                self.cvfltr[alias].append(f)
            else:
                self.cvfltr[alias] = [f]
            if skip_master:
                return

            joins, distinct = f.joins(self.resource)
            for tn in joins:
                join = joins[tn]
                if alias not in self.joins:
                    self.joins[alias] = Storage()
                self.joins[alias][tn] = join
                self._add_query(join, component=component, master=master)
            self.distinct |= distinct

            left, distinct = f.joins(self.resource, left=True)
            for tn in left:
                join = left[tn]
                if alias not in self.left:
                    self.left[alias] = Storage()
                self.left[alias][tn] = join
            self.distinct |= distinct

        else:
            self._add_query(f, component=component, master=master)
        return

    # -------------------------------------------------------------------------
    def _add_query(self, q, component=None, master=True):
        """
            Extend this filter by a DAL filter query

            @param q: the filter query
            @param component: name of the component the filter query
                              applies for, None for the master resource
            @param master: whether to apply the filter query to both
                           component and master
                           (False=filter the component only)
        """

        resource = self.resource
        if component and component in resource.components:
            c = resource.components[component]
            c.fquery = q
        else:
            c = None
        if master:
            if component and c:
                join = c.get_join()
                self.query = self._andq(self.query, join)
            elif component:
                return
            self.query = self._andq(self.query, q)
        return

    # -------------------------------------------------------------------------
    def _add_vfltr(self, f, component=None, master=True):
        """
            Extend this filter by a virtual filter

            @param f: the filter
            @param component: name of the component the filter applies for,
                              None for the master resource
            @param master: whether to apply the filter to both component
                           and master (False=filter the component only)
        """

        resource = self.resource
        if component and component in resource.components:
            c = resource.components[component]
            c.fvfltr = f
        else:
            c = None
        if master:
            alias = resource.alias
            if component and c:
                alias = c.alias
                join = c.get_join()
                self.query = self._andq(self.query, join)
            elif component:
                return
            if self.vfltr is not None:
                self.vfltr &= f
            else:
                self.vfltr = f
        return

    # -------------------------------------------------------------------------
    @staticmethod
    def _andq(query, q):

        try:
            expand = str(q)
        except ValueError:
            # invalid data type in q
            return query
        if query is None:
            query = q
        else:
            if expand not in str(query):
                query &= q
        return query

    # -------------------------------------------------------------------------
    @staticmethod
    def _andf(vfltr, f):

        if vfltr is None:
            vfltr = f
        else:
            vfltr &= f
        return vfltr

    # -------------------------------------------------------------------------
    def get_query(self):
        """ Return the effective query """
        return self.query

    # -------------------------------------------------------------------------
    def get_filter(self):
        """ Return the effective virtual filter """
        return self.vfltr

    # -------------------------------------------------------------------------
    def get_left_joins(self):
        """ Get all left joins for this filter """

        left = self.left
        if left:
            return [j for alias in left
                      for tablename in left[alias]
                      for j in left[alias][tablename]]
        else:
            return []

    # -------------------------------------------------------------------------
    def get_fields(self):
        """ Get all field selectors in this filter """

        if self.vfltr:
            return self.vfltr.fields()
        else:
            return []

    # -------------------------------------------------------------------------
    @staticmethod
    def parse_url_query(resource, vars):
        """
            URL query parser

            @param resource: the resource
            @param vars: the URL query vars (GET vars)
        """

        query = Storage()

        if vars is None:
            return query

        queries = [(k, vars[k]) for k in vars if k.find(".") > 0]
        for k, val in queries:

            # Get operator and field selector
            op = None
            if "__" in k:
                fs, op = k.split("__", 1)
            else:
                fs = k
            if op and op[-1] == "!":
                op = op.rstrip("!")
                invert = True
            else:
                invert = False
            if not op:
                op = "eq"
                if fs[-1] == "!":
                    invert = True
                    fs = fs.rstrip("!")

            # Parse the value
            v = S3ResourceFilter._parse_value(val)

            if "|" in fs:
                selectors = fs.split("|")
            else:
                selectors = [fs]

            q = None
            prefix = None
            for fs in selectors:

                # Check prefix
                if "." in fs:
                    a = fs.split(".", 1)[0]
                    if prefix is None:
                        prefix = a
                elif prefix is not None:
                    fs = "%s.%s" % (prefix, fs)
                else:
                    # Invalid selector
                    q = None
                    break

                # Build a S3ResourceQuery
                rquery = None
                try:
                    if op == S3ResourceQuery.LIKE:
                        # Auto-lowercase and replace wildcard
                        f = S3FieldSelector(fs).lower()
                        if isinstance(v, basestring):
                            v = v.replace("*", "%").lower()
                        elif isinstance(v, list):
                            v = [x.replace("*", "%").lower() for x in v]
                    else:
                        f = S3FieldSelector(fs)
                    rquery = S3ResourceQuery(op, f, v)
                except (SyntaxError, KeyError):
                    q = None
                    break

                # Invert operation
                if invert:
                    rquery = ~rquery

                # Add to subquery
                if q is None:
                    q = rquery
                else:
                    q |= rquery

            if q is None:
                continue

            # Append to query
            if len(selectors) > 1:
                alias = resource.alias
            else:
                alias = selectors[0].split(".", 1)[0]
            if alias not in query:
                query[alias] = [q]
            else:
                query[alias].append(q)

        return query

    # -------------------------------------------------------------------------
    @staticmethod
    def parse_bbox_query(resource, vars):
        """
            Generate a Query from a URL boundary box query

            Supports multiple bboxes, but optimised for the usual case of just 1

            @param resource: the resource
            @param vars: the URL get vars
        """

        bbox_query = None
        if vars:
            for k in vars:
                if k[:4] == "bbox":
                    table = resource.table
                    tablename = resource.tablename
                    fields = table.fields

                    fname = None
                    if k.find(".") != -1:
                        fname = k.split(".")[1]
                    elif tablename not in ("gis_location",
                                           "gis_feature_query"):
                        for f in fields:
                            if str(table[f].type) == "reference gis_location":
                                fname = f
                                break
                    if fname is not None and fname not in fields:
                        # Field not found - ignore
                        continue
                    try:
                        minLon, minLat, maxLon, maxLat = vars[k].split(",")
                    except:
                        # Badly-formed bbox - ignore
                        continue
                    else:
                        bbox_filter = None
                        if tablename == "gis_feature_query" or \
                           tablename == "gis_cache":
                            gtable = table
                        else:
                            gtable = current.s3db.gis_location
                            if current.deployment_settings.get_gis_spatialdb():
                                # Use the Spatial Database
                                minLon = float(minLon)
                                maxLon = float(maxLon)
                                minLat = float(minLat)
                                maxLat = float(maxLat)
                                bbox = "POLYGON((%s %s, %s %s, %s %s, %s %s, %s %s))" % \
                                            (minLon, minLat,
                                             minLon, maxLat,
                                             maxLon, maxLat,
                                             maxLon, minLat,
                                             minLon, minLat)
                                try:
                                    # Spatial DAL & Database
                                    bbox_filter = gtable.the_geom.st_intersects(bbox)
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
    @staticmethod
    def _parse_value(value):
        """
            Parses the value(s) of a URL variable, respects
            quoted values, resolves the NONE keyword

            @param value: the value as either string or list of strings
            @note: does not support quotes within quoted strings
        """

        if type(value) is list:
            value = ",".join(value)
        vlist = []
        w = ""
        quote = False
        for c in value:
            if c == '"':
                w += c
                quote = not quote
            elif c == "," and not quote:
                if w in ("NONE", "None"):
                    w = None
                else:
                    w = w.strip('"')
                vlist.append(w)
                w = ""
            else:
                w += c
        if w in ("NONE", "None"):
            w = None
        else:
            w = w.strip('"')
        vlist.append(w)
        if len(vlist) == 1:
            return vlist[0]
        return vlist

    # -------------------------------------------------------------------------
    def __call__(self, rows, start=None, limit=None):
        """
            Filter a set of rows by the effective virtual filter

            @param rows: a Rows object
            @param start: index of the first matching record to select
            @param limit: maximum number of records to select
        """

        vfltr = self.vfltr
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

        resource = self.resource
        distinct |= self.distinct
        if resource is None:
            return 0
        table = resource.table
        tablename = resource.tablename

        # Left joins
        left_joins = left
        if left_joins is None:
            left_joins = []
        elif not isinstance(left, list):
            left_joins = [left_joins]
        joined_tables = [str(join.first) for join in left_joins]

        # Add the left joins from the filter
        fjoins = self.get_left_joins()
        for join in fjoins:
            tn = str(join.first)
            if tn not in joined_tables:
                joined_tables.append(str(join.first))
                left_joins.append(join)
        if left_joins:
            try:
                left_joins.sort(resource.sortleft)
            except:
                pass
            left = left_joins
        else:
            left = None

        if self.vfltr is None:
            if distinct:
                rows = current.db(self.query).select(table._id,
                                                     left=left,
                                                     distinct=distinct)
                return len(rows)
            else:
                cnt = table[table._id.name].count()
                row = current.db(self.query).select(cnt, left=left).first()
                if row:
                    return(row[cnt])
                else:
                    return 0
        else:
            rows = resource.select([table._id.name],
                                   left=left,
                                   distinct=distinct)
            rows = resource.extract(rows, [table._id.name])

        if rows is None:
            return 0
        return len(rows)

    # -------------------------------------------------------------------------
    def __nonzero__(self):
        """ Boolean test of the instance """

        return self.resource is not None and self.query is not None

    # -------------------------------------------------------------------------
    def __repr__(self):
        """ String representation of the instance """

        resource = self.resource

        left_joins = self.get_left_joins()
        if left_joins:
            try:
                left_joins.sort(resource.sortleft)
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

            @returns: a Storage of URL GET variables
        """
        resource = self.resource

        url_vars = Storage()
        for f in self.cvfltr.values():
            for q in f:
                sub = q.serialize_url(resource=resource)
                url_vars.update(sub)
        return url_vars

# =============================================================================
class S3Pivottable:
    """ Class representing a pivot table of a resource """

    #: Supported aggregation methods
    METHODS = ["list", "count", "min", "max", "sum", "avg"] #, "std"]

    def __init__(self, resource, rows, cols, layers):
        """
            Constructor

            @param resource: the S3Resource
            @param rows: field selector for the rows dimension
            @param cols: field selector for the columns dimension
            @param layers: list of tuples of (field selector, method)
                           for the aggregation layers
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
        s3db = current.s3db
        tablename = resource.tablename
        get_config = s3db.get_config

        # The "report_fields" table setting defines which additional
        # fields shall be included in the report base layer. This is
        # useful to provide easy access to the record data behind a
        # pivot table cell.
        fields = get_config(tablename, "report_fields",
                 get_config(tablename, "list_fields", []))

        # We also want to include all rows/cols options which are
        # defined for this resource
        options = get_config(resource.tablename, "report_options")
        if options is not None:
            fields += options.get("rows", []) + options.get("cols", [])

        self._get_fields(fields=fields)

        # Retrieve the records --------------------------------------------------
        #
        records = resource.select(self.dfields)

        ## Generate the report -------------------------------------------------
        ##
        if records:
            try:
                pkey = resource.table._id
                self.records = Storage([(i[pkey], i) for i in records])
            except KeyError:
                raise KeyError("Could not retrieve primary key values of %s" %
                               resource.tablename)

            # Generate the data frame -----------------------------------------
            #
            from pyvttbl import DataFrame
            df = DataFrame()
            insert = df.insert

            item_list = []
            seen = item_list.append

            flatten = self._flatten
            expand = self._expand

            for row in records:
                item = expand(flatten(row))
                for i in item:
                    if i not in item_list:
                        seen(i)
                        insert(i)

            # Group the records -----------------------------------------------
            #
            tfields = self.tfields
            hpkey = tfields[self.pkey]
            hrows = self.rows and [tfields[self.rows]] or []
            hcols = self.cols and [tfields[self.cols]] or []
            pt = df.pivot(hpkey, hrows, hcols, aggregate="tolist")

            # Initialize columns and rows -------------------------------------
            #
            if cols:
                self.col = [Storage({"value": v != "__NONE__" and v or None})
                            for v in [n[0][1] for n in pt.cnames]]
                self.numcols = len(self.col)
            else:
                self.col = [Storage({"value": None})]
                self.numcols = 1

            if rows:
                self.row = [Storage({"value": v != "__NONE__" and v or None})
                            for v in [n[0][1] for n in pt.rnames]]
                self.numrows = len(self.row)
            else:
                self.row = [Storage({"value": None})]
                self.numrows = 1

            # Add the layers --------------------------------------------------
            #
            add_layer = self._add_layer
            layers = list(self.layers)
            for f, m in self.layers:
                add_layer(pt, f, m)

        else:
            # No items to report on -------------------------------------------
            #
            self.empty = True

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
    # Internal methods
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
            return "%s.%s" % (alias, s) \
                   if "." not in s.split("$", 1)[0] else s

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
        rfields = Storage([(f.selector, f) for f in rfields])
        self.rfields = rfields

        # tfields (transposition-fields): fields to group the records by
        key = lambda s: str(hash(s)).replace("-", "_")
        tfields = {pkey:key(pkey)}
        if rows:
            tfields[rows] = key(rows)
        if cols:
            tfields[cols] = key(cols)
        self.tfields = tfields

        return

    # -------------------------------------------------------------------------
    def _flatten(self, row):
        """
            Prepare a DAL Row for the data frame

            The item must consist of
            the primary key of the table, rows-value, cols-value

            @param row: the row
        """

        item = {}
        rfields = self.rfields
        tfields = self.tfields

        extract = lambda rf: S3FieldSelector.extract(self.resource, row, rf)
        for f in tfields:
            rfield = rfields[f]
            value = extract(rfield)
            if value is None and f != self.pkey:
                value = "__NONE__"
            if type(value) is str:
                value = s3_unicode(value)
            item[tfields[f]] = value
        return item

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
        lfield = rfields[field]
        tname = lfield.tname
        fname = lfield.fname
        if fname in row:
            value = row[fname]
        elif tname in row and fname in row[tname]:
            value = row[tname][fname]
        else:
            value = None
        return value

    # -------------------------------------------------------------------------
    def _expand(self, row, field=None):
        """
            Expand a data frame row into a list of rows for list:type values

            @param row: the row
            @param field: the field to expand (None for all fields)
        """

        if field is None:
            rows = [row]
            for field in row:
                rows = self._expand(rows, field=field)
            return rows
        else:
            results = []
            rows = row
            for r in rows:
                value = r[field]
                if isinstance(value, (list, tuple)):
                    if not len(value):
                        # Always have at least a None-entry
                        value.append(None)
                    for v in value:
                        result = Storage(r)
                        result[field] = v
                        results.append(result)
                else:
                    results.append(r)
            return results

    # -------------------------------------------------------------------------
    def _add_layer(self, pt, fact, method):
        """
            Compute a new layer from the base layer (pt+items)

            @param pt: the pivot table with record IDs
            @param fact: the fact field for the layer
            @param method: the aggregation method of the layer
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

        numcols = len(pt.cnames)
        numrows = len(pt.rnames)

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
                    data = pt[r][c]
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
                    all_values = self.records.keys()
                else:
                    values = []
                    append = values.append
                    for i in ids:
                        value = extract(records[i], fact)
                        if value is None:
                            continue
                        append(value)
                    if len(values) and type(values[0]) is list:
                        values = reduce(lambda x, y: x.extend(y) or x, values)
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
            Compute an aggregation of atomic values

            @param values: the values
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
            return len(values)

        elif method == "min":
            try:
                return min(values)
            except TypeError:
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

# =============================================================================
# Utility classes - move?
# =============================================================================
class S3TypeConverter:
    """ Universal data type converter """

    @classmethod
    def convert(cls, a, b):
        """
            Convert b into the data type of a

            @raise TypeError: if any of the data types are not supported
                              or the types are incompatible
            @raise ValueError: if the value conversion fails
        """

        if isinstance(a, lazyT):
            a = str(a)
        if b is None:
            return None
        if type(a) is type:
            if a in (str, unicode):
                return cls._str(b)
            if a is int:
                return cls._int(b)
            if a is bool:
                return cls._bool(b)
            if a is long:
                return cls._long(b)
            if a is float:
                return cls._float(b)
            if a is datetime.datetime:
                return cls._datetime(b)
            if a is datetime.date:
                return cls._date(b)
            if a is datetime.time:
                return cls._time(b)
            raise TypeError
        if type(b) is type(a) or isinstance(b, type(a)):
            return b
        if isinstance(a, (list, tuple)):
            if isinstance(b, (list, tuple)):
                return b
            elif isinstance(b, basestring):
                if "," in b:
                    b = b.split(",")
                else:
                    b = [b]
            else:
                b = [b]
            if len(a):
                cnv = cls.convert
                return [cnv(a[0], item) for item in b]
            else:
                return b
        if isinstance(b, (list, tuple)):
            cnv = cls.convert
            return [cnv(a, item) for item in b]
        if isinstance(a, basestring):
            return cls._str(b)
        if isinstance(a, bool):
            return cls._bool(b)
        if isinstance(a, int):
            return cls._int(b)
        if isinstance(a, long):
            return cls._long(b)
        if isinstance(a, float):
            return cls._float(b)
        if isinstance(a, datetime.datetime):
            return cls._datetime(b)
        if isinstance(a, datetime.date):
            return cls._date(b)
        if isinstance(a, datetime.time):
            return cls._time(b)
        raise TypeError

    # -------------------------------------------------------------------------
    @staticmethod
    def _bool(b):
        """ Convert into bool """

        if isinstance(b, bool):
            return b
        if isinstance(b, basestring):
            if b.lower() in ("true", "1"):
                return True
            elif b.lower() in ("false", "0"):
                return False
        if isinstance(b, (int, long)):
            if b == 0:
                return False
            else:
                return True
        raise TypeError

    # -------------------------------------------------------------------------
    @staticmethod
    def _str(b):
        """ Convert into string """

        if isinstance(b, basestring):
            return b
        if isinstance(b, datetime.date):
            raise TypeError # @todo: implement
        if isinstance(b, datetime.datetime):
            raise TypeError # @todo: implement
        if isinstance(b, datetime.time):
            raise TypeError # @todo: implement
        return str(b)

    # -------------------------------------------------------------------------
    @staticmethod
    def _int(b):
        """ Convert into int """

        if isinstance(b, int):
            return b
        return int(b)

    # -------------------------------------------------------------------------
    @staticmethod
    def _long(b):
        """ Convert into long """

        if isinstance(b, long):
            return b
        return long(b)

    # -------------------------------------------------------------------------
    @staticmethod
    def _float(b):
        """ Convert into float """

        if isinstance(b, long):
            return b
        return float(b)

    # -------------------------------------------------------------------------
    @staticmethod
    def _datetime(b):
        """ Convert into datetime.datetime """

        if isinstance(b, datetime.datetime):
            return b
        elif isinstance(b, basestring):
            try:
                tfmt = current.xml.ISOFORMAT
                (y, m, d, hh, mm, ss, t0, t1, t2) = time.strptime(b, tfmt)
            except ValueError:
                tfmt = "%Y-%m-%d %H:%M:%S"
                (y, m, d, hh, mm, ss, t0, t1, t2) = time.strptime(b, tfmt)
            return datetime.datetime(y, m, d, hh, mm, ss)
        else:
            raise TypeError

    # -------------------------------------------------------------------------
    @staticmethod
    def _date(b):
        """ Convert into datetime.date """

        if isinstance(b, datetime.date):
            return b
        elif isinstance(b, basestring):
            format = current.deployment_settings.get_L10n_date_format()
            validator = IS_DATE(format=format)
            value, error = validator(v)
            if error:
                raise ValueError
            return value
        else:
            raise TypeError

    # -------------------------------------------------------------------------
    @staticmethod
    def _time(b):
        """ Convert into datetime.time """

        if isinstance(b, datetime.time):
            return b
        elif isinstance(b, basestring):
            validator = IS_TIME()
            value, error = validator(v)
            if error:
                raise ValueError
            return value
        else:
            raise TypeError

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
        success = current.db(table._id==row[table._id]).update(**data)
        if success:
            current.s3db.update_super(table, form.vars)
            current.auth.s3_set_record_owner(table, row[table._id], force_update=True)
            current.manager.onaccept(table, form, method="update")
        else:
            self.raise_error("Could not update %s.%s" %
                            (table._tablename, id))
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
            if alias != self.resource.alias:
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
        manager = current.manager

        resource = self.resource
        table = resource.table
        tablename = resource.tablename

        raise_error = self.raise_error

        # Check for master resource
        if resource.parent:
            raise_error("Must not merge from component", SyntaxError)

        # Check permissions
        auth = current.auth
        has_permission = auth.s3_has_permission
        permitted = has_permission("update", table,
                                   record_id = original_id) and \
                    has_permission("delete", table,
                                   record_id = duplicate_id)
        if not permitted:
            raise_error("Operation not permitted", auth.permission.error)

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
            update_record(table, original_id, original, data)

        # Delete the duplicate
        if not is_super_entity:
            self.merge_realms(table, original, duplicate)
            delete_record(table, duplicate_id, replaced_by=original_id)

        # Success
        return True

# END =========================================================================
