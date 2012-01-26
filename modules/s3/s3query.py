# -*- coding: utf-8 -*-

"""
    S3 Query Builder Toolkit

    @requires: U{B{I{gluon}} <http://web2py.com>}

    @author: Dominic König <dominic[at]aidiq.com>

    @copyright: 2012 (c) Sahana Software Foundation
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

__all__ = ["S3ResourceFilter"]

from gluon import *
from gluon import current
from gluon.storage import Storage

# =============================================================================

class S3ResourceFilter:
    """ Class representing a resource filter """

    # @todo: add_filter()
    # @todo: add_component_filter()

    def __init__(self, resource, id=None, uid=None, filter=None, vars=None):
        """ @todo: docstring """

        # @todo: retain vars
        # @todo: process "filter" parameter

        self.resource = resource

        self.mquery = None      # Master query
        self.mvfltr = None      # Master virtual filter
        self.cquery = Storage() # Component queries
        self.cvfltr = storage() # Component virtual filters
        self.joins = ()         # Joins
        self.query = None       # Effective query
        self.vfltr = None       # Effective virtual filter

        # cardinality, multiple results expected by default
        self.multiple = True

        manager = current.manager
        model = manager.model
        DELETED = manager.DELETED

        parent = resource.parent
        name = resource.name
        table = resource.table
        tablename = resource.tablename

        # Master query --------------------------------------------------------
        #

        # Accessible/available query
        if resource.accessible_query is not None:
            mquery = resource.accessible_query("read", table)
        else:
            mquery = (table._id > 0)

        # Deletion status
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
        if uid is not None and xml.UID in table:
            if not isinstance(uid, (list, tuple)):
                self.multiple = False
                mquery = mquery & (table[xml.UID] == uid)
            else:
                mquery = mquery & (table[xml.UID].belongs(uid))

        self.mquery = mquery

        # Component or link table query ---------------------------------------
        #
        if parent:
            pf = parent.rfilter
            if pf.mquery:
                # Use the master query of the parent filter plus the component join
                mquery &= pf.mquery
                mquery &= resource.get_join()

                # If the parent filter contains a subquery for this component
                # then add it to the master query
                if resource.alias in pf.cquery:
                    mquery &= pf.cquery[resource.alias]

                # If we have a link table and the parent filter contains a
                # subquery for the link table, then add it to the master query
                if resource.link is not None:
                    lname = resource.link.name
                    if lname in pf.cquery:
                        mquery &= pf.cquery[lname]

                # Otherwise, if this is a link table, and the parent filter
                # contains a subquery for the linked table, then add this to
                # the master query
                elif resource.linked is not None:
                    cname = resource.linked.alias
                    if cname in pf.cquery:
                        mquery &= pf.cquery[cname]

            else:
                # Use the active query of the parent filter plus the component join
                mquery &= pf.query # use the effective query
                join = resource.get_join()
                if str(mquery).find(str(join)) == -1:
                    mquery = mquery & (join)

            # Component filter @todo
            #if resource.filter is not None:
                #mquery = mquery & (resource.filter)

            # Cardinality @todo
            #resource._multiple = resource.multiple
            #resource._query = mquery

            # Set the active query to the master query
            self.mquery = mquery
            self.query = mquery

        # Master resource query -----------------------------------------------
        #
        else:
            # URL queries -----------------------------------------------------
            #
            if vars:
                r, v, j = self.parse_url_query(resource, vars)
                self.cquery = r
                self.cvfltr = v
                self.joins = j

                # @todo: BBOX query
                #bbox = self.parse_bbox_query(resource, vars)
                #if bbox is not None:
                    #self.mquery &= bbox

                # Extend the master query by URL filters for the master resource
                if name in self.cquery:
                    self.mquery &= self.cquery[name]
                    del self.cquery[name]
                # Master virtual filter
                if name in self.cvfltr:
                    self.mvfltr = self.cvfltr[name]
                    del self.cvfltr[name]
                # Remove the join to the master table
                if tablename in self.joins:
                    del self.joins[tablename]

            # Effective query -------------------------------------------------
            #
            # @todo: add some comments here
            #
            joins = []

            self.vfltr = self.mvfltr
            self.query = self.mquery

            auth = current.auth
            aq = auth.s3_accessible_query
            for alias in self.cvfltr:
                vfltr = self.cvfltr[alias]
                if alias != name:
                    component = None
                    if alias in resource.components:
                        component = resource.components[alias]
                    else:
                        continue
                    ctable = component.table
                    ctablename = component.tablename
                    if ctablename not in joins:
                        joins.append(ctablename)
                    accessible = aq("read", ctable)
                    if str(accessible) not in str(self.query):
                        self.query &= accessible
                    if DELETED in ctable.fields:
                        remaining = ctable[DELETED] != True
                        if str(remaining) not in str(self.query):
                            self.query &= remaining
                if self.vfltr is None:
                    self.vfltr = vfltr
                else:
                    self.vfltr &= vfltr

            for alias in self.cquery:
                cquery = self.cquery[alias]
                if alias in resource.components:
                    component = resource.components[alias]
                else:
                    continue
                ctable = component.table
                ctablename = component.tablename
                if ctablename not in joins:
                    joins.append(ctablename)
                accessible = aq("read", ctable)
                if str(accessible) not in str(self.query):
                    self.query &= accessible
                if DELETED in ctable.fields:
                    remaining = ctable[DELETED] != True
                    if str(remaining) not in str(self.query):
                        self.query &= remaining
                self.query &= cquery

            for tn in joins:
                if tn in self.joins:
                    join = self.joins[tn]
                    for q in join:
                        if str(q) not in str(self.query):
                            self.query &= q
                else:
                    continue

        print self

    # -------------------------------------------------------------------------
    def __call__(self, rows):
        """ Filter a set of rows by virtual filters """

        # @todo: implement
        raise NotImplementedError
        
    # -------------------------------------------------------------------------
    def query(self):
        """ Return the effective query """

        # @todo: implement
        raise NotImplementedError

    # -------------------------------------------------------------------------
    def __repr__(self):

        resource = self.resource
        r = self.cquery
        v = self.cvfltr
        j = self.joins

        rq = ["..%s: %s" % (key, r[key]) for key in r]
        vq = ["..%s: %s" % (key, v[key].represent(resource)) for key in v]
        jq = ["..%s: \n....%s" %
              (key, "\n....".join([str(q) for q in j[key]]))
              for key in j]

        rqueries = "\n".join(rq)
        vqueries = "\n".join(vq)
        jqueries = "\n".join(jq)

        if self.vfltr:
            vf = self.vfltr.represent(resource)
        else:
            vf = ""

        if self.mvfltr:
            mvf = self.mvfltr.represent(resource)
        else:
            mvf = ""

        represent = "\nS3ResourceFilter %s" \
                    "\nMaster query: %s" \
                    "\nMaster virtual filter: %s" \
                    "\nComponent queries:\n%s" \
                    "\nComponent virtual filters:\n%s" \
                    "\nJoins:\n%s" \
                    "\nEffective query: %s" \
                    "\nEffective virtual filter: %s" % (
                    resource.tablename,
                    self.mquery,
                    mvf,
                    rqueries,
                    vqueries,
                    jqueries,
                    self.query,
                    vf)

        return represent

    # -------------------------------------------------------------------------
    @staticmethod
    def parse_url_query(resource, vars):
        """
            URL query parser

            @param resource: the resource
            @param vars: the URL query vars (GET vars)
        """

        rquery = Storage()
        vfltr = Storage()
        joins = Storage()

        if vars is None:
            return rquery, vfltr, joins
        queries = [(k, vars[k]) for k in vars if k.find(".") > 0]
        for k, val in queries:
            op = None
            if "__" in k:
                fn, op = k.split("__", 1)
            else:
                fn = k
            if op and op[-1] == "!":
                op = op.rstrip("!")
                invert = True
            else:
                invert = False
            if not op:
                op = "eq"
            if "," in val:
                # @todo: skip this if value is enclosed in quotes
                val = val.split(",")
            # @todo: remove matching outer quotes
            try:
                q = S3ResourceQuery(op, S3QueryField(fn), val)
            except SyntaxError:
                continue
            if invert:
                q = ~q
            alias, f = fn.split(".", 1)
            # Extract the required joins
            joins.update(q.joins(resource))
            # Try to translate into a real query
            r = q.query(resource)
            if r is not None:
                # This translates into a real query
                query = rquery.get(alias, None)
                if query is None:
                    query = r
                else:
                    query = query & r
                rquery[alias] = r
            else:
                # Virtual query
                query = vfltr.get(alias, None)
                if query is None:
                    query = q
                else:
                    query = query & q
                vfltr[alias] = q
        return rquery, vfltr, joins

    # -------------------------------------------------------------------------
    @staticmethod
    def parse_bbox_query(resource, vars):

        s3db = current.s3db
        locations = s3db.gis_location
        table = resource.table
        bbox_query = None

        if vars:
            for k in vars:
                if k[:4] == "bbox":
                    fname = None
                    if k.find(".") != -1:
                        fname = k.split(".")[1]
                    elif resource.tablename != "gis_location":
                        for f in resource.table.fields:
                            if str(table[f].type) == "reference gis_location":
                                fname = f
                                break
                    if fname is None or fname not in resource.table.fields:
                        # Field not found - ignore
                        continue
                    try:
                        minLon, minLat, maxLon, maxLat = vars[k].split(",")
                    except:
                        # Badly-formed bbox - ignore
                        continue
                    else:
                        bbox_filter = ((locations.lon > minLon) & \
                                       (locations.lon < maxLon) & \
                                       (locations.lat > minLat) & \
                                       (locations.lat < maxLat))
                        if fname is not None:
                            # Need a join
                            join = (locations.id == table[fname])
                            bbox = (join & bbox_filter)
                        else:
                            bbox = bbox_filter
                    if bbox_query is None:
                        bbox_query = bbox
                    else:
                        bbox_query = bbox_query & bbox

        return bbox_query

# =============================================================================

class S3QueryField:
    """ Helper class to construct a resource query """

    def __init__(self, name, type=None):
        """ Constructor """

        if not isinstance(name, str) or not name:
            raise SyntaxError("name required")
        self.name = name
        self.type = type

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
    def represent(self, resource):

        try:
            lfield = self.get_field(resource, self.name)
        except:
            return "#undef#_%s" % self.name
        return lfield.colname

    # -------------------------------------------------------------------------
    @classmethod
    def extract(cls, resource, row, field):
        """
            Extract a value from a Row

            @param resource: the resource
            @param row: the Row
            @param field: the field

            @returns: field if field is not a Field/S3QueryField instance,
                      the value from the row otherwise
        """

        if isinstance(field, Field):
            field = field.name
            if "." in field:
                tname, fname = field.split(".", 1)
            else:
                tname = None
                fname = field
        elif isinstance(field, S3QueryField):
            field = field.name
            lf = cls.get_field(resource, field)
            tname = lf.tname
            fname = lf.fname
        elif isinstance(field, dict):
            tname = field.get("tname", None)
            fname = field.get("fname", None)
            if not fname:
                return None
        else:
            return field
        if fname in row:
            value = row[fname]
        elif tname is not None and \
             tname in row and fname in row[tname]:
            value = row[tname][fname]
        else:
            value = None
        return value

    # -------------------------------------------------------------------------
    @classmethod
    def get_field(cls, resource, fieldname, join=None):
        """
            Resolve a fieldname against a resource

            @param resource: the resource
            @param fieldname: the fieldname
            @param join: join query to append to

            @returns: a Storage like:
                {
                    fieldname   => the original name
                    field       => Field instance or None (for virtual fields)
                    join        => join (for $-references)
                    tname       => tablename for the field
                    fname       => fieldname for the field
                    colname     => column name in the row
                }
        """

        db = current.db
        s3db = current.s3db
        manager = current.manager
        xml = manager.xml
        tablename = resource.tablename

        original = fieldname
        if join is None:
            join = []
        if "$" in fieldname:
            fieldname, tail = fieldname.split("$", 1)
        else:
            tail = None
        if "." in fieldname:
            tn, fn = fieldname.split(".", 1)
        else:
            tn = None
            fn = fieldname

        if tn and tn != resource.name:
            # Build component join
            if tn in resource.components:
                j = resource.components[tn].get_join()
                join.append(j)
                tn = resource.components[tn].tablename
            else:
                raise KeyError("%s is not a component of %s" % (tn, tablename))
        else:
            tn = tablename

        # Load the table
        table = s3db[tn]
        if table is None:
            raise KeyError("undefined table %s" % tn)
        else:
            if fn == "uid":
                fn = xml.UID
            if fn in table.fields:
                f = table[fn]
            else:
                f = None

        if tail:
            if not f:
                raise KeyError("no field %s in %s" % (f, tn))

            # Find the referenced table
            ftype = str(f.type)
            if ftype[:9] == "reference":
                ktablename = ftype[10:]
                multiple = False
            elif ftype[:14] == "list:reference":
                ktablename = ftype[15:]
                multiple = True
            else:
                raise SyntaxError("%s.%s is not a foreign key" % (tn, f))

            # Find the primary key
            if "." in ktablename:
                ktablename, pkey = ktablename.split(".", 1)
            else:
                pkey = None
            manager.load(ktablename)
            ktable = db[ktablename]
            if pkey is None:
                pkey = ktable._id
            else:
                pkey = ktable[pkey]

            # Add the join
            j = (f == pkey)
            join.append(j)

            # Define the referenced resource
            prefix, name = ktablename.split("_", 1)
            resource = manager.define_resource(prefix, name)

            # Resolve the tail
            field = cls.get_field(resource, tail, join=join)
            field.update(fieldname=original)
            return field
        else:
            field = Storage(fieldname=fieldname,
                            tname = tn,
                            fname = fn,
                            colname = "%s.%s" % (tn, fn),
                            field=f,
                            join=join)
            return field

    # -------------------------------------------------------------------------
    def resolve(self, resource):
        """
            Resolve this field against a resource

            @param resource: the resource
        """
        return self.get_field(resource, self.name)

# =============================================================================

class S3ResourceQuery:
    """ Helper class representing a resource query """

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

    # -------------------------------------------------------------------------
    def __init__(self, op, left=None, right=None):
        """ Constructor """

        self.op = op
        self.left = left
        self.right = right

        # Resolve the values anyway
        # change __eq into __belongs if list
        # @todo: do this only in urls
        #if op != self.BELONGS and isinstance(right, (list, tuple)):
            #if len(right) > 1:
                #self.op = self.OR
                #self.left = S3ResourceQuery(op, left=left, right=right[0])
                #self.right = S3ResourceQuery(op, left=left, right=right[1:])
            #elif len(right):
                #self.right = self.get_value(right[0])
            #else:
                #self.right = None
        #elif isinstance(right, str):
            #self.right = self.get_value(right)
        #else:
            #self.right = right

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
    def joins(self, resource):
        """
            Get a Storage {tablename: [list of joins]} for this query

            @param resource: the resource to resolve the query against
        """

        op = self.op
        l = self.left
        r = self.right
        if op in (self.AND, self.OR):
            joins = l.joins(resource)
            joins.update(r.joins(resource))
            return joins
        elif op == self.NOT:
            return l.joins(resource)
        if isinstance(l, S3QueryField):
            try:
                lfield = l.resolve(resource)
            except:
                return Storage()
            tname = lfield.tname
            join = lfield.join
        return Storage({tname:join})

    # -------------------------------------------------------------------------
    def query(self, resource):
        """
            Convert this resource query into a DAL query, ignoring virtual
            fields (result does not contain the joins)

            @param resource: the resource to resolve the query against
        """

        op = self.op
        l = self.left
        r = self.right

        # Resolve query components --------------------------------------------
        #
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

        # Resolve the fields --------------------------------------------------
        #
        get_field = lambda f: S3QueryField.get_field(resource, f)
        if isinstance(l, S3QueryField):
            try:
                lf = get_field(l.name)
            except:
                return None
            lfield = lf.field
            if lfield is None:
                return None # virtual field
        elif isinstance(l, Field):
            lfield = l
        else:
            return None # not a field at all
        if isinstance(r, S3QueryField):
            try:
                lf = get_field(r.name)
            except:
                return None
            rfield = lf.field
            if rfield is None:
                return None # virtual field
        else:
            rfield = r

        # Resolve the operator ------------------------------------------------
        #
        if op == self.CONTAINS:
            q = lfield.contains(rfield)
        elif op == self.BELONGS:
            q = lfield.belongs(rfield)
        elif op == self.LIKE:
            q = lfield.like(rfield)
        elif op == self.LT:
            q = lfield < rfield
        elif op == self.LE:
            q = lfield <= rfield
        elif op == self.EQ:
            q = lfield == rfield
        elif op == self.NE:
            q = lfield != rfield
        elif op == self.GE:
            q = lfield >= rfield
        elif op == self.GT:
            q = lfield > rfield
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
            l = self.left(resource, row)
            r = self.right(resource, row)
            if l is None:
                return r
            if r is None:
                return l
            return l and r
        elif self.op == self.OR:
            l = self.left(resource, row)
            r = self.right(resource, row)
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
        if isinstance(left, S3QueryField):
            lfield = left.resolve(resource)
            if lfield.field is not None:
                real = True
        else:
            lfield = left
            if isinstance(left, Field):
                real = True
        right = self.right
        if isinstance(right, S3QueryField):
            rfield = right.resolve(resource)
            if rfield.field is None:
                real = False
        else:
            rfield = right
        if virtual and real:
            return None

        extract = lambda f: S3QueryField.extract(resource, row, f)
        try:
            l = extract(lfield)
            r = extract(rfield)
        except (KeyError, SyntaxError):
            return None
        try:
            return self._probe(l, r)
        except (TypeError, ValueError):
            return False

    # -------------------------------------------------------------------------
    def _probe(self, l, r):
        """
            Probe whether the value pair matches the query

            @param l: the left value
            @param r: the right value
        """

        result = False

        op = self.op
        contains = self._contains
        convert = S3TypeConverter.convert
        if op == self.CONTAINS:
            r = convert(l, r)
            result = contains(l, r)
        elif op == self.BELONGS:
            r = convert(l, r)
            result = contains(r, l)
        elif op == self.LIKE:
            result = str(r) in str(l)
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
                    l = [item for item in b if item in a]
                    return len(l) and True or False
                else:
                    return b in a
            else:
                return str(b) in str(a)
        except:
            return False

    # -------------------------------------------------------------------------
    def get_value(self, name):
        """ @todo: docstring """

        db = current.db
        s3db = current.s3db

        if name[0] == "[" and name[-1] == "]":
            try:
                tn, id, fn = name[1:-1].split("/", 2)
            except:
                return name
            table = s3db.table(tn, None)
            if table is not None:
                query = (table._id == id)
                if fn in table.fields:
                    row = db(query).select(table[fn]).first()
                else:
                    row = db(query).select().first()
                if row and fn in row:
                    return row[fn]
                else:
                    return None
        return name

    # -------------------------------------------------------------------------
    def represent(self, resource):
        """
            Represent this query as a string

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
            if isinstance(l, S3QueryField):
                l = l.represent(resource)
            elif isinstance(l, basestring):
                l = '"%s"' % l
            if isinstance(r, S3QueryField):
                r = r.represent(resource)
            elif isinstance(r, basestring):
                r = '"%s"' % r
            if op == self.CONTAINS:
                return "(%s in %s)" % (r, l)
            elif op == self.BELONGS:
                return "(%s in %s)" % (l, r)
            elif op == self.LIKE:
                return "(%s in %s)" % (r, l)
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
        if isinstance(a, bool):
            return cls._bool(b)
        if isinstance(a, basestring):
            return cls._str(b)
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
            if b.lower() == "true":
                return True
            elif b.lower() == "false":
                return False
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
            manager = current.manager
            xml = manager.xml
            tfmt = xml.ISOFORMAT
            (y,m,d,hh,mm,ss,t0,t1,t2) = time.strptime(v, tfmt)
            return datetime.datetime(y,m,d,hh,mm,ss)
        else:
            raise TypeError

    # -------------------------------------------------------------------------
    @staticmethod
    def _date(b):
        """ Convert into datetime.date """

        if isinstance(b, datetime.date):
            return b
        elif isinstance(b, basestring):
            validator = IS_DATE(format=settings.get_L10n_date_format())
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

# END =========================================================================
