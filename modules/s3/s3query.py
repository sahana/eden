# =============================================================================
class S3QueryBuilder2:
    """ New Resource Query Builder, not in use yet """

    @staticmethod
    def parse_url_query(resource, vars):

        query = None

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

            q = S3ResourceQuery(op, S3QueryField(fn), val)
            if invert:
                q = ~q
            if query is None:
                query = q
            else:
                query = query & q

        f = S3ResourceFilter(resource, query)
        return f

# =============================================================================
class S3QueryField:
    """ Represents a field within a resource query """

    def __init__(self, name):
        if not isinstance(name, str) or not name:
            raise SyntaxError("name required")
        self.name = name

    def __lt__(self, value):
        return S3ResourceQuery(S3ResourceQuery.LT, self, value)

    def __le__(self, value):
        return S3ResourceQuery(S3ResourceQuery.LE, self, value)

    def __eq__(self, value):
        return S3ResourceQuery(S3ResourceQuery.EQ, self, value)

    def __ne__(self, value):
        return S3ResourceQuery(S3ResourceQuery.NE, self, value)

    def __ge__(self, value):
        return S3ResourceQuery(S3ResourceQuery.GE, self, value)

    def __gt__(self, value):
        return S3ResourceQuery(S3ResourceQuery.GT, self, value)

    def like(self, value):
        return S3ResourceQuery(S3ResourceQuery.LIKE, self, value)

    def belongs(self, value):
        return S3ResourceQuery(S3ResourceQuery.BELONGS, self, value)

    def contains(self, value):
        return S3ResourceQuery(S3ResourceQuery.CONTAINS, self, value)

# =============================================================================
class S3ResourceQuery:
    """ Helper class representing a resource query """

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

    def __init__(self, op, first=None, second=None):
        self.op = op
        self.first = first
        self.second = second

    # -------------------------------------------------------------------------
    def __and__(self, other):
        return S3ResourceQuery(self.AND, self, other)

    # -------------------------------------------------------------------------
    def __or__(self, other):
        return S3ResourceQuery(self.OR, self, other)

    # -------------------------------------------------------------------------
    def __invert__(self):
        if self.op == self.NOT:
            return self.first
        else:
            return S3ResourceQuery(self.NOT, self)

    # -------------------------------------------------------------------------
    def __call__(self, resource, row, virtual=True):
        """
            Probe whether the row matches the query

            @param resource: the resource
            @param row: the DB row
            @param virtual: check only virtual fields
        """

        if self.op == self.AND:
            l = self.first(resource, row, virtual=virtual)
            r = self.second(resource, row, virtual=virtual)
            if l is None:
                return r
            if r is None:
                return l
            return l and r

        elif self.op == self.OR:
            l = self.first(resource, row, virtual=virtual)
            r = self.second(resource, row, virtual=virtual)
            if l is None:
                return r
            if r is None:
                return l
            return l or r

        elif self.op == self.NOT:
            l = self.first(resource, row, virtual=virtual)
            if l is None:
                return None
            else:
                return not l
        else:
            name = self.first
            if isinstance(name, S3QueryField):
                name = name.name
            if isinstance(name, str):
                f = self.get_field(resource, name)
                if not f:
                    return None
                if virtual and f.field is not None:
                    return None
                if f.tname in row and f.fname in row[f.tname]:
                    value = row[f.tname][f.fname]
                elif f.fname in row:
                    value = row[f.fname]
                else:
                    # not present
                    return None
            else:
                value = name

        return self.probe(value)

    # -------------------------------------------------------------------------
    def probe(self, value):
        """
            Probe whether the value matches the query

            @param value: the value
        """

        result = False

        def contains(a, b):
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

        if self.op == self.CONTAINS:
            second = S3TypeConverter.convert(value, self.second)
            result = contains(value, second)
        elif self.op == self.BELONGS:
            second = S3TypeConverter.convert(value, self.second)
            result = contains(second, value)
        elif self.op == self.LIKE:
            result = str(self.second) in str(value)
        else:
            try:
                second = S3TypeConverter.convert(value, self.second)
                if self.op == self.LT:
                    result = value < self.second
                elif self.op == self.LE:
                    result = value <= self.second
                elif self.op == self.EQ:
                    result = value == self.second
                elif self.op == self.NE:
                    result = value != self.second
                elif self.op == self.GE:
                    result = value >= self.second
                elif self.op == self.GT:
                    result = value > self.second
            except:
                result = False
        return result

    # -------------------------------------------------------------------------
    def get_field(self, resource, fieldname, join=None):
        """
            {
                fieldname
                field           => Field instance for real fields
                                => function for lazy virtual fields
                                => string for virtual fields
                join            => join (for $-references)
                left            => join (for .-references)
                tname           => tablename for the field
                fname           => fieldname for the field
                colname         => column name in the row
            }
        """

        db = current.db
        manager = current.manager

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
                # Syntax error: not a component
                return None
        else:
            tn = tablename

        manager.load(tn)
        try:
            table = db[tn]
        except:
            # Syntax error: no such table
            return None
        else:
            if fn in table.fields:
                f = table[fn]
            else:
                f = None

        if tail:
            if not f:
                # Syntax error: not a foreign key
                return None

            # Find the referenced table
            ftype = str(f.type)
            if ftype[:9] == "reference":
                ktablename = ftype[10:]
                multiple = False
            elif ftype[:14] == "list:reference":
                ktablename = ftype[15:]
                multiple = True
            else:
                # Syntax error: not a foreign key
                return None

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
            field = self.get_field(resource, tail, join=join)
            if field is None:
                # Syntax error
                return None
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

# =============================================================================
class S3ResourceFilter:

    # -------------------------------------------------------------------------
    def __init__(self, resource, query):

        self.resource = resource
        self.query = query

    # -------------------------------------------------------------------------
    def __call__(self, rows, virtual=True):

        if not self.query:
            return rows
        result = []
        for row in rows:
            test = self.query(self.resource, row, virtual=virtual)
            if test is None or test:
                result.append(row)
        return result

    # -------------------------------------------------------------------------
    def __repr__(self):

        resource = self.resource
        query = self.query

        if query is None:
            return ""
        if query.op == query.AND:
            first = S3ResourceFilter(resource, query.first)
            second = S3ResourceFilter(resource, query.second)
            return "(%s and %s)" % (first, second)
        elif query.op == query.OR:
            first = S3ResourceFilter(resource, query.first)
            second = S3ResourceFilter(resource, query.second)
            return "(%s or %s)" % (first, second)
        elif query.op == query.NOT:
            first = S3ResourceFilter(resource, query.first)
            return "not %s" % first
        else:
            name = query.first
            if isinstance(name, S3QueryField):
                name = name.name
            if isinstance(name, str):
                f = query.get_field(resource, name)
                if f is not None:
                    f = f.colname
                else:
                    f = "<undefined>"
            else:
                f = repr(name)
            if query.op == query.LT:
                return "%s < %s" % (f, repr(query.second))
            elif query.op == query.LE:
                return "%s <= %s" % (f, repr(query.second))
            elif query.op == query.EQ:
                return "%s == %s" % (f, repr(query.second))
            elif query.op == query.NE:
                return "%s != %s" % (f, repr(query.second))
            elif query.op == query.GE:
                return "%s >= %s" % (f, repr(query.second))
            elif query.op == query.GT:
                return "%s > %s" % (f, repr(query.second))
            elif query.op == query.LIKE:
                return "%s.like(%s)" % (f, repr(query.second))
            elif query.op == query.CONTAINS:
                return "%s.contains(%s)" % (f, repr(query.second))
            elif query.op == query.BELONGS:
                return "%s.contains(%s)" % (repr(query.second), f)
            else:
                return "syntax error"

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
                l = []
                for item in b:
                    try:
                        _b = S3TypeConverter.convert(a[0], item)
                    except:
                        continue
                    else:
                        l.append[_b]
                return l
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
        if isinstance(b, int):
            return b
        return int(b)

    # -------------------------------------------------------------------------
    @staticmethod
    def _long(b):
        if isinstance(b, long):
            return b
        return long(b)

    # -------------------------------------------------------------------------
    @staticmethod
    def _float(b):
        if isinstance(b, long):
            return b
        return float(b)

    # -------------------------------------------------------------------------
    @staticmethod
    def _datetime(b):
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
