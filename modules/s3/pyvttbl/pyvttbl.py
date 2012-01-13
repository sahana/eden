from __future__ import print_function

# Copyright (c) 2011, Roger Lew [see LICENSE.txt]
# This software is funded in part by NIH Grant P20 RR016454.

# Python 2 to 3 workarounds
import sys
if sys.version_info[0] == 2:
    _strobj = basestring
    _xrange = xrange
elif sys.version_info[0] == 3:
    _strobj = str
    _xrange = range

import collections
import csv
import itertools
import inspect
import math
import sqlite3
import warnings

from pprint import pprint as pp
from copy import copy, deepcopy
from collections import namedtuple
try:
    from collections import Counter,OrderedDict
except ImportError:
    from gluon.contrib.simplejson import OrderedDict
    from counter import Counter

import pystaggrelite3
from dictset import DictSet
from texttable import Texttable as TextTable
from stats import jsci, stats, pstat

# check for third party packages
#try:
    #import pylab
    #HAS_PYLAB = True
#except:
HAS_PYLAB = False

#try:
    #import numpy as np
    #HAS_NUMPY = True
#except:
HAS_NUMPY = False

#try:
    #import scipy
    #HAS_SCIPY = True
#except:
HAS_SCIPY = False

__version__ = '0.3.6.1'

def _isfloat(string):
    """
    returns true if string can be cast as a float,
    returns zero otherwise
    """
    try:
        float(string)
    except:
        return False
    return True

def _isint(string):
    """
    returns true if string can be cast as an int,
    returns zero otherwise
    """
    try:
        f = float(string)
    except:
        return False
    if round(f) - f == 0:
        return True
    return False

def _flatten(x):
    """_flatten(sequence) -> list

    Returns a single, flat list which contains all elements retrieved
    from the sequence and all recursively contained sub-sequences
    (iterables).

    Examples:
    >>> [1, 2, [3,4], (5,6)]
    [1, 2, [3, 4], (5, 6)]
    >>> _flatten([[[1,2,3], (42,None)], [4,5], [6], 7, MyVector(8,9,10)])
    [1, 2, 3, 42, None, 4, 5, 6, 7, 8, 9, 10]"""

    result = []
    for el in x:
        #if isinstance(el, (list, tuple)):
        if hasattr(el, "__iter__") and not isinstance(el, _strobj):
            result.extend(_flatten(el))
        else:
            result.append(el)
    return result

def _xunique_combinations(items, n):
    """
    returns the unique combinations of items. the n parameter controls
    the number of elements in items to combine in each combination
    """
    if n == 0:
        yield []
    else:
        for i in _xrange(len(items)):
            for cc in _xunique_combinations(items[i+1:], n-1):
                yield [items[i]]+cc

def _str(x, dtype='a', n=3):
    """
    makes string formatting more human readable
    """
    try    : f=float(x)
    except : return str(x)

    if math.isnan(f) : return 'nan'
    if math.isinf(f) : return 'inf'

    if   dtype == 'i' : return str(int(round(f)))
    elif dtype == 'f' : return '%.*f'%(n, f)
    elif dtype == 'e' : return '%.*e'%(n, f)
    elif dtype == 't' : return str(x)
    else:
        if f-round(f) == 0:
            if abs(f) > 1e8:
                return '%.*e'%(n, f)
            else:
                return str(int(round(f)))
        else:
            if abs(f) > 1e8 or abs(f) < 1e-8:
                return '%.*e'%(n, f)
            else:
                return '%.*f'%(n, f)

# the dataframe class
class DataFrame(OrderedDict):
    """holds the data in a dummy-coded group format"""
    def __init__(self, *args, **kwds):
        """
        initialize a DataFrame object

          keep in mind that because this class uses sqlite3
          behind the scenes the keys are case-insensitive
        """
        super(DataFrame, self).__init__()

        # Initialize sqlite3
        self.conn = sqlite3.connect(':memory:')
        self.cur = self.conn.cursor()
        self.aggregates = tuple('avg count count group_concat '  \
                                'group_concat max min sum total tolist' \
                                .split())

        # Bind pystaggrelite3 aggregators to sqlite3
        for n, a, f in pystaggrelite3.getaggregators():
            self.bind_aggregate(n, a, f)

        # holds the factors conditions (and all the data values)
        # maybe this should be built on the fly for necessary
        # columns only?
        self.conditions = DictSet([(n, self[n]) for n in self.names()])

        # prints the sqlite3 queries to stdout before
        # executing them for debugging purposes
        self.PRINTQUERIES = False

        # controls whether plot functions return the test dictionaries
        self.TESTMODE = False

        super(DataFrame, self).update(*args, **kwds)

    def bind_aggregate(self, name, arity, func):
        self.conn.create_aggregate(name, arity, func)

        self.aggregates = list(self.aggregates)
        self.aggregates.append(name)
        self.aggregates = tuple(self.aggregates)

    def read_tbl(self, fname, skip=0, delimiter=',',labels=True):
        """
        loads tabulated data from a plain text file

          Checks and renames duplicate column labels as well as checking
          for missing cells. readTbl will warn and skip over missing lines.
        """

        # open and read dummy coded data results file to data dictionary
        fid = open(fname, 'r')
        csv_reader = csv.reader(fid, delimiter=delimiter)
        d = OrderedDict()
        colnames = []

        for i, row in enumerate(csv_reader):
            # skip requested rows
            if i < skip:
                pass

            # read column labels from ith+1 line
            elif i == skip and labels:
                colnameCounter = Counter()
                for k, colname in enumerate(row):
                    colnameCounter[colname] += 1
                    if colnameCounter[colname] > 1:
                        warnings.warn("Duplicate label '%s' found"
                                      %colname,
                                      RuntimeWarning)
                        colname = '%s_%i'%(colname, colnameCounter[colname])
                    colnames.append(colname)
                    d[colname] = []

            # if labels is false we need to make labels
            elif i == skip and not labels:
                colnames = ['COL_%s'%(k+1) for k in range(len(row))]
                for j,colname in enumerate(colnames):
                    if _isfloat(row[j]):
                        d[colname] = [float(row[j])]
                    else:
                        d[colname] = [row[i]]

            # for remaining lines where i>skip...
            else:
                if len(row) != len(colnames):
                    warnings.warn('Skipping line %i of file. '
                                  'Expected %i cells found %i'\
                                  %(i+1, len(colnames), len(row)),
                                  RuntimeWarning)
                else:
                    for j, colname in enumerate(colnames):
                        if _isfloat(row[j]):
                            d[colname].append(float(row[j]))
                        else:
                            d[colname].append(row[j])

        # close data file
        fid.close()
        self.clear()
        for k, v in d.items():
            name_type = (k, self._check_sqlite3_type(v))
            super(DataFrame, self).__setitem__(name_type, v)

        del d
        self.conditions = DictSet([(n,self[n]) for n in self.names()])

    def __contains__(self, key):
        return key in self.names()

    def __setitem__(self, key, item):
        """
        assign a column in the table

          the key should be a string (it will be converted to a string)
          if it is not supplied as one. The key must also not have white
          space and must not be a case variant of an existing key. These
          constraints are to avoid problems when placing data into
          sqlite3.

          The assigned item must be iterable. To add a single row use
          the insert method. To  another table to this one use
          the attach method.
        """
        # check item
        if not hasattr(item, '__iter__'):
            raise TypeError("'%s' object is not iterable"%type(item).__name__)

        # tuple, no where conditions to handle
        if isinstance(key, tuple):
            name, dtype = key
            if name.lower() in map(str.lower, self.names()) and \
               name not in self.names():
                raise Exception("a case variant of '%s' already exists"%name)
            if name in self.names() and dtype != self.typesdict()[name]:
                del self[name]
            super(DataFrame, self).__setitem__((name, dtype), item)
            self.conditions[name] = self[key]
            return

        # string, no where conditions to handle
        split_key = str(key).split()
        name = split_key[0]
        if len(split_key) == 1:
            dtype = self._check_sqlite3_type(item)
            if name.lower() in map(str.lower, self.names()) and \
               name not in self.names():
                raise Exception("a case variant of '%s' already exists"%name)
            if name in self.names():
                del self[name]
            super(DataFrame, self).__setitem__((name, dtype), item)
            self.conditions[name] = self[key]
            return

        # string, with where conditions to handle
        if name not in self.names():
            raise KeyError(name)
        self._get_indices_where(split_key[1:])

        indices = [tup[0] for tup in list(self.cur)]

        if len(indices) != len(item):
            raise Exception('Length of items must length '
                            'of conditions in selection')
        for i,v in zip(indices, item):
            self[name][i] = v
        self.conditions[name] = self[key]

    def __getitem__(self, key):
        """
        returns an item
        """
        if isinstance(key, tuple):
            name_type = key
            return super(DataFrame, self).__getitem__(name_type)

        split_key = str(key).split()
        if len(split_key) == 1:
            name_type = (split_key[0], self.typesdict()[split_key[0]])
            return super(DataFrame, self).__getitem__(name_type)

        if split_key[0] not in self.names():
            raise KeyError(split_key[0])

        self._get_indices_where(split_key[1:])

        return [self[split_key[0]][tup[0]] for tup in self.cur]

    def __delitem__(self, key):
        """
        delete a column from the table
        """
        if isinstance(key, tuple):
            name_type = key
        else:
            key = str(key)
            name_type = (key, self.typesdict()[key])

        del self.conditions[key]
        super(DataFrame, self).__delitem__(name_type)

    def __str__(self):
        """
        returns human friendly string representation of object
        """
        if self == {}:
            return '(table is empty)'

        tt = TextTable(max_width=100000000)
        dtypes = [t[0] for t in self.types()]
        dtypes = list(''.join(dtypes).replace('r', 'f'))
        tt.set_cols_dtype(dtypes)

        aligns = [('l','r')[dt in 'fi'] for dt in dtypes]
        tt.set_cols_align(aligns)

        tt.header(self.names())
        if self.shape()[1] > 0:
            tt.add_rows(zip(*list(self.values())), header=False)
        tt.set_deco(TextTable.HEADER)

        # output the table
        return tt.draw()

    def names(self):
        """
        returns a list of the column labels
        """
        if len(self) == 0:
            return tuple()

        return list(zip(*list(self.keys())))[0]

    def types(self):
        """
        returns a list of the sqlite3 datatypes of the columns
        """
        if len(self) == 0:
            return tuple()

        return list(zip(*list(self.keys())))[1]

    def typesdict(self):
        """
        returns a lookup dictionary of names and datatypes
        """
        return OrderedDict(self.keys())

    def shape(self):
        """
        returns the size of the table as a tuple

          The first element is the number of columns.
          The second element is the number of rows
        """
        if len(self) == 0:
            return (0, 0)

        return (len(self), len(self.values()[0]))

    def _are_col_lengths_equal(self):
        """
        private method to check if the items in self have equal lengths

          returns True if all the items are equal
          returns False otherwise
        """
        # if self is not empty
        counts = map(len, self.values())
        if all(c - counts[0] + 1 == 1 for c in counts):
            return True
        else:
            return False

    def _check_sqlite3_type(self, iterable):
        """
        checks the sqlite3 datatype of iterable

          returns either 'null', 'integer', 'real', or 'text'
        """
        if len(iterable) == 0:
            return 'null'
        elif all(map(_isint, iterable)):
            return 'integer'
        elif all(map(_isfloat, iterable)):
            return 'real'
        else:
            return 'text'

    def _execute(self, query, t=tuple()):
        """
        private method to execute sqlite3 query

          When the PRINTQUERIES bool is true it prints the queries
          before executing them
        """
        if self.PRINTQUERIES:
            print(query)
            if len(t) > 0:
                print('  ', t)
            print()

        self.cur.execute(query, t)

    def _executemany(self, query, tlist):
        """
        private method to execute sqlite3 queries

          When the PRINTQUERIES bool is true it prints the queries
          before executing them. The execute many method is about twice
          as fast for building tables as the execute method.
        """
        if self.PRINTQUERIES:
            print(query)
            print('  ', tlist[0])
            print('   ...\n')

        self.cur.executemany(query, tlist)

    def _get_indices_where(self, where):
        # where should be a split string. No sense splitting it twice

        # preprocess where
        tokens = []
        nsubset2 = set()
        names = self.names()
        for w in where:
            if w in names:
                tokens.append('_%s_'%w)
                nsubset2.add(w)
            else:
                tokens.append(w)
        where = ' '.join(tokens)

        super(DataFrame, self).__setitem__(('INDICES','integer'),
                                         range(self.shape()[1]))

        nsubset2.add('INDICES')

        # build the table
        self.conn.commit()
        self._execute('drop table if exists GTBL')

        self.conn.commit()
        query =  'create temp table GTBL\n  ('
        query += ', '.join('_%s_ %s'%(n, self.typesdict()[n]) for n in nsubset2)
        query += ')'
        self._execute(query)

        # build insert query
        query = 'insert into GTBL values ('
        query += ','.join('?' for n in nsubset2) + ')'
        self._executemany(query, zip(*[self[n] for n in nsubset2]))
        self.conn.commit()

        super(DataFrame, self).__delitem__(('INDICES','integer'))

        # get the indices
        query = 'select _INDICES_ from GTBL %s'%where
        self._execute(query)


    def _build_sqlite3_tbl(self, nsubset, where=None):
        """
        build or rebuild sqlite table with columns in nsubset based on
        the where list

          where can be a list of tuples. Each tuple should have three
          elements. The first should be a column key (label). The second
          should be an operator: in, =, !=, <, >. The third element
          should contain value for the operator.

          where can also be a list of strings. or a single string.
        """
        if where == None:
            where = []

        if isinstance(where, _strobj):
            where = [where]

        #  1. Perform some checkings
        ##############################################################
        if not hasattr(where, '__iter__'):
            raise TypeError( "'%s' object is not iterable"
                             % type(where).__name__)

        nsubset = map(str, nsubset)

        #  2. Figure out which columns need to go into the table
        #     to be able to filter the data
        ##############################################################
        nsubset2 = set(nsubset)
        for item in where:
            if isinstance(item, _strobj):
                nsubset2.update(w for w in item.split() if w in self.names())
            else:
                if str(item[0]) in self.names():
                    nsubset2.add(str(item[0]))

        # orders nsubset2 to match the order in self.names()
        nsubset2 = [n for n in self.names() if n in nsubset2]

        #  3. Build a table
        ##############################################################
        self.conn.commit()
        self._execute('drop table if exists TBL2')

        self.conn.commit()
        query =  'create temp table TBL2\n  ('
        query += ', '.join('_%s_ %s'%(n, self.typesdict()[n]) for n in nsubset2)
        query += ')'
        self._execute(query)

        # build insert query
        query = 'insert into TBL2 values ('
        query += ','.join('?' for n in nsubset2) + ')'
        self._executemany(query, zip(*[self[n] for n in nsubset2]))
        self.conn.commit()

        #  4. If where == None then we are done. Otherwise we need
        #     to build query to filter the rows
        ##############################################################
        if where == []:
            self._execute('drop table if exists TBL')
            self.conn.commit()

            self._execute('alter table TBL2 rename to TBL')
            self.conn.commit()
        else:
            # Initialize another temparary table
            self._execute('drop table if exists TBL')
            self.conn.commit()

            query = []
            for n in nsubset:
                query.append('_%s_ %s'%(n, self.typesdict()[n]))
            query = ', '.join(query)
            query =  'create temp table TBL\n  (' + query + ')'
            self._execute(query)

            # build filter query
            query = []
            for item in where:
                # process item as a string
                if isinstance(item, _strobj):
                    tokens = []
                    for word in item.split():
                        if word in self.names():
                            tokens.append('_%s_'%word)
                        else:
                            tokens.append(word)
                    query.append(' '.join(tokens))

                # process item as a tuple
                else:
                    try:
                        (k,op,value) = item
                    except:
                        raise Exception('could not upack tuple from where')

                    if _isfloat(value):
                        query.append(' _%s_ %s %s'%(k, op, value))
                    elif isinstance(value,list):
                        if _isfloat(value[0]):
                            args = ', '.join(str(v) for v in value)
                        else:
                            args = ', '.join('"%s"'%v for v in value)
                        query.append(' _%s_ %s (%s)'%(k, op, args))
                    else:
                        query.append(' _%s_ %s "%s"'%(k, op, value))

            query = ' and '.join(query)
            nstr = ', '.join('_%s_'%n for n in nsubset)
            query = 'insert into TBL select %s from TBL2\n where '%nstr + query

            # run query
            self._execute(query)
            self.conn.commit()

            # delete TBL2
            self._execute('drop table if exists TBL2')
            self.conn.commit()

    def _get_sqlite3_tbl_info(self):
        """
        private method to get a list of tuples containing information
        relevant to the current sqlite3 table

          Returns a list of tuples. Each tuple cooresponds to a column.
          Tuples include the column name, data type, whether or not the
          column can be NULL, and the default value for the column.
        """
        self.conn.commit()
        self._execute('PRAGMA table_info(TBL)')
        return list(self.cur)

    def pivot(self, val, rows=None, cols=None, aggregate='avg',
              where=None, flatten=False, attach_rlabels=False):
        """
        returns a PyvtTbl object
        """

        if rows == None:
            rows = []

        if cols == None:
            cols = []

        if where == None:
            where = []

        p = PyvtTbl()
        p.run(self, val, rows, cols, aggregate,
                       where, flatten, attach_rlabels)
        return p


    def select_col(self, val, where=None):
        """
        returns the a copy of the selected values based on the
        where parameter
        """
        if where == None:
            where = []

        # 1.
        # check to see if data columns have equal lengths
        if not self._are_col_lengths_equal():
            raise Exception('columns have unequal lengths')

        # 2.
        # check the supplied arguments
        if val not in self.names():
            raise KeyError(val)

        # check to make sure exclude is mappable
        # todo

        # warn if exclude is not a subset of self.conditions
        if not set(self.names()) >= set(tup[0] for tup in where):
            warnings.warn("where is not a subset of table conditions",
                          RuntimeWarning)

        if where == []:
            return copy(self[val])
        else:
            self._build_sqlite3_tbl([val], where)
            self._execute('select * from TBL')
            return [r[0] for r in self.cur]

    def sort(self, order=None):
        """
        sort the table in-place

          order is a list of factors to sort by
          to reverse order append " desc" to the factor
        """
        if order == None:
            order = []

        # Check arguments
        if self == {}:
            raise Exception('Table must have data to sort data')

        # check to see if data columns have equal lengths
        if not self._are_col_lengths_equal():
            raise Exception('columns have unequal lengths')

        if not hasattr(order, '__iter__'):
            raise TypeError( "'%s' object is not iterable"
                             % type(order).__name__)

        # check or build order
        if order == []:
            order = self.names()

        # there are probably faster ways to do this, we definitely need
        # to treat the words as tokens to avoid problems were column
        # names are substrings of other column names
        for i, k in enumerate(order):
            ks = k.split()
            if ks[0] not in self.names():
                raise KeyError(k)

            if len(ks) == 1:
                order[i] = '_%s_'%ks[0]

            elif len(ks) == 2:
                if ks[1].lower() not in ['desc', 'asc']:
                    raise Exception("'order arg must be 'DESC' or 'ASC'")
                order[i] = '_%s_ %s'%(ks[0], ks[1])

            elif len(ks) > 2:
                raise Exception('too many parameters specified')

        # build table
        self._build_sqlite3_tbl(self.names())

        # build and excute query
        query = 'select * from TBL order by ' + ', '.join(order)
        self._execute(query)

        # read sorted order from cursor
        d = []
        for row in self.cur:
            d.append(list(row))

        d = zip(*d) # transpose
        for i, n in enumerate(self.names()):
            self[n] = list(d[i])

    def where(self, where):
        """
        Applies the where filter to a copy of the DataFrame, and
        returns the new DataFrame. The associated DataFrame is not copied.
        """
        new = DataFrame()

        self._build_sqlite3_tbl(self.names(), where)
        self._execute('select * from TBL')
        for n, values in zip(self.names(), zip(*list(self.cur))):
            new[n] = list(values)

        return new

    def where_update(self, where):
        """
        Applies the where filter in-place.
        """
        self._build_sqlite3_tbl(self.names(), where)
        self._execute('select * from TBL')
        for n, values in zip(self.names(), zip(*list(self.cur))):
            del self[n]
            self[n] = list(values)

    def validate(self, criteria, verbose=False, report=False):
        """
        validate the data in the table.

          The criteria argument should be a dict. The keys should
          coorespond to columns in the table. The values should be
          functions which take a single parameter and return a boolean.

          Validation fails if the keys in the criteria dict is not a
          subset of the table keys.
        """
        # do some checking
        if self == {}:
            raise Exception('table must have data to validate data')

        try:
            c = set(criteria.keys())
            s = set(self.names())
        except:
            raise TypeError('criteria must be mappable type')

        # check if the criteria dict has keys that aren't in self
        all_keys_found = bool((c ^ (c & s)) == set())

        # if the user doesn't want a detailed report we don't have
        # to do as much book keeping and can greatly simplify the
        # logic
        if not verbose and not report:
            if all_keys_found:
                return all(all(map(criteria[k], self[k])) for k in criteria)
            else:
                return False

        # loop through specified columns and apply the
        # validation function to each value in the column
        valCounter = Counter()
        reportDict = {}
        for k in (c & s):
            reportDict[k] = []
            if verbose:
                print('\nValidating %s:'%k)

            for i,v in enumerate(self[k]):
                try:
                    func = criteria[k]
                    result = func(v)
                except:
                    result = False
                    valCounter['code_failures'] +=1

                valCounter[result] += 1
                valCounter['n'] += 1

                if result:
                    if verbose:
                        print('.', end='')
                else:
                    reportDict[k].append(
                        "Error: on index %i value "
                        "'%s' failed validation"%(i, str(v)))
                    if verbose:
                        print('X', end='')
            if verbose:
                print()

        # do some book keeping
        pass_or_fail = (valCounter['n'] == valCounter[True]) & all_keys_found

        # print a report if the user has requested one
        if report:
            print('\nReport:')
            for k in (c&s):
                if len(reportDict[k]) > 0:
                    print('While validating %s:'%k)
                for line in reportDict[k]:
                    print('   ',line)

            print(  '  Values tested:', valCounter['n'],
                  '\n  Values passed:', valCounter[True],
                  '\n  Values failed:', valCounter[False])

            if valCounter['code_failures'] != 0:
                print('\n  (%i values failed because '
                      'func(x) did not properly execute)'
                      %valCounter['code_failures'])

            if not all_keys_found:
                print('\n  Error: criteria dict contained '
                      'keys not found in table:'
                      '\n   ', ', '.join(c ^ (c & s)))

            if pass_or_fail:
                print('\n***Validation PASSED***')
            else:
                print('\n***Validation FAILED***')

        # return the test result
        return pass_or_fail

    def attach(self, other):
        """
        attaches a second DataFrame to this DataFrame

          both DataFrames must have the same columns
        """

        # do some checking
        if not isinstance(other, DataFrame):
            raise TypeError('second argument must be a DataFrame')

        if not self._are_col_lengths_equal():
            raise Exception('columns in self have unequal lengths')

        if not other._are_col_lengths_equal():
            raise Exception('columns in other have unequal lengths')

        if not set(self.names()) == set(other.names()):
            raise Exception('self and other must have the same columns')

        if not all(self.typesdict()[n] == other.typesdict()[n]
                                                   for n in self.names()):
            raise Exception('types of self and other must match')

        # perform attachment
        for n in self.names():
            self[n].extend(copy(other[n]))

        # update state variables
        self.conditions = DictSet([(n, self[n]) for n in self.names()])

    def insert(self, row):
        """
        insert a row into the table

          The row should be mappable. e.g. a dict or a list with
          key/value pairs.
        """
        try:
            c = set(dict(row).keys())
            s = set(self.names())
        except:
            raise TypeError('row must be mappable type')

        # the easy case
        if self == {}:
            # if the table is empty try and unpack the table as
            # a row so it preserves the order of the column names
            if isinstance(row, list):
                for (k, v) in row:
                    self[k] = [v]
                    self.conditions[k] = [v]
            else:
                for (k, v) in dict(row).items():
                    self[k] = [v]
                    self.conditions[k] = [v]
        elif c - s == set():
            for (k, v) in dict(row).items():
                self[k].append(v)
                self.conditions[k].add(v)
        else:
            raise Exception('row must have the same keys as the table')

    def write(self, where=None, fname=None, delimiter=','):
        """
        write the contents of the DataFrame to a plaintext file
        """
        if where == None:
            where = []

        if self == {}:
            raise Exception('Table must have data to print data')

        # check to see if data columns have equal lengths
        if not self._are_col_lengths_equal():
            raise Exception('columns have unequal lengths')

        if self.shape()[1] < 1:
            raise Exception('Table must have at least one row to print data')

        # check or build fname
        if fname != None:
            if not isinstance(fname, _strobj):
                raise TypeError('fname must be a string')
        else:
            lnames = [str(n).lower().replace('1','') for n in self.names()]
            fname = 'X'.join(lnames)

            if delimiter == ',':
                fname += '.csv'
            elif delimiter == '\t':
                fname += '.tsv'
            else:
                fname += '.txt'

        with open(fname,'wb') as fid:
            wtr = csv.writer(fid, delimiter=delimiter)
            wtr.writerow(self.names())

            if where == []:
                wtr.writerows(zip(*list(self[n] for n in self.names())))
            else:
                self._build_sqlite3_tbl(self.names(), where)
                self._execute('select * from TBL')
                wtr.writerows(list(self.cur))

    def descriptives(self, cname, where=None):
        """
        returns a dict of descriptive statistics for column cname
        """

        if where == None:
            where = []

        if self == {}:
            raise Exception('Table must have data to calculate descriptives')

        # check to see if data columns have equal lengths
        if not self._are_col_lengths_equal():
            raise Exception('columns have unequal lengths')

        if cname not in self.names():
            raise KeyError(cname)

        V = self.select_col(cname, where=where)
        d = Descriptives()
        d.run(V, cname)
        return d

    def summary(self, where=None):
        """
        prints a the (cname) for each column in the DataFrame
        """
        for (cname,dtype) in self.keys():
            if dtype in ['real', 'integer']:
                print(self.descriptives(cname, where))
                print()

            else:
                print('%s contains non-numerical data\n'%cname)

    def marginals(self, val, factors, where=None):
        """
        returns a marginals object containg means, counts,
        standard errors, and confidence intervals for the
        marginal conditions of the factorial combinations
        sepcified in the factors list.
        """
        if where == None:
            where = []

        if self == {}:
            raise Exception('Table must have data to find marginals')

        # check to see if data columns have equal lengths
        if not self._are_col_lengths_equal():
            raise Exception('columns have unequal lengths')

        m = Marginals()
        m.run(self, val, factors, where)
        return m

    def anova1way(self, val, factor, posthoc='tukey', where=None):
        """
        returns an ANOVA1way object containing the results of a
        one-way analysis of variance on val over the conditions
        in factor. The conditions do not necessarily need to have
        equal numbers of samples.
        """
        if where == None:
            where = []

        if self == {}:
            raise Exception('Table must have data to find marginals')

        # check to see if data columns have equal lengths
        if not self._are_col_lengths_equal():
            raise Exception('columns have unequal lengths')

        # build list of lists for ANOVA1way object
        list_of_lists = []
        pt = self.pivot(val,rows=[factor],
                        aggregate='tolist',
                        where=where)
        for L in pt:
            list_of_lists.append(L[0])

        # build list of condiitons
        conditions_list = [tup[1] for [tup] in pt.rnames]

        a = Anova1way()
        a.run(list_of_lists, val, factor, conditions_list, posthoc='tukey')
        return a

    def chisquare1way(self, observed, expected_dict=None,
                      alpha=0.05, where=None):
        """
        Returns a ChiSquare1way object containing the results of a
        chi-square goodness-of-fit test on the data in observed. The data
        in the observed column are treated a categorical. Expected counts
        can be given with the expected_dict. It should be a dictionary
        object with keys matching the categories in observed and values
        with the expected counts. The categories in the observed column
        must be a subset of the keys in the expected_dict. If
        expected_dict is None,the total N is assumed to be equally
        distributed across all groups.
        """
        # ched the expected_dict
        if expected_dict != None:
            try:
                expected_dict2 = dict(copy(expected_dict))
            except:
                raise TypeError("'%s' is not a mappable type"
                                %type(expected_dict).__name__())

            if not self.conditions[observed] <= set(expected_dict2.keys()):
                raise Exception('expected_dict must contain a superset of  '
                                'of the observed categories')
        else:
            expected_dict2 = Counter()

        # find the counts
        observed_dict=Counter(self.select_col(observed, where))

        # build arguments for ChiSquare1way
        observed_list = []
        expected_list = []
        conditions_list = sorted(set(observed_dict.keys()) |
                                 set(expected_dict2.keys()))
        for key in conditions_list:
            observed_list.append(observed_dict[key])
            expected_list.append(expected_dict2[key])

        if expected_dict == None:
            expected_list = None

        # run analysis
        x = ChiSquare1way()
        x.run(observed_list, expected_list, conditions_list=conditions_list,
              measure=observed, alpha=alpha)

        return x

    def chisquare2way(self, rfactor, cfactor, alpha=0.05, where=None):
        row_factor = self.select_col(rfactor, where)
        col_factor = self.select_col(cfactor, where)

        x2= ChiSquare2way()
        x2.run(row_factor, col_factor, alpha=alpha)
        return x2


    def correlation(self, variables, coefficient='pearson',
                    alpha=0.05, where=None):
        """
        calculates a correlation matrix between the measures
        in the the variables parameter. The correlation
        coefficient can be set to pearson, spearman,
        kendalltau, or pointbiserial.
        """
        list_of_lists = []
        for var in sorted(variables):
            list_of_lists.append(self.select_col(var, where))

        cor= Correlation()
        cor.run(list_of_lists, sorted(variables),
                coefficient=coefficient, alpha=alpha)
        return cor

    def ttest(self, aname, bname=None, pop_mean=0., paired=False,
              equal_variance=True, where=None):
        """
        If bname is not specified a one-way t-test is performed on
        comparing the values in column aname with a hypothesized
        population mean of 0. The hypothesized population mean can
        be specified through the pop_mean parameter.

        If bname is provided the values in aname and bname are
        compared. When paired is True. A matched pairs t-test is
        performed and the equal_variance parameter is ignored.

        When paired is false the samples in aname and bname are
        treated as independent.
        """
        if where == None:
            where = []

        if self == {}:
            raise Exception('Table must have data to find marginals')

        # check to see if data columns have equal lengths
        if not self._are_col_lengths_equal():
            raise Exception('columns have unequal lengths')

        adata = self.select_col(aname, where=where)
        if bname != None:
            bdata = self.select_col(bname, where=where)
        else:
            bdata = None

        t = Ttest()
        t.run(adata, bdata, pop_mean=pop_mean,
              paired=paired, equal_variance=equal_variance,
              aname=aname, bname=bname)
        return t

    def histogram(self, cname, where=None, bins=10,
                  range=None, density=False, cumulative=False):
        """
        Returns Histogram object
        """
        if where == None:
            where = []

        if self == {}:
            raise Exception('Table must have data to calculate histogram')

        # check to see if data columns have equal lengths
        if not self._are_col_lengths_equal():
            raise Exception('columns have unequal lengths')

        if cname not in self.names():
            raise KeyError(cname)

        V = sorted(self.select_col(cname, where=where))
        h = Histogram()
        h.run(V, cname=cname, bins=bins, range=range,
              density=density, cumulative=cumulative)
        return h

# conditionally load plot methods
    if HAS_NUMPY and HAS_PYLAB and HAS_SCIPY:
        from anova import Anova
        def anova(self, dv, sub='SUBJECT', wfactors=None, bfactors=None,
                  measure='', transform='', alpha=0.05):
            aov=Anova()
            aov.run(self, dv, sub=sub, wfactors=wfactors, bfactors=bfactors,
                    measure=measure, transform=transform, alpha=alpha)
            return aov

    # conditionally load plot methods
    if HAS_NUMPY and HAS_PYLAB:
        def histogram_plot(self, val, where=None, bins=10,
                      range=None, density=False, cumulative=False,
                      fname=None, quality='medium'):
            """
            Creates a histogram plot with the specified parameters
            """

            if where == None:
                where = []

            # check fname
            if not isinstance(fname, _strobj) and fname != None:
                raise TypeError('fname must be None or string')

            if isinstance(fname, _strobj):
                if not (fname.lower().endswith('.png') or \
                        fname.lower().endswith('.svg')):
                    raise Exception('fname must end with .png or .svg')

            # select_col does checking of val and where
            v = self.select_col(val, where=where)

            fig=pylab.figure()
            tup = pylab.hist(np.array(v), bins=bins, range=range,
                             normed=density, cumulative=cumulative)
            pylab.title(val)

            if fname == None:
                fname = 'hist(%s).png'%val.lower()

            # save figure
            if quality == 'low' or fname.endswith('.svg'):
                pylab.savefig(fname)

            elif quality == 'medium':
                pylab.savefig(fname, dpi=200)

            elif quality == 'high':
                pylab.savefig(fname, dpi=300)

            else:
                pylab.savefig(fname)

            pylab.close()

            if self.TESTMODE:
                # build and return test dictionary
                return {'bins':tup[0], 'counts':tup[1], 'fname':fname}

    # conditionally load plot methods
    if HAS_NUMPY and HAS_PYLAB:
        def scatter_plot(self, aname, bname, where=None,
                         fname=None, quality='medium'):
            """
            Creates a scatter plot with the specified parameters
            """

            if where == None:
                where = []

            # check fname
            if not isinstance(fname, _strobj) and fname != None:
                raise TypeError('fname must be None or string')

            if isinstance(fname, _strobj):
                if not (fname.lower().endswith('.png') or \
                        fname.lower().endswith('.svg')):
                    raise Exception('fname must end with .png or .svg')

            # select_col does checking of aname, bnames, and where
            adata = self.select_col(aname, where)
            bdata = self.select_col(bname, where)

            fig=pylab.figure()
            pylab.scatter(adata, bdata)
            pylab.xlabel(aname)
            pylab.ylabel(bname)

            if fname == None:
                fname = 'scatter(%sX%s).png'%(aname.lower(),bname.lower())

            # save figure
            if quality == 'low' or fname.endswith('.svg'):
                pylab.savefig(fname)

            elif quality == 'medium':
                pylab.savefig(fname, dpi=200)

            elif quality == 'high':
                pylab.savefig(fname, dpi=300)

            else:
                pylab.savefig(fname)

            pylab.close()

            if self.TESTMODE:
                # build and return test dictionary
                return {'bins':tup[0], 'counts':tup[1], 'fname':fname}

    # conditionally load plot methods
    if HAS_NUMPY and HAS_PYLAB:
        def box_plot(self, val, factors=None, where=None,
                fname=None, quality='medium'):
            """
            Creates a box plot with the specified parameters
            """

            if factors == None:
                factors = []

            if where == None:
                where = []

            # check to see if there is any data in the table
            if self == {}:
                raise Exception('Table must have data to print data')

            # check to see if data columns have equal lengths
            if not self._are_col_lengths_equal():
                raise Exception('columns have unequal lengths')

            # check the supplied arguments
            if val not in self.names():
                raise KeyError(val)

            if not hasattr(factors, '__iter__'):
                raise TypeError( "'%s' object is not iterable"
                                 % type(factors).__name__)

            for k in factors:
                if k not in self.names():
                    raise KeyError(k)

            # check for duplicate names
            dup = Counter([val]+factors)
            del dup[None]
            if not all([count==1 for count in dup.values()]):
                raise Exception('duplicate labels specified as plot parameters')

            # check fname
            if not isinstance(fname, _strobj) and fname != None:
                raise TypeError('fname must be None or string')

            if isinstance(fname, _strobj):
                if not (fname.lower().endswith('.png') or \
                        fname.lower().endswith('.svg')):
                    raise Exception('fname must end with .png or .svg')

            test = {}

            if factors == []:
                d = self.select_col(val, where=where)
                fig = pylab.figure()
                pylab.boxplot(np.array(d))
                xticks = pylab.xticks()[0]
                xlabels = [val]
                pylab.xticks(xticks, xlabels)

                test['d'] = d
                test['val'] = val

            else:
                D = self.pivot(val, rows=factors,
                               where=where,
                               aggregate='tolist')

                fig = pylab.figure(figsize=(6*len(factors),6))
                fig.subplots_adjust(left=.05, right=.97, bottom=0.24)
                pylab.boxplot([np.array(_flatten(d)) for d in D])
                xticks = pylab.xticks()[0]
                xlabels = ['\n'.join('%s = %s'%fc for fc in c) for c in D.rnames]
                pylab.xticks(xticks, xlabels,
                             rotation='vertical',
                             verticalalignment='top')

                test['d'] = [np.array(_flatten(d)) for d in D]
                test['xlabels'] = xlabels

            maintitle = '%s'%val

            if factors != []:
                maintitle += ' by '
                maintitle += ' * '.join(factors)

            fig.text(0.5, 0.95, maintitle,
                     horizontalalignment='center',
                     verticalalignment='top')

            test['maintitle'] = maintitle

            if fname == None:
                fname = 'box(%s).png'%val.lower()

            test['fname'] = fname

            # save figure
            if quality == 'low' or fname.endswith('.svg'):
                pylab.savefig(fname)

            elif quality == 'medium':
                pylab.savefig(fname, dpi=200)

            elif quality == 'high':
                pylab.savefig(fname, dpi=300)

            else:
                pylab.savefig(fname)

            pylab.close()

            if self.TESTMODE:
                return test

    # conditionally load plot methods
    if HAS_NUMPY and HAS_PYLAB:
        def interaction_plot(self, val, xaxis,
                        seplines=None, sepxplots=None, sepyplots=None,
                        xmin='AUTO', xmax='AUTO', ymin='AUTO', ymax='AUTO',
                        where=None, fname=None, quality='low', yerr=None):
            """
            Creates an interaction plot with the specified parameters
            """

            ##############################################################
            # interaction_plot programmatic flow                         #
            ##############################################################
            #  1. Check to make sure a plot can be generated with the    #
            #     specified arguments and parameter                      #
            #  2. Set yerr aggregate                                     #
            #  3. Figure out ymin and ymax if 'AUTO' is specified        #
            #  4. Figure out how many subplots we need to make and the   #
            #     levels of those subplots                               #
            #  5. Initialize pylab.figure and set plot parameters        #
            #  6. Build and set main title                               #
            #  7. loop through the the rlevels and clevels and make      #
            #     subplots                                               #
            #      7.1 Create new axes for the subplot                   #
            #      7.2 Add subplot title                                 #
            #      7.3 Format the subplot                                #
            #      7.4 Iterate plotnum counter                           #
            #  8. Place yerr text in bottom right corner                 #
            #  9. Save the figure                                        #
            # 10. return the test dictionary                             #
            ##############################################################

            #  1. Check to make sure a plot can be generated with the
            #     specified arguments and parameter
            ##############################################################
            # pylab doesn't like not being closed. To avoid starting
            # a plot without finishing it, we do some extensive checking
            # up front

            if where == None:
                where = []

            # check for data
            if self == {}:
                raise Exception('Table must have data to plot marginals')

            # check to see if data columns have equal lengths
            if not self._are_col_lengths_equal():
                raise Exception('columns have unequal lengths')

            # check to make sure arguments are column labels
            if val not in self.names():
                raise KeyError(val)

            if xaxis not in self.names():
                raise KeyError(xaxis)

            if seplines not in self.names() and seplines != None:
                raise KeyError(seplines)

            if sepxplots not in self.names() and sepxplots != None:
                raise KeyError(sepxplots)

            if sepyplots not in self.names() and sepyplots != None:
                raise KeyError(sepyplots)

            # check for duplicate names
            dup = Counter([val, xaxis, seplines, sepxplots, sepyplots])
            del dup[None]
            if not all([count == 1 for count in dup.values()]):
                raise Exception('duplicate labels specified as plot parameters')

            # check fname
            if not isinstance(fname, _strobj) and fname != None:
                raise TypeError('fname must be None or string')

            if isinstance(fname, _strobj):
                if not (fname.lower().endswith('.png') or \
                        fname.lower().endswith('.svg')):
                    raise Exception('fname must end with .png or .svg')

            # check cell counts
            cols = [f for f in [seplines, sepxplots, sepyplots] if f in self.names()]
            counts = self.pivot(val, rows=[xaxis], cols=cols,
                                flatten=True, where=where, aggregate='count')

            for count in counts:
                if count < 1:
                    raise Exception('cell count too low to calculate mean')

            #  2. Initialize test dictionary
            ##############################################################
            # To test the plotting a dict with various plot parameters
            # is build and returned to the testing module. In this
            # scenario our primary concern is that the values represent
            # what we think they represent. Whether they match the plot
            # should be fairly obvious to the user.
            test = {}

            #  3. Set yerr aggregate so sqlite knows how to calculate yerr
            ##############################################################

            # check yerr
            aggregate = None
            if yerr == 'sem':
                aggregate = 'sem'

            elif yerr == 'stdev':
                aggregate = 'stdev'

            elif yerr == 'ci':
                aggregate = 'ci'

            for count in counts:
                if aggregate != None and count < 2:
                    raise Exception('cell count too low to calculate %s'%yerr)

            test['yerr'] = yerr
            test['aggregate'] = aggregate

            #  4. Figure out ymin and ymax if 'AUTO' is specified
            ##############################################################
            desc = self.descriptives(val)

            if ymin == 'AUTO':
                # when plotting postive data always have the y-axis go to 0
                if desc['min'] >= 0.:
                    ymin = 0.
                else:
                    ymin = desc['mean'] - 3.*desc['stdev']
            if ymax == 'AUTO':
                ymax = desc['mean'] + 3.*desc['stdev']

            if any([math.isnan(ymin), math.isinf(ymin), math.isnan(ymax), math.isinf(ymax)]):
                raise Exception('calculated plot bounds nonsensical')

            test['ymin'] = ymin
            test['ymax'] = ymax

            #  5. Figure out how many subplots we need to make and the
            #     levels of those subplots
            ##############################################################
            numrows = 1
            rlevels = [1]
            if sepyplots != None:
                rlevels = copy(counts.conditions[sepyplots]) # a set
                numrows = len(rlevels) # a int
                rlevels = sorted(rlevels) # set -> sorted list

            numcols = 1
            clevels = [1]
            if sepxplots != None:
                clevels = copy(counts.conditions[sepxplots])
                numcols = len(clevels)
                clevels = sorted(clevels) # set -> sorted list

            test['numrows']  = numrows
            test['rlevels']  = rlevels
            test['numcols']  = numcols
            test['clevels']  = clevels

            #  6. Initialize pylab.figure and set plot parameters
            ##############################################################
            fig = pylab.figure(figsize=(6*numcols, 4*numrows+1))
            fig.subplots_adjust(wspace=.05, hspace=0.2)

            #  7. Build and set main title
            ##############################################################
            maintitle = '%s by %s'%(val,xaxis)

            if seplines:
                maintitle += ' * %s'%seplines
            if sepxplots:
                maintitle += ' * %s'%sepxplots
            if sepyplots:
                maintitle += ' * %s'%sepyplots

            fig.text(0.5, 0.95, maintitle,
                     horizontalalignment='center',
                     verticalalignment='top')

            test['maintitle']  = maintitle

            #  8. loop through the the rlevels and clevels and make
            #     subplots
            ##############################################################
            test['y'] = []
            test['yerr'] = []
            test['subplot_titles'] = []
            test['xmins'] = []
            test['xmaxs'] = []

            plotnum = 1 # subplot counter
            axs = []

            for r, rlevel in enumerate(rlevels):
                for c, clevel in enumerate(clevels):

                    #  8.1 Create new axes for the subplot
                    ######################################################
                    axs.append(pylab.subplot(numrows, numcols, plotnum))

                    ######## If separate lines are not specified #########
                    if seplines == None:
                        y = self.pivot(val, cols=[xaxis], where=where,
                                       aggregate='avg', flatten=True)

                        if aggregate != None:
                            yerr = self.pivot(val, cols=[xaxis],
                                              where=where,
                                              aggregate=aggregate,
                                              flatten=True)

                        x = [name for [(label, name)] in y.cnames]

                        if _isfloat(yerr):
                            yerr = np.array([yerr for a in x])

                        if all([_isfloat(a) for a in x]):
                            axs[-1].errorbar(x, y, yerr)
                            if xmin == 'AUTO' and xmax == 'AUTO':
                                xmin, xmax = axs[-1].get_xlim()
                                xran = xmax - xmin
                                xmin = xmin - 0.05*xran
                                xmax = xmax + 0.05*xran

                            axs[-1].plot([xmin, xmax], [0., 0.], 'k:')

                        else : # categorical x axis
                            axs[-1].errorbar(_xrange(len(x)), y, yerr)
                            pylab.xticks(_xrange(len(x)), x)
                            xmin = - 0.5
                            xmax = len(x) - 0.5

                            axs[-1].plot([xmin, xmax], [0., 0.], 'k:')

                    ########## If separate lines are specified ###########
                    else:
                        y = self.pivot(val, rows=[seplines], cols=[xaxis],
                                       where=where, aggregate='avg',
                                       flatten=False)

                        if aggregate != None:
                            yerrs = self.pivot(val,
                                               rows=[seplines],
                                               cols=[xaxis],
                                               where=where,
                                               aggregate=aggregate,
                                               flatten=False)

                        x = [name for [(label, name)] in y.cnames]

                        if _isfloat(yerr):
                            yerr = np.array([yerr for a in x])

                        plots = []
                        labels = []
                        for i, name in enumerate(y.rnames):
                            if aggregate != None:
                                yerr = yerrs[i]

                            labels.append(name[0][1])

                            if all([_isfloat(a) for a in x]):
                                plots.append(
                                    axs[-1].errorbar(x, y[i], yerr)[0])

                                if xmin == 'AUTO' and xmax == 'AUTO':
                                    xmin , xmax = axs[-1].get_xlim()
                                    xran = xmax - xmin
                                    xmin = xmin - .05*xran
                                    xmax = xmax + .05*xran

                                axs[-1].plot([xmin, xmax], [0.,0.], 'k:')

                            else : # categorical x axis
                                plots.append(
                                    axs[-1].errorbar(
                                        _xrange(len(x)), y[i],yerr)[0])

                                pylab.xticks(_xrange(len(x)), x)
                                xmin = - 0.5
                                xmax = len(x) - 0.5

                                axs[-1].plot([xmin, xmax], [0., 0.], 'k:')

                        pylab.figlegend(plots, labels, loc=1,
                                        labelsep=.005,
                                        handlelen=.01,
                                        handletextsep=.005)

                    test['y'].append(y)
                    if yerr == None:
                        test['yerr'].append([])
                    else:
                        test['yerr'].append(yerr)
                    test['xmins'].append(xmin)
                    test['xmaxs'].append(xmax)

                    #  8.2 Add subplot title
                    ######################################################
                    if rlevels == [1] and clevels == [1]:
                        title = ''

                    elif rlevels == [1]:
                        title = _str(clevel)

                    elif clevels == [1]:
                        title = _str(rlevel)

                    else:
                        title = '%s = %s, %s = %s' \
                                % (sepyplots, _str(rlevel),
                                   sepxplots, _str(rlevel))

                    pylab.title(title, fontsize='medium')
                    test['subplot_titles'].append(title)

                    #  8.3 Format the subplot
                    ######################################################
                    pylab.xlim(xmin, xmax)
                    pylab.ylim(ymin, ymax)

                    # supress tick labels unless subplot is on the bottom
                    # row or the far left column
                    if r != (len(rlevels) - 1):
                        locs, labels = pylab.xticks()
                        pylab.xticks(locs, ['' for l in _xrange(len(locs))])

                    if c != 0:
                        locs, labels = pylab.yticks()
                        pylab.yticks(locs, ['' for l in _xrange(len(locs))])

                    # Set the aspect ratio for the subplot
                    Dx = abs(axs[-1].get_xlim()[0] - axs[-1].get_xlim()[1])
                    Dy = abs(axs[-1].get_ylim()[0] - axs[-1].get_ylim()[1])
                    axs[-1].set_aspect(.75*Dx/Dy)

                    #  8.4 Iterate plotnum counter
                    ######################################################
                    plotnum += 1

            #  9. Place yerr text in bottom right corner
            ##############################################################
            if aggregate != None:
                if aggregate == 'ci':
                    aggregate = '95% ci'

                pylab.xlabel('\n\n                '
                             '*Error bars reflect %s'\
                             %aggregate.upper())

            # 10. Save the figure
            ##############################################################
            if fname == None:
                fname = maintitle.lower() \
                                 .replace('by', '~') \
                                 .replace('*', 'X') \
                                 .replace(' ', '')

            if quality == 'low' or fname.endswith('.svg'):
                pylab.savefig(fname)

            elif quality == 'medium':
                pylab.savefig(fname, dpi=200)

            elif quality == 'high':
                pylab.savefig(fname, dpi=300)

            else:
                pylab.savefig(fname)

            pylab.close()

            test['fname'] = fname

            # 11. return the test dictionary
            ##############################################################
            if self.TESTMODE:
                return test

class PyvtTbl(list):
    """
    list of lists container holding the pivoted data
    """
    def __init__(self, *args, **kwds):
        if len(args) > 1:
            raise Exception('expecting only 1 argument')

        if kwds.has_key('val'):
            self.val = kwds['val']
        else:
            self.val = None

        if kwds.has_key('show_tots'):
            self.show_tots = kwds['show_tots']
        else:
            self.show_tots = True

        if kwds.has_key('calc_tots'):
            self.calc_tots = kwds['calc_tots']
        else:
            self.calc_tots = True

        if kwds.has_key('row_tots'):
            self.row_tots = kwds['row_tots']
        else:
            self.row_tots = None

        if kwds.has_key('col_tots'):
            self.col_tots = kwds['col_tots']
        else:
            self.col_tots = None

        if kwds.has_key('grand_tot'):
            self.grand_tot = kwds['grand_tot']
        else:
            self.grand_tot = None

        if kwds.has_key('rnames'):
            self.rnames = kwds['rnames']
        else:
            self.rnames = None

        if kwds.has_key('cnames'):
            self.cnames = kwds['cnames']
        else:
            self.cnames = None

        if kwds.has_key('aggregate'):
            self.aggregate = kwds['aggregate']
        else:
            self.aggregate = 'avg'

        if kwds.has_key('flatten'):
            self.flatten = kwds['flatten']
        else:
            self.flatten = False

        if kwds.has_key('where'):
            self.where = kwds['where']
        else:
            self.where = []

        if kwds.has_key('attach_rlabels'):
            self.attach_rlabels = kwds['attach_rlabels']
        else:
            self.attach_rlabels = False

        if len(args) == 1:
            super(PyvtTbl, self).__init__(args[0])
        else:
            super(PyvtTbl, self).__init__()

    def run(self, df, val, rows=None, cols=None,
                 aggregate='avg', where=None, flatten=False,
                 attach_rlabels=False, calc_tots=True):

        # public method, saves table to df variables after pivoting
        """
        val = the colname to place as the data in the table
        rows = list of colnames whos combinations will become rows
               in the table if left blank their will be one row
        cols = list of colnames whos combinations will become cols
               in the table if left blank their will be one col
        aggregate = function applied across data going into each cell
                  of the table
                  http://www.sqlite.org/lang_aggfunc.html
        where = list of tuples or list of strings for filtering data
        """

        if rows == None:
            rows = []

        if cols == None:
            cols = []

        if where == None:
            where = []

        ##############################################################
        # pivot programmatic flow                                    #
        ##############################################################
        #  1.  Check to make sure the table can be pivoted with the  #
        #      specified parameters                                  #
        #  2.  Create a sqlite table with only the data in columns   #
        #      specified by val, rows, and cols. Also eliminate      #
        #      rows that meet the exclude conditions                 #
        #  3.  Build rnames and cnames lists                         #
        #  4.  Build query based on val, rows, and cols              #
        #  5.  Run query                                             #
        #  6.  Read data to from cursor into a list of lists         #
        #  7.  Query grand, row, and column totals                   #
        #  8.  Clean up                                              #
        #  9.  flatten if specified                                  #
        #  10. return data, rnames, and cnames                       #
        ##############################################################

        #  1. Check to make sure the table can be pivoted with the
        #     specified parameters
        ##############################################################
        #  This may seem excessive but it provides better feedback
        #  to the user if the errors can be parsed out before had
        #  instead of crashing on confusing looking code segments


        # check to see if data columns have equal lengths
        if not df._are_col_lengths_equal():
            raise Exception('columns have unequal lengths')

        # check the supplied arguments
        if val not in df.names():
            raise KeyError(val)

        if not hasattr(rows, '__iter__'):
            raise TypeError( "'%s' object is not iterable"
                             % type(cols).__name__)

        if not hasattr(cols, '__iter__'):
            raise TypeError( "'%s' object is not iterable"
                             % type(cols).__name__)

        for k in rows:
            if k not in df.names():
                raise KeyError(k)

        for k in cols:
            if k not in df.names():
                raise KeyError(k)

        # check for duplicate names
        dup = Counter([val] + rows + cols)
        del dup[None]
        if not all(count == 1 for count in dup.values()):
            raise Exception('duplicate labels specified')

        # check aggregate function
        aggregate = aggregate.lower()

        if aggregate not in df.aggregates:
            raise ValueError("supplied aggregate '%s' is not valid"%aggregate)

        # check to make sure where is properly formatted
        # todo

        #  2. Create a sqlite table with only the data in columns
        #     specified by val, rows, and cols. Also eliminate
        #     rows that meet the exclude conditions
        ##############################################################
        df._build_sqlite3_tbl([val] + rows + cols, where)

        #  3. Build rnames and cnames lists
        ##############################################################

        # Refresh conditions list so we can build row and col list
        df._execute('select %s from TBL'
                      %', '.join('_%s_'%n for n in [val] + rows + cols))
        Zconditions = DictSet(zip([val]+rows+cols, zip(*list(df.cur))))

        # Build rnames
        if rows == []:
            rnames = [1]
        else:
            g = Zconditions.unique_combinations(rows)
            rnames = [zip(rows, v) for v in g]

        rsize = len(rnames)

        # Build cnames
        if cols == []:
            cnames = [1]
        else:
            g = Zconditions.unique_combinations(cols)
            cnames = [zip(cols, v) for v in g]

        csize=len(cnames)

        #  4. Build query based on val, rows, and cols
        ##############################################################
        #  Here we are using string formatting to build the query.
        #  This method is generally discouraged for security, but
        #  in this circumstance I think it should be okay. The column
        #  labels are protected with leading and trailing underscores.
        #  The rest of the query is set by the logic.
        #
        #  When we pass the data in we use the (?) tuple format
        if aggregate == 'tolist':
            agg = 'group_concat'
        else:
            agg = aggregate

        query = ['select ']
        if rnames == [1] and cnames == [1]:
            query.append('%s( _%s_ ) from TBL'%(agg, val))
        else:
            if rnames == [1]:
                query.append('_%s_'%val)
            else:
                query.append(', '.join('_%s_'%r for r in rows))

            if cnames == [1]:
                query.append('\n  , %s( _%s_ )'%(agg, val))
            else:
                for cs in cnames:
                    query.append('\n  , %s( case when '%agg)
                    if all(map(_isfloat, zip(*cs)[1])):
                        query.append(
                        ' and '.join(('_%s_=%s'%(k, v) for k, v in cs)))
                    else:
                        query.append(
                        ' and '.join(('_%s_="%s"'%(k ,v) for k, v in cs)))
                    query.append(' then _%s_ end )'%val)

            if rnames == [1]:
                query.append('\nfrom TBL')
            else:
                query.append('\nfrom TBL group by ')

                for i, r in enumerate(rows):
                    if i != 0:
                        query.append(', ')
                    query.append('_%s_'%r)

        #  5. Run Query
        ##############################################################
        df._execute(''.join(query))

        #  6. Read data to from cursor into a list of lists
        ##############################################################

        d = []
        val_type = df.typesdict()[val]

        # keep the columns with the row labels
        if attach_rlabels:
            if aggregate == 'tolist':
                for row in df.cur:
                    d.append([])
                    for cell in list(row):
                        if val_type == 'real' or val_type == 'integer':
                            d[-1].append(eval('[%s]'%cell))
                        else:
                            d[-1].append(cell.split(','))
            else:
                for row in df.cur:
                    d.append(list(row))

            cnames = [(r, '') for r in rows].extend(cnames)

        # eliminate the columns with row labels
        else:
            if aggregate == 'tolist':
                for row in df.cur:
                    d.append([])
                    for cell in list(row)[-len(cnames):]:
                        if val_type == 'real' or val_type == 'integer':
                            d[-1].append(eval('[%s]'%cell))
                        else:
                            d[-1].append(cell.split(','))
            else:
                for row in df.cur:
                    d.append(list(row)[-len(cnames):])

        #  7. Get totals
        ##############################################################
        if calc_tots:
            if aggregate in ['tolist', 'group_concat', 'arbitrary']:
                self.calc_tots = False
            else:
                query = 'select %s( _%s_ ) from TBL'%(agg, val)
                df._execute(query)
                self.grand_tot = list(df.cur)[0][0]

                if cnames != [1] and rnames != [1]:
                    query = ['select %s( _%s_ ) from TBL group by'%(agg, val)]
                    query.append(', '.join('_%s_'%r for r in rows))
                    df._execute(' '.join(query))
                    self.row_tots = [tup[0] for tup in df.cur]

                    query = ['select %s( _%s_ ) from TBL group by'%(agg, val)]
                    query.append(', '.join('_%s_'%r for r in cols))
                    df._execute(' '.join(query))
                    self.col_tots = [tup[0] for tup in df.cur]

        #  8. Clean up
        ##############################################################
        df.conn.commit()

        #  9. flatten if specified
        ##############################################################
        if flatten:
            d = _flatten(d)

        #  10. set data, rnames, and cnames
        ##############################################################
        self.df = df
        self.val = val
        self.rows = rows
        self.cols = cols
        self.aggregate = aggregate
        self.where = where
        self.flatten = flatten
        self.attach_rlabels = attach_rlabels

        self.rnames = rnames
        self.cnames = cnames
        self.aggregate = aggregate
        self.conditions = Zconditions

        super(PyvtTbl, self).__init__(d)

    def transpose(self):
        """
        tranpose the pivot table in place
        """
        super(PyvtTbl,self).__init__([list(r) for r in zip(*self)])
        self.rnames,self.cnames = self.cnames,self.rnames
        self.row_tots,self.col_tots = self.col_tots,self.row_tots

    def _are_row_lengths_equal(self):
        """
        private method to check if the lists in self have equal lengths

          returns True if all the items are equal
          returns False otherwise
        """
        # if self is not empty
        counts = map(len, self.__iter__())
        if all(c - counts[0] + 1 == 1 for c in counts):
            return True
        else:
            return False

    def _get_rows(self):
        """
        returns a list of tuples containing row labels and conditions
        """
        if self.rnames == [1]:
            return [1]
        else:
            return [str(k) for (k, v) in self.rnames[0]]

    def _get_cols(self):
        """
        returns a list of tuples containing column labels and conditions
        """
        if self.cnames == [1]:
            return [1]
        else:
            return [str(k) for (k, v) in self.cnames[0]]

    def shape(self):
        """
        returns the size of the pivot table as a tuple. Does not
        include row label columns.

          The first element is the number of columns.
          The second element is the number of rows
        """
        if len(self) == 0:
            return (0, 0)

        return (len(self.rnames), len(self[0]))

    def write(self, fname=None, delimiter=','):
        """
        writes the pivot table to a plaintext file

          as currently implemented does not write grandtotals
        """

        if self == []:
            raise Exception('must call pivot before writing pivot table')

        rows = self._get_rows()
        cols = self._get_cols()

        # check or build fname
        if fname != None:
            if not isinstance(fname, _strobj):
                raise TypeError('fname must be a string')
        else:
            # if rows == [1] then lower_rows becomes ['']
            # if cols...
            lower_rows = [str(n).lower().replace('1','') for n in rows]
            lower_cols = [str(n).lower().replace('1','') for n in cols]

            fname = '%s~(%s)Z(%s)'%(self.val.lower(),
                                    'X'.join(lower_rows),
                                    'X'.join(lower_cols))
            if delimiter == ',':
                fname += '.csv'
            elif delimiter == '\t':
                fname += '.tsv'
            else:
                fname += '.txt'

        # build and write first line
        first = ['%s(%s)'%(self.aggregate, self.val)]

        data = [] # append the rows to this list and write with
                  # csv writer in one call

        # no rows or cols were specified
        if self.rnames == [1] and self.cnames == [1]:
            # build and write the header
            header = ['Value']

            # initialize the texttable and add stuff
            data.append(self[0])

        elif self.rnames == [1]: # no rows were specified
            # build the header
            header = ['_'.join('%s=%s'%(f, c) for (f, c) in L) \
                      for L in self.cnames]

            # initialize the texttable and add stuff
            data.append(self[0])

        elif self.cnames == [1]: # no cols were specified
            # build the header
            header = rows + ['Value']

            # initialize the texttable and add stuff
            for i, L in enumerate(self.rnames):
                data.append([c for (f, c) in L] + self[i])

        else: # table has rows and cols
            # build the header
            header = copy(rows)
            for L in self.cnames:
                header.append('_'.join('%s=%s'%(f, c) for (f, c) in L))

            # initialize the texttable and add stuff
            for i, L in enumerate(self.rnames):
                data.append([c for (f, c) in L] + self[i])

        # write file
        with open(fname, 'wb') as fid:
            wtr = csv.writer(fid, delimiter=delimiter)
            wtr.writerow(first)
            wtr.writerow(header)
            wtr.writerows(data)

    def __str__(self):
        """
        returns a human friendly string representation of the table
        """
        if self == []:
            return '(table is empty)'

        if self.flatten:
            return super(PyvtTbl, self).__str__()

        showtots = self.show_tots and self.calc_tots

        rows = self._get_rows()
        cols = self._get_cols()

        # initialize table
        tt = TextTable(max_width=0)

        # no rows or cols were specified
        if self.rnames == [1] and self.cnames == [1]:
            # build the header
            header = ['Value']

            # initialize the texttable and add stuff
            tt.set_cols_dtype(['t'])
            tt.set_cols_dtype(['l'])
            tt.add_row(self[0])

        elif self.rnames == [1]: # no rows were specified
            # build the header
            header = [',\n'.join('%s=%s'%(f, c) for (f, c) in L) \
                      for L in self.cnames]
            if showtots:
                header.append('Total')

            # initialize the texttable and add stuff
            # False and True evaluate as 0 and 1 for integer addition
            # and list indexing
            tt.set_cols_dtype(['a'] * (len(self.cnames)+showtots))
            tt.set_cols_align(['r'] * (len(self.cnames)+showtots))
            tt.add_row(self[0]+([],[self.grand_tot])[showtots])

        elif self.cnames == [1]: # no cols were specified
            # build the header
            header = rows + ['Value']

            # initialize the texttable and add stuff
            tt.set_cols_dtype(['t'] * len(rows) + ['a'])
            tt.set_cols_align(['l'] * len(rows) + ['r'])
            for i, L in enumerate(self.rnames):
                try:
                    tt.add_row([c for (f, c) in L] + self[i])
                except:
                    tt.add_row([c for (f, c) in L] + [""])

            if showtots:
                tt.footer(['Total'] +
                          ['']*(len(rows)-1) +
                          [self.grand_tot])

        else: # table has rows and cols
            # build the header
            header = copy(rows)
            for L in self.cnames:
                header.append(',\n'.join('%s=%s'%(f, c) for (f, c) in L))
            if showtots:
                header.append('Total')

            dtypes = ['t'] * len(rows) + ['a'] * (len(self.cnames)+showtots)
            aligns = ['l'] * len(rows) + ['r'] * (len(self.cnames)+showtots)

            # initialize the texttable and add stuff
            tt.set_cols_dtype(dtypes)
            tt.set_cols_align(aligns)
            for i, L in enumerate(self.rnames):
                if self.row_tots:
                    row_tots = self.row_tots[i]
                else:
                    row_tots = []
                tt.add_row([c for (f, c) in L] +
                           self[i] +
                           ([],[row_tots])[showtots])

            if showtots:
                tt.footer(['Total'] +
                          ['']*(len(rows)-1) +
                          self.col_tots +
                          [self.grand_tot])

        # add header and decoration
        tt.header(header)
        tt.set_deco(TextTable.HEADER | TextTable.FOOTER)

        # return the formatted table
        return '%s(%s)\n%s'%(self.aggregate, self.val, tt.draw())

    def __repr__(self):
        """
        returns a machine friendly string representation of the object
        """
        if self == []:
            return 'PyvtTbl()'

        args = super(PyvtTbl, self).__repr__()
        kwds = []
        if self.val != None:
            kwds.append(", val='%s'"%self.val)

        if self.show_tots != True:
            kwds.append(", show_tots=False")

        if self.calc_tots != True:
            kwds.append(", calc_tots=False")

        if self.row_tots != None:
            kwds.append(', row_tots=%s'%repr(self.row_tots))

        if self.col_tots != None:
            kwds.append(', col_tots=%s'%repr(self.col_tots))

        if self.grand_tot != None:
            kwds.append(', grand_tot=%s'%repr(self.grand_tot))

        if self.rnames != None:
            kwds.append(', rnames=%s'%repr(self.rnames))

        if self.cnames != None:
            kwds.append(', cnames=%s'%repr(self.cnames))

        if self.aggregate != 'avg':
            kwds.append(", aggregate='%s'"%self.aggregate)

        if self.flatten != False:
            kwds.append(', flatten=%s'%self.flatten)

        if self.where != []:
            if isinstance(self.where, _strobj):
                kwds.append(", where='%s'"%self.where)
            else:
                kwds.append(", where=%s"%self.where)

        if self.attach_rlabels != False:
            kwds.append(', attach_rlabels=%s'%self.attach_rlabels)

        if len(kwds)>1:
            kwds = ''.join(kwds)

        return 'PyvtTbl(%s%s)'%(args,kwds)

class Ttest(OrderedDict):
    """Student's t-test"""
    def __init__(self, *args, **kwds):
        if len(args) > 1:
            raise Exception('expecting only 1 argument')

        if kwds.has_key('paired'):
            self.paired = kwds['paired']
        else:
            self.paired = False

        if kwds.has_key('equal_variance'):
            self.equal_variance = kwds['equal_variance']
        else:
            self.equal_variance = True

        if kwds.has_key('alpha'):
            self.alpha = kwds['alpha']
        else:
            self.alpha = 0.05

        if kwds.has_key('aname'):
            self.aname = kwds['aname']
        else:
            self.aname = None

        if kwds.has_key('bname'):
            self.bname = kwds['bname']
        else:
            self.bname = None

        if kwds.has_key('type'):
            self.type = kwds['type']
        else:
            self.type = None

        if len(args) == 1:
            super(Ttest, self).__init__(args[0])
        else:
            super(Ttest, self).__init__()

    def run(self, A, B=None, pop_mean=None, paired=False, equal_variance=True,
                 alpha=0.05, aname=None, bname=None):
        """
        Compares the data in A to the data in B. If A or B are
        multidimensional they are flattened before testing.

        When paired is True, the equal_variance parameter has
        no effect, an exception is raised if A and B are not
        of equal length.
          t = \frac{\overline{X}_D - \mu_0}{s_D/\sqrt{n}}
          where:
            \overline{X}_D is the difference of the averages
            s_D is the standard deviation of the differences

          \mathrm{d.f.} = n_1 - 1

        When paired is False and equal_variance is True.
          t = \frac{\bar {X}_1 - \bar{X}_2}{S_{X_1X_2} \cdot \sqrt{\frac{1}{n_1}+\frac{1}{n_2}}}
          where:
          {S_{X_1X_2} is the pooled standard deviation
          computed as:
            S_{X_1X_2} = \sqrt{\frac{(n_1-1)S_{X_1}^2+(n_2-1)S_{X_2}^2}{n_1+n_2-2}}

          \mathrm{d.f.} = n_1 + n_2 - 2

        When paired is False and equal_variance is False.
          t = {\overline{X}_1 - \overline{X}_2 \over s_{\overline{X}_1 - \overline{X}_2}}
          where:
            s_{\overline{X}_1 - \overline{X}_2} = \sqrt{{s_1^2 \over n_1} + {s_2^2  \over n_2}}
            where:
            s_1^2 and s_2^2 are the unbiased variance estimates

          \mathrm{d.f.} = \frac{(s_1^2/n_1 + s_2^2/n_2)^2}{(s_1^2/n_1)^2/(n_1-1) + (s_2^2/n_2)^2/(n_2-1)}
        """

        try:
            A = _flatten(list(copy(A)))
        except:
            raise TypeError('A must be a list-like object')

        try:
            if B != None:
                B = _flatten(list(copy(B)))
        except:
            raise TypeError('B must be a list-like object')

        if aname == None:
            self.aname = 'A'
        else:
            self.aname = aname

        if bname == None:
            self.bname = 'B'
        else:
            self.bname = bname

        self.A = A
        self.B = B
        self.paired = paired
        self.equal_variance = equal_variance
        self.alpha = alpha

        if B == None:
            t, prob2, n, df, mu, v = stats.lttest_1samp(A, pop_mean)

            self.type = 't-Test: One Sample for means'
            self['t'] = t
            self['p2tail'] = prob2
            self['p1tail'] = prob2 / 2.
            self['n'] = n
            self['df'] = df
            self['mu'] = mu
            self['pop_mean'] = pop_mean
            self['var'] = v
            self['tc2tail'] = jsci.tinv(alpha,df)
            self['tc1tail'] = jsci.tinv(2. * alpha,df)

        elif paired == True:
            if len(A) - len(B) != 0:
                raise Exception('A and B must have equal lengths '
                                'for paired comparisons')

            t, prob2, n, df, mu1, mu2, v1, v2 = stats.ttest_rel(A, B)
            r, rprob2 = stats.pearsonr(A,B)

            self.type = 't-Test: Paired Two Sample for means'
            self['t'] = t
            self['p2tail'] = prob2
            self['p1tail'] = prob2 / 2.
            self['n1'] = n
            self['n2'] = n
            self['r'] = r
            self['df'] = df
            self['mu1'] = mu1
            self['mu2'] = mu2
            self['var1'] = v1
            self['var2'] = v2
            self['tc2tail'] = jsci.tinv(alpha,df)
            self['tc1tail'] = jsci.tinv(2. * alpha,df)

        elif equal_variance:
            t, prob2, n1, n2, df, mu1, mu2, v1, v2, svar = stats.ttest_ind(A, B)

            self.type = 't-Test: Two-Sample Assuming Equal Variances'
            self['t'] = t
            self['p2tail'] = prob2
            self['p1tail'] = prob2 / 2.
            self['n1'] = n1
            self['n2'] = n2
            self['df'] = df
            self['mu1'] = mu1
            self['mu2'] = mu2
            self['var1'] = v1
            self['var2'] = v2
            self['vpooled'] = svar
            self['tc2tail'] = jsci.tinv(alpha,df)
            self['tc1tail'] = jsci.tinv(2. * alpha,df)

        else:
            t, prob2, n1, n2, df, mu1, mu2, v1, v2 = stats.ttest_ind_uneq(A, B)

            self.type = 't-Test: Two-Sample Assuming Unequal Variances'
            self['t'] = t
            self['p2tail'] = prob2
            self['p1tail'] = prob2 / 2.
            self['n1'] = n1
            self['n2'] = n2
            self['df'] = df
            self['mu1'] = mu1
            self['mu2'] = mu2
            self['var1'] = v1
            self['var2'] = v2
            self['tc2tail'] = jsci.tinv(alpha,df)
            self['tc1tail'] = jsci.tinv(2. * alpha,df)

    def __str__(self):

        if self == {}:
            return '(no data in object)'


        if self.B == None:
            tt = TextTable(max_width=100000000)
            tt.set_cols_dtype(['t', 'a'])
            tt.set_cols_align(['l', 'r'])
            tt.set_deco(TextTable.HEADER)

            first = 't-Test: One Sample for means\n'
            tt.header( ['',                       self.aname])
            tt.add_row(['Sample Mean',            self['mu']])
            tt.add_row(['Hypothesized Pop. Mean', self['pop_mean']])
            tt.add_row(['Variance',               self['var']])
            tt.add_row(['Observations',           self['n']])
            tt.add_row(['df',                     self['df']])
            tt.add_row(['t Stat',                 self['t']])
            tt.add_row(['P(T<=t) one-tail',       self['p1tail']])
            tt.add_row(['t Critical one-tail',    self['tc1tail']])
            tt.add_row(['P(T<=t) two-tail',       self['p2tail']])
            tt.add_row(['t Critical two-tail',    self['tc2tail']])

            return '%s\n%s'%(first, tt.draw())


        tt = TextTable(max_width=100000000)
        tt.set_cols_dtype(['t', 'a', 'a'])
        tt.set_cols_align(['l', 'r', 'r'])
        tt.set_deco(TextTable.HEADER)

        if self.paired == True:
            first = 't-Test: Paired Two Sample for means\n'
            tt.header( ['',                    self.aname,      self.bname])
            tt.add_row(['Mean',                self['mu1'],     self['mu2']])
            tt.add_row(['Variance',            self['var1'],    self['var2']])
            tt.add_row(['Observations',        self['n1'],      self['n2']])
            tt.add_row(['Pearson Correlation', self['r'],      ''])
            tt.add_row(['df',                  self['df'],      ''])
            tt.add_row(['t Stat',              self['t'],       ''])
            tt.add_row(['P(T<=t) one-tail',    self['p1tail'],  ''])
            tt.add_row(['t Critical one-tail', self['tc1tail'], ''])
            tt.add_row(['P(T<=t) two-tail',    self['p2tail'],  ''])
            tt.add_row(['t Critical two-tail', self['tc2tail'], ''])

        elif self.equal_variance:
            first = 't-Test: Two-Sample Assuming Equal Variances\n'
            tt.header( ['',                    self.aname,      self.bname])
            tt.add_row(['Mean',                self['mu1'],     self['mu2']])
            tt.add_row(['Variance',            self['var1'],    self['var2']])
            tt.add_row(['Observations',        self['n1'],      self['n2']])
            tt.add_row(['Pooled Variance',     self['vpooled'], ''])
            tt.add_row(['df',                  self['df'],      ''])
            tt.add_row(['t Stat',              self['t'],       ''])
            tt.add_row(['P(T<=t) one-tail',    self['p1tail'],  ''])
            tt.add_row(['t Critical one-tail', self['tc1tail'], ''])
            tt.add_row(['P(T<=t) two-tail',    self['p2tail'],  ''])
            tt.add_row(['t Critical two-tail', self['tc2tail'], ''])

        else:
            first = 't-Test: Two-Sample Assuming Unequal Variances\n'
            tt.header( ['',                    self.aname,      self.bname])
            tt.add_row(['Mean',                self['mu1'],     self['mu2']])
            tt.add_row(['Variance',            self['var1'],    self['var2']])
            tt.add_row(['Observations',        self['n1'],      self['n2']])
            tt.add_row(['df',                  self['df'],      ''])
            tt.add_row(['t Stat',              self['t'],       ''])
            tt.add_row(['P(T<=t) one-tail',    self['p1tail'],  ''])
            tt.add_row(['t Critical one-tail', self['tc1tail'], ''])
            tt.add_row(['P(T<=t) two-tail',    self['p2tail'],  ''])
            tt.add_row(['t Critical two-tail', self['tc2tail'], ''])

        return ''.join([first,tt.draw()])

    def __repr__(self):
        if self == {}:
            return 'Ttest()'

        s = []
        for k, v in self.items():
            s.append("('%s', %s)"%(k, repr(v)))
        args = '[' + ', '.join(s) + ']'

        kwds = []
        if self.paired != False:
            kwds.append(", paired=%s"%self.paired)

        if self.equal_variance != True:
            kwds.append(", equal_variance=%s"%self.equal_variance)

        if self.alpha != 0.05:
            kwds.append(", alpha=%s"%self.alpha)

        if self.aname != None:
            kwds.append(", aname='%s'"%self.aname)

        if self.bname != None:
            kwds.append(", bname='%s'"%self.bname)

        if self.type != None:
            kwds.append(", type='%s'"%self.type)

        kwds= ''.join(kwds)

        return 'Ttest(%s%s)'%(args,kwds)

class Anova1way(OrderedDict):
    """1-way ANOVA"""
    def __init__(self, *args, **kwds):
        if len(args) > 1:
            raise Exception('expecting only 1 argument')

        if kwds.has_key('posthoc'):
            self.posthoc = kwds['posthoc']
        else:
            self.posthoc = 'tukey'

        if kwds.has_key('multtest'):
            self.multtest = kwds['multtest']
        else:
            self.multtest = None

        if kwds.has_key('val'):
            self.val = kwds['val']
        else:
            self.val = 'Measure'

        if kwds.has_key('factor'):
            self.factor = kwds['factor']
        else:
            self.factor = 'Factor'

        if kwds.has_key('conditions_list'):
            self.conditions_list = kwds['conditions_list']
        else:
            self.conditions_list = []

        if kwds.has_key('alpha'):
            self.alpha = kwds['alpha']
        else:
            self.alpha = 0.05

        if len(args) == 1:
            super(Anova1way, self).__init__(args[0])
        else:
            super(Anova1way, self).__init__()

    def run(self, list_of_lists, val='Measure',
            factor='Factor', conditions_list=None,
            posthoc='tukey', alpha=0.05):
        """
        performs a one way analysis of variance on the data in
        list_of_lists. Each sub-list is treated as a group. factor
        is a label for the independent variable and conditions_list
        is a list of labels for the different treatment groups.
        """
        self.L = list_of_lists
        self.val = val
        self.factor = factor
        self.alpha = alpha

        if conditions_list == None:
            abc = lambda i : 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'\
                             [i%26]*(int(math.floor(i/26))+1)
            for i in _xrange(len(list_of_lists)):
                self.conditions_list.append(abc(i))
        else:
            self.conditions_list = conditions_list

        f, prob, ns, means, vars, ssbn, sswn, dfbn, dfwn = \
           stats.lF_oneway(list_of_lists)

        self['f'] = f
        self['p'] = prob
        self['ns'] = ns
        self['mus'] = means
        self['vars'] = vars
        self['ssbn'] = ssbn
        self['sswn'] = sswn
        self['dfbn'] = dfbn
        self['dfwn'] = dfwn
        self['msbn'] = ssbn/dfbn
        self['mswn'] = sswn/dfwn

        o_f, o_prob, o_ns, o_means, o_vars, o_ssbn, o_sswn, o_dfbn, o_dfwn = \
           stats.lF_oneway(stats.obrientransform(list_of_lists))

        self['o_f'] = o_f
        self['o_p'] = o_prob
        self['o_ns'] = o_ns
        self['o_mus'] = o_means
        self['o_vars'] = o_vars
        self['o_ssbn'] = o_ssbn
        self['o_sswn'] = o_sswn
        self['o_dfbn'] = o_dfbn
        self['o_dfwn'] = o_dfwn
        self['o_msbn'] = o_ssbn/o_dfbn
        self['o_mswn'] = o_sswn/o_dfwn

        if posthoc.lower() == 'tukey':
            self._tukey()

        elif posthoc.lower() == 'snk':
            self._snk()

    def _tukey(self):
        from qsturng import qsturng, psturng
        # http://www.utdallas.edu/~herve/abdi-NewmanKeuls2010-pretty.pdf
        # put means into a dict
        d = dict([(k,v) for k,v in zip(self.conditions_list, self['mus'])])

        # calculate the number of comparisons
        s = sum(range(len(d)))

        # calculate critical studentized range q statistic
        k = len(d)
        df = sum(self['ns']) - k
        q_crit10 = qsturng(.9, k, df)
        q_crit05 = qsturng(.95, k, df)
        q_crit01 = qsturng(.99, k, df)

        # run correlations
        multtest = {}

        for x in sorted(self.conditions_list):
            for y in sorted(self.conditions_list):
                if not multtest.has_key((y,x)):
                    abs_diff = abs(d[x]-d[y])
                    q = abs_diff / math.sqrt(self['mswn']*(1./s))
                    sig = 'ns'
                    if  q > q_crit10:
                        sig = '+'
                    if q > q_crit05:
                        sig = '*'
                    if q > q_crit01:
                        sig += '*'
                    multtest[(x,y)] = dict(q=q,
                                           sig=sig,
                                           abs_diff=abs(d[x]-d[y]),
                                           q_crit10=q_crit10,
                                           q_crit05=q_crit05,
                                           q_crit01=q_crit01,
                                           q_k=k,
                                           q_df=df)

        self.multtest = multtest

    def _snk(self):
        from qsturng import qsturng, psturng
        # http://www.utdallas.edu/~herve/abdi-NewmanKeuls2010-pretty.pdf
        # put means into a dict
        d = dict([(k,v) for k,v in zip(self.conditions_list, self['mus'])])

        # calculate the number of comparisons
        s = sum(range(len(d)))

        # figure out differences between pairs
        L = {}
        for x in sorted(self.conditions_list):
            for y in sorted(self.conditions_list):
                if not L.has_key((y,x)):
                    L[(x,y)] = abs(d[x]-d[y])


        # calculate critical studentized range q statistic
        k = len(d)
        df = sum(self['ns']) - k

        multtest = {}
        for i,(pair,abs_diff) in enumerate(sorted(list(L.items),
                                           key=lambda t: t[1],
                                           reverse=True)):
            q = abs_diff / math.sqrt(self['mswn']*(1./s))
            q_crit10 = qsturng(.9, k, df)
            q_crit05 = qsturng(.95, k, df)
            q_crit01 = qsturng(.99, k, df)

            sig = 'ns'
            if  q > q_crit10:
                sig = '+'
            if q > q_crit05:
                sig = '*'
            if q > q_crit01:
                sig += '*'
            multtest[(x,y)] = dict(q=q,
                                   sig=sig,
                                   abs_diff=abs(d[x]-d[y]),
                                   q_crit10=q_crit10,
                                   q_crit05=q_crit05,
                                   q_crit01=q_crit01,
                                   q_k=k,
                                   q_df=df)

            k -= 1


        self.multtest = multtest

    def __str__(self):

        if self == {}:
            return '(no data in object)'

        tt_s = TextTable(max_width=0)
        tt_s.set_cols_dtype(['t', 'a', 'a', 'a', 'a'])
        tt_s.set_cols_align(['l', 'r', 'r', 'r', 'r'])
        tt_s.set_deco(TextTable.HEADER)

        tt_s.header( ['Groups','Count','Sum', 'Average','Variance'])
        for g, c, a, v in zip(self.conditions_list,
                              self['ns'],
                              self['mus'],
                              self['vars']):
            tt_s.add_row([g, c, c * a, a, v])

        tt_o = TextTable(max_width=0)
        tt_o.set_cols_dtype(['t', 'a', 'a', 'a', 'a', 'a'])
        tt_o.set_cols_align(['l', 'r', 'r', 'r', 'r', 'r'])
        tt_o.set_deco(TextTable.HEADER | TextTable.FOOTER)

        tt_o.header( ['Source of Variation','SS','df','MS','F','P-value'])
        tt_o.add_row(['Treatments',self['o_ssbn'],self['o_dfbn'],
                                   self['o_msbn'],self['o_f'],self['o_p']])
        tt_o.add_row(['Error', self['o_sswn'],self['o_dfwn'],
                               self['o_mswn'],' ', ''])
        tt_o.footer( ['Total',self['o_ssbn']+self['o_sswn'],
                              self['o_dfbn']+self['o_dfwn'],' ',' ',' '])

        tt_a = TextTable(max_width=0)
        tt_a.set_cols_dtype(['t', 'a', 'a', 'a', 'a', 'a'])
        tt_a.set_cols_align(['l', 'r', 'r', 'r', 'r', 'r'])
        tt_a.set_deco(TextTable.HEADER | TextTable.FOOTER)

        tt_a.header( ['Source of Variation','SS','df','MS','F','P-value'])
        tt_a.add_row(['Treatments',self['ssbn'],self['dfbn'],
                                   self['msbn'],self['f'],self['p']])
        tt_a.add_row(['Error', self['sswn'],self['dfwn'],
                               self['mswn'],' ', ''])
        tt_a.footer( ['Total',self['ssbn']+self['sswn'],
                              self['dfbn']+self['dfwn'],' ',' ',' '])

        posthoc = ''
        if self.posthoc.lower() == 'tukey' and self.multtest != None:
            tt_m = TextTable(max_width=0)
            tt_m.set_cols_dtype(['t'] + ['a']*len(self.conditions_list))
            tt_m.set_cols_align(['l'] + ['l']*len(self.conditions_list))
            tt_m.set_deco(TextTable.HEADER | TextTable.FOOTER)
            tt_m.header([''] + sorted(self.conditions_list))

            for a in sorted(self.conditions_list):
                rline = [a]
                for b in sorted(self.conditions_list):
                    if a == b:
                        rline.append('0')
                    elif self.multtest.has_key((a,b)):
                        q = self.multtest[(a,b)]['q']
                        sig = self.multtest[(a,b)]['sig']
                        rline.append('%s %s'%(_str(q), sig))
                    else:
                        rline.append(' ')

                tt_m.add_row(rline)
            tt_m.footer(['']*(len(self.conditions_list) + 1))
            q_crit10 = self.multtest[(a,b)]['q_crit10']
            q_crit05 = self.multtest[(a,b)]['q_crit05']
            q_crit01 = self.multtest[(a,b)]['q_crit01']
            k = self.multtest[(a,b)]['q_k']
            df = self.multtest[(a,b)]['q_df']

            posthoc = 'POSTHOC MULTIPLE COMPARISONS\n\n'
            posthoc += 'Tukey HSD: Table of q-statistics\n'
            posthoc += tt_m.draw()
            posthoc += '\n  + p < .10 (q-critical[%i, %i] = %s)'%(k, df, q_crit10)
            posthoc += '\n  * p < .05 (q-critical[%i, %i] = %s)'%(k, df, q_crit05)
            posthoc += '\n ** p < .01 (q-critical[%i, %i] = %s)'%(k, df, q_crit01)

        return 'Anova: Single Factor on %s\n\n'%self.val + \
               'SUMMARY\n%s\n\n'%tt_s.draw() + \
               "O'BRIEN TEST FOR HOMOGENEITY OF VARIANCE\n%s\n\n"%tt_o.draw() + \
               'ANOVA\n%s\n\n'%tt_a.draw() + \
               posthoc

    def __repr__(self):
        if self == {}:
            return 'Anova1way()'

        s = []
        for k, v in self.items():
            s.append("('%s', %s)"%(k, repr(v)))
        args = '[' + ', '.join(s) + ']'

        kwds = []
        if self.val != 'Measure':
            kwds.append(', val="%s"'%self.val)

        if self.posthoc != 'tukey':
            kwds.append(', posthoc="%s"'%self.posthoc)

        if self.multtest != None:
            kwds.append(', multtest=%s'%repr(self.multtest))

        if self.factor != 'Factor':
            kwds.append(', factor="%s"'%self.factor)

        if self.conditions_list != []:
            kwds.append(', conditions_list=%s'%repr(self.conditions_list))

        if self.alpha != 0.05:
            kwds.append(', alpha=%s'%str(self.alpha))

        kwds= ''.join(kwds)

        return 'Anova1way(%s%s)'%(args,kwds)

class Correlation(OrderedDict):
    """bivariate correlation matrix"""
    def __init__(self, *args, **kwds):
        if len(args) > 1:
            raise Exception('expecting only 1 argument')

        if kwds.has_key('conditions_list'):
            self.conditions_list = kwds['conditions_list']
        else:
            self.conditions_list = []

        if kwds.has_key('coefficient'):
            self.coefficient = kwds['coefficient']
        else:
            self.coefficient = 'pearson'

        if kwds.has_key('alpha'):
            self.alpha = kwds['alpha']
        else:
            self.alpha = 0.05

        if kwds.has_key('N'):
            self.N = kwds['N']
        else:
            self.N = 0

        if len(args) == 1:
            super(Correlation, self).__init__(args[0])
        else:
            super(Correlation, self).__init__()

    def run(self, list_of_lists, conditions_list=None,
            coefficient='pearson', alpha=0.05):
        """

        """

        # check list_of_lists
        if len(list_of_lists) < 2:
            raise Exception('expecting 2 or more items in variables list')

        lengths = [len(L) for L in list_of_lists]

        if not all(L-lengths[0]+1 for L in lengths):
            raise Exception('lists must be of equal length')

        # check coefficient
        if coefficient == 'pearson':
            func = stats.pearsonr
        elif coefficient == 'spearman':
            func = stats.spearmanr
        elif coefficient == 'pointbiserial':
            func = stats.pointbiserialr
        elif coefficient == 'kendalltau':
            func = stats.kendalltau
        else:
            raise Exception('invalid coefficient parameter')

        self.coefficient = coefficient

        # build or check conditions list
        if conditions_list == None:
            self.conditions_list = []
            abc = lambda i : 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'\
                             [i%26]*(int(math.floor(i/26))+1)
            for i in _xrange(len(list_of_lists)):
                self.conditions_list.append(abc(i))
        else:
            self.conditions_list = conditions_list

        if len(list_of_lists) != len(self.conditions_list):
            raise Exception('list_of_lists and conditions_list '
                            'must be of equal length')

        # put data into a dict
        d=dict([(k,v) for k,v in zip(self.conditions_list, list_of_lists)])

        # run correlations
        for x,y in _xunique_combinations(self.conditions_list, 2):
            r, prob = func(d[x],d[y])
            self[(x,y)] = dict(r=r, p=prob)

        self.alpha = alpha
        self.N = lengths[0]

        self.lm_significance_testing()

    def lm_significance_testing(self):
        """
        Performs Larzelere and Mulaik Significance Testing
        on the paired correlations in self.

        The testing follows a stepdown procedure similiar
        to the Holm for multiple comparisons.
        The absolute r values are are arranged in decreasing
        order and the significant alpha level is adjusted
        according to alpha/(k-i+1) where k is the total
        number of tests and i the current pair.
        """

        # perform post_hoc analysis
        L = [(key, abs(self[key]['r'])) for key in self]
        k = len(self)
        self.lm = []
        for i,(pair,r) in enumerate(sorted(
                              L, key=lambda t: t[1], reverse=True)):
            adj_alpha = self.alpha / (k - (i + 1) + 1)
            self.lm.append([pair, i+1, r, self[pair]['p'], adj_alpha])

    def __str__(self):

        if self == {}:
            return '(no data in object)'

        tt = TextTable(max_width=0)
        tt.set_cols_dtype(['t', 't'] + ['a']*len(self.conditions_list))
        tt.set_cols_align(['l', 'l'] + ['r']*len(self.conditions_list))
        tt.set_deco(TextTable.HEADER | TextTable.HLINES)
        tt.header(['',''] + sorted(self.conditions_list))

        for a in sorted(self.conditions_list):
            rline = [a, self.coefficient]
            pline = ['', 'Sig (2-tailed)']
            nline = ['', 'N']
            for b in sorted(self.conditions_list):
                if a == b:
                    rline.append('1')
                    pline.append(' .')
                    nline.append(self.N)
                elif self.has_key((a,b)):
                    rline.append(self[(a,b)]['r'])
                    pline.append(self[(a,b)]['p'])
                    nline.append(self.N)
                elif self.has_key((b,a)):
                    rline.append(self[(b,a)]['r'])
                    pline.append(self[(b,a)]['p'])
                    nline.append(self.N)

            tt.add_row(['%s\n%s\n%s'%(_str(r),_str(p),_str(n))
                        for r,p,n in zip(rline,pline,nline)])

        tt_lm = TextTable(max_width=0)
        tt_lm.set_cols_dtype(['t', 'i', 'f', 'a', 'a', 't'])
        tt_lm.set_cols_align(['l', 'r', 'r', 'r', 'r', 'l'])
        tt_lm.set_deco(TextTable.HEADER)
        tt_lm.header(['Pair', 'i', 'Correlation', 'P', 'alpha/(k-i+1)', 'Sig.'])

        for row in self.lm:
            x, y = row[0]
            tt_lm.add_row(['%s vs. %s'%(x, y)] +
                          row[1:] +
                          ([''],['**'])[row[3] < row[4]])

        return 'Bivariate Correlations\n\n' + tt.draw() + \
               '\n\nLarzelere and Mulaik Significance Testing\n\n' + tt_lm.draw()

    def __repr__(self):
        if self == {}:
            return 'Correlation()'

        s = []
        for k, v in self.items():
            s.append("(%s, %s)"%(repr(k), repr(v)))
        args = '[' + ', '.join(s) + ']'

        kwds = []

        if self.conditions_list != []:
            kwds.append(', conditions_list=%s'%repr(self.conditions_list))

        if self.coefficient != 'pearson':
            kwds.append(", coefficient='%s'"%str(self.coefficient))

        if self.alpha != 0.05:
            kwds.append(', alpha=%s'%str(self.alpha))

        if self.N != 0:
            kwds.append(', N=%i'%self.N)

        kwds= ''.join(kwds)

        return 'Correlation(%s%s)'%(args,kwds)

class ChiSquare1way(OrderedDict):
    """1-way Chi-Square Test"""
    def __init__(self, *args, **kwds):
        if len(args) > 1:
            raise Exception('expecting only 1 argument')

        if kwds.has_key('measure'):
            self.measure = kwds['measure']
        else:
            self.measure = 'Measure'

        if kwds.has_key('conditions_list'):
            self.conditions_list = kwds['conditions_list']
        else:
            self.conditions_list = []

        if kwds.has_key('alpha'):
            self.alpha = kwds['alpha']
        else:
            self.alpha = 0.05

        if len(args) == 1:
            super(ChiSquare1way, self).__init__(args[0])
        else:
            super(ChiSquare1way, self).__init__()

    def run(self, observed, expected=None, conditions_list=None,
            measure='Measure', alpha=0.05):
        """

        """
        chisq, prob, df, expected = stats.lchisquare(observed, expected)
        try:
            lnchisq, lnprob, lndf, lnexpected = \
                     stats.llnchisquare(observed, expected)
        except:
            lnchisq, lnprob, lndf, lnexpected = 'nan','nan','nan','nan'

        self.observed = observed
        self.expected = expected
        self.alpha = alpha

        if conditions_list == None:
            self.conditions_list = []
            abc = lambda i : 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'\
                             [i%26]*(int(math.floor(i/26))+1)
            for i in _xrange(len(observed)):
                self.conditions_list.append(abc(i))
        else:
            self.conditions_list = conditions_list

        self['chisq'] = chisq
        self['p'] = prob
        self['df'] = df
        self['lnchisq'] = lnchisq
        self['lnp'] = lnprob
        self['lndf'] = lndf
        self.observed = observed
        self.expected = expected

    def __str__(self):

        if self == {}:
            return '(no data in object)'

        tt_s = TextTable(max_width=0)
        tt_s.set_cols_dtype(['t'] + ['a']*len(self.observed))
        tt_s.set_cols_align(['l'] + ['r']*len(self.observed))
        tt_s.set_deco(TextTable.HEADER)

        tt_s.header( [' '] + self.conditions_list)

        tt_s.add_row(['Observed'] + self.observed)
        tt_s.add_row(['Expected'] + self.expected)

        tt_a = TextTable(max_width=0)
        tt_a.set_cols_dtype(['t', 'a', 'a', 'a'])
        tt_a.set_cols_align(['l', 'r', 'r', 'r'])
        tt_a.set_deco(TextTable.HEADER)

        tt_a.header([' ', 'Value', 'df', 'P'])
        tt_a.add_row(['Pearson Chi-Square',
                      self['chisq'], self['df'], self['p']])
        tt_a.add_row(['Likelihood Ratio',
                      self['lnchisq'], self['lndf'], self['lnp']])
        tt_a.add_row(['Observations', sum(self.observed),'',''])

        return 'Chi-Square: Single Factor\n\n' + \
               'SUMMARY\n%s\n\n'%tt_s.draw() + \
               'CHI-SQUARE TESTS\n%s'%tt_a.draw()

    def __repr__(self):
        if self == {}:
            return 'ChiSquare1way()'

        s = []
        for k, v in self.items():
            s.append("('%s', %s)"%(k, repr(v)))
        args = '[' + ', '.join(s) + ']'

        kwds = []
        if self.measure != 'Measure':
            kwds.append(', val="%s"'%self.measure)

        if self.conditions_list != []:
            kwds.append(', conditions_list=%s'%repr(self.conditions_list))

        if self.alpha != 0.05:
            kwds.append(', alpha=%s'%str(self.alpha))

        kwds= ''.join(kwds)

        return 'ChiSquare1way(%s%s)'%(args,kwds)


class ChiSquare2way(OrderedDict):
    def __init__(self, *args, **kwds):
        if len(args) > 1:
            raise Exception('expecting only 1 argument')

        if kwds.has_key('counter'):
            self.counter = kwds['counter']
        else:
            self.counter = None

        if kwds.has_key('row_counter'):
            self.row_counter = kwds['row_counter']
        else:
            self.row_counter = None

        if kwds.has_key('col_counter'):
            self.col_counter = kwds['col_counter']
        else:
            self.col_counter = None

        if kwds.has_key('N_r'):
            self.N_r = kwds['N_r']
        else:
            self.N_r = None

        if kwds.has_key('N_c'):
            self.N_c = kwds['N_c']
        else:
            self.N_c = None

        if kwds.has_key('alpha'):
            self.alpha = kwds['alpha']
        else:
            self.alpha = 0.05

        if len(args) == 1:
            super(ChiSquare2way, self).__init__(args[0])
        else:
            super(ChiSquare2way, self).__init__()

    def run(self, row_factor, col_factor, alpha=0.05):
        """
        runs a 2-way chi square on the matched data in row_factor
        and col_factor.
        """

        if len(row_factor) != len(col_factor):
            raise Exception('row_factor and col_factor must be equal lengths')

        counter = Counter()
        row_counter= Counter()
        col_counter= Counter()
        for r,c in zip(row_factor, col_factor):
            counter[(r,c)] += 1.
            row_counter[r] += 1.
            col_counter[c] += 1.

        N = float(sum(counter.values()))
        observed = []
        expected = []
        for r in sorted(row_counter):
            observed.append([])
            expected.append([])
            for c in sorted(col_counter):
                observed[-1].append(counter[(r,c)])
                expected[-1].append((row_counter[r]*col_counter[c])/N)

        N_r, N_c = len(row_counter), len(col_counter)
        df = (N_r - 1) * (N_c - 1)

        chisq = sum((o-e)**2/e for o,e in
                    zip(_flatten(observed),_flatten(expected)))
        prob = stats.chisqprob(chisq, df)

        try:
            lnchisq = 2.*sum(o*math.log(o/e) for o,e in
                             zip(_flatten(observed),_flatten(expected)))
            lnprob = stats.chisqprob(lnchisq, df)
        except:
            lnchisq = 'nan'
            lnprob = 'nan'

        if N_r == N_c == 2:
            ccchisq = sum((abs(o-e)-0.5)**2/e for o,e in
                          zip(_flatten(observed),_flatten(expected)))
            ccprob = stats.chisqprob(ccchisq, df)
        else:
            ccchisq = None
            ccprob = None


        def rprob(r,df):
            TINY = 1e-30
            t = r*math.sqrt(df/((1.0-r+TINY)*(1.0+r+TINY)))
            return stats.betai(0.5*df,0.5,df/(df+t*t))

        k = min([N_r, N_c])
        cramerV = math.sqrt(chisq/(N*(k-1)))
        cramerV_prob = rprob(cramerV, N-2)
        C = math.sqrt(chisq/(chisq + N))
        C_prob = rprob(C, N-2)

        self['chisq'] = chisq
        self['p'] = prob
        self['df'] = df
        self['lnchisq'] = lnchisq
        self['lnp'] = lnprob
        self['ccchisq'] = ccchisq
        self['ccp'] = ccprob
        self['N'] = N
        self['C'] = C
        self['CramerV'] = cramerV
        self['CramerV_prob'] = cramerV_prob
        self['C'] = C
        self['C_prob'] = C_prob

        self.counter = counter
        self.row_counter = row_counter
        self.col_counter = col_counter
        self.N_r = N_r
        self.N_c = N_c

    def __str__(self):
        """Returns human readable string representaition of Marginals"""

        if self == {}:
            return '(no data in object)'

        tt_s = TextTable(max_width=0)
        tt_s.set_cols_dtype(['t'] + ['a']*(self.N_c + 1))
        tt_s.set_cols_align(['l'] + ['r']*(self.N_c + 1))
        tt_s.set_deco(TextTable.HEADER | TextTable.FOOTER)
        tt_s.header( [' '] + sorted(self.col_counter) + ['Total'])

        for r, rv in sorted(self.row_counter.items()):
            line = [r]
            for c, cv in sorted(self.col_counter.items()):
                o = self.counter[(r,c)]
                e = (rv*cv)/self['N']
                line.append('%s\n(%s)'%(_str(o), _str(e)))
            line.append(rv)
            tt_s.add_row(line)
        tt_s.footer(['Total'] +
                    [v for c,v in sorted(self.col_counter.items())] +
                    [self['N']])

        tt_sym = TextTable(max_width=0)
        tt_sym.set_cols_dtype(['t', 'a', 'a'])
        tt_sym.set_cols_align(['l', 'r', 'r'])
        tt_sym.set_deco(TextTable.HEADER)
        tt_sym.header(['','Value','Approx.\nSig.'])
        tt_sym.add_row(["Cramer's V", self['CramerV'], self['CramerV_prob']])
        tt_sym.add_row(["Contingency Coefficient", self['C'], self['C_prob']])
        tt_sym.add_row(["N of Valid Cases", self['N'], ''])


        tt_a = TextTable(max_width=0)
        tt_a.set_cols_dtype(['t', 'a', 'a', 'a'])
        tt_a.set_cols_align(['l', 'r', 'r', 'r'])
        tt_a.set_deco(TextTable.HEADER)
        tt_a.header([' ', 'Value', 'df', 'P'])
        tt_a.add_row(['Pearson Chi-Square',
                      self['chisq'], self['df'], self['p']])
        if self['ccchisq'] != None:
            tt_a.add_row(['Continuity Correction',
                          self['ccchisq'], self['df'], self['ccp']])
        tt_a.add_row(['Likelihood Ratio',
                      self['lnchisq'], self['df'], self['lnp']])
        tt_a.add_row(["N of Valid Cases", self['N'], '', ''])

        return 'Chi-Square: two Factor\n\n' + \
               'SUMMARY\n%s\n\n'%tt_s.draw() + \
               'SYMMETRIC MEASURES\n%s\n\n'%tt_sym.draw() + \
               'CHI-SQUARE TESTS\n%s'%tt_a.draw()


    def __repr__(self):
        if self == {}:
            return 'ChiSquare2way()'

        s = []
        for k, v in self.items():
            s.append("('%s', %s)"%(k, repr(v)))
        args = '[' + ', '.join(s) + ']'

        kwds = []
        if self.counter != None:
            kwds.append(', counter=%s'%repr(self.counter))

        if self.row_counter != None:
            kwds.append(', row_counter=%s'%repr(self.row_counter))

        if self.col_counter != None:
            kwds.append(', col_counter=%s'%repr(self.col_counter))

        if self.N_r != None:
            kwds.append(', N_r=%i'%self.N_r)

        if self.N_c != None:
            kwds.append(', N_c=%i'%self.N_c)

        if self.alpha != 0.05:
            kwds.append(', alpha=%s'%str(self.alpha))

        return 'ChiSquare2way(%s%s)'%(args, ''.join(kwds))

class Descriptives(OrderedDict):
    def __init__(self, *args, **kwds):
        if len(args) > 1:
            raise Exception('expecting only 1 argument')

        if kwds.has_key('cname'):
            self.cname = kwds['cname']
        else:
            self.cname = None

        if len(args) == 1:
            super(Descriptives, self).__init__(args[0])
        else:
            super(Descriptives, self).__init__()

    def run(self, V, cname=None):
        """
        generates and stores descriptive statistics for the
        numerical data in V
        """
        try:
            V = sorted(_flatten(list(copy(V))))
        except:
            raise TypeError('V must be a list-like object')

        if cname == None:
            self.cname = ''
        else:
            self.cname = cname

        N = float(len(V))

        self['count'] = N
        self['mean'] = sum(V) / N
        self['var'] = sum([(self['mean']-v)**2 for v in V]) / (N - 1)
        self['stdev']= math.sqrt(self['var'])
        self['sem'] = self['stdev'] / math.sqrt(N)
        self['rms'] = math.sqrt(sum([v**2 for v in V]) / N)
        self['min'] = min(V)
        self['max'] = max(V)
        self['range'] = self['max'] - self['min']
        self['median'] = V[int(N/2)]
        if self['count'] % 2 == 0:
            self['median'] += V[int(N/2)-1]
            self['median'] /= 2.
        self['mode'] = Counter(V).most_common()[0][0]
        self['95ci_lower'] = self['mean'] - 1.96*self['sem']
        self['95ci_upper'] = self['mean'] + 1.96*self['sem']

    def __str__(self):

        if self == {}:
            return '(no data in object)'

        tt = TextTable(48)
        tt.set_cols_dtype(['t', 'f'])
        tt.set_cols_align(['l', 'r'])
        for (k, v) in self.items():
            tt.add_row([' %s'%k, v])
        tt.set_deco(TextTable.HEADER)

        return ''.join(['Descriptive Statistics\n  ',
                         self.cname,
                         '\n==========================\n',
                         tt.draw()])

    def __repr__(self):
        if self == {}:
            return 'Descriptives()'

        s = []
        for k, v in self.items():
            s.append("('%s', %s)"%(k, repr(v)))
        args = '[' + ', '.join(s) + ']'

        kwds = ''
        if self.cname != None:
            kwds = ", cname='%s'"%self.cname


        return 'Descriptives(%s%s)'%(args, kwds)

class Histogram(OrderedDict):
    def __init__(self, *args, **kwds):
        if len(args) > 1:
            raise Exception('expecting only 1 argument')

        if kwds.has_key('cname'):
            self.cname = kwds['cname']
        else:
            self.cname = None

        if kwds.has_key('bins'):
            self.bins = kwds['bins']
        else:
            self.bins = 10.

        if kwds.has_key('range'):
            self.range = kwds['range']
        else:
            self.range = None

        if kwds.has_key('density'):
            self.density = kwds['density']
        else:
            self.density = False

        if kwds.has_key('cumulative'):
            self.cumulative = kwds['cumulative']
        else:
            self.cumulative = False

        if len(args) == 1:
            super(Histogram, self).__init__(args[0])
        else:
            super(Histogram, self).__init__()

    def run(self, V, cname=None, bins=10,
                 range=None, density=False, cumulative=False):
        """
        generates and stores histogram data for numerical data in V
        """

        super(Histogram, self).__init__()

        try:
            V = sorted(_flatten(list(V)))
        except:
            raise TypeError('V must be a list-like object')

        if len(V) == 0:
            raise Exception('V has zero length')

        if cname == None:
            self.cname = ''
        else:
            self.cname = cname

        values, bin_edges = pystaggrelite3.hist(V, bins=bins,
                   range=range, density=density, cumulative=cumulative)

        self['values'] = values
        self['bin_edges'] = bin_edges

        if cname == None:
            self.cname = ''
        else:
            self.cname = cname

        self.bins = bins
        self.range = range
        self.density = density
        self.cumulative = cumulative

    def __str__(self):

        tt = TextTable(48)
        tt.set_cols_dtype(['f', 'f'])
        tt.set_cols_align(['r', 'r'])
        for (b, v) in zip(self['bin_edges'],self['values']+['']):
            tt.add_row([b, v])
        tt.set_deco(TextTable.HEADER)
        tt.header(['Bins','Values'])

        return ''.join([('','Cumulative ')[self.cumulative],
                        ('','Density ')[self.density],
                        'Histogram for ', self.cname, '\n',
                        tt.draw()])

    def __repr__(self):
        if self == {}:
            return 'Histogram()'

        s = []
        for k, v in self.items():
            s.append("('%s', %s)"%(k, repr(v)))
        args = '[' + ', '.join(s) + ']'

        kwds = []
        if self.cname != None:
            kwds.append(", cname='%s'"%self.cname)

        if self.bins != 10:
            kwds.append(', bins=%s'%self.bins)

        if self.range != None:
            kwds.append(', range=%s'%repr(range))

        if self.density != False:
            kwds.append(', density=%s'%density)

        if self.cumulative != False:
            kwds.append(', cumulative=%s'%cumulative)

        kwds= ''.join(kwds)

        return 'Histogram(%s%s)'%(args, kwds)

class Marginals(OrderedDict):
    def __init__(self, *args, **kwds):
        if len(args) > 1:
            raise Exception('expecting only 1 argument')

        if kwds.has_key('val'):
            self.val = kwds['val']
        else:
            self.val = None

        if kwds.has_key('factors'):
            self.factors = kwds['factors']
        else:
            self.factors = None

        if kwds.has_key('where'):
            self.where = kwds['where']
        else:
            self.where = []

        if len(args) == 1:
            super(Marginals, self).__init__(args[0])
        else:
            super(Marginals, self).__init__()

    def run(self, df, val, factors, where=None):
        """
        generates and stores marginal data from the DataFrame df
        and column labels in factors.
        """

        if where == None:
            where = []

        if df == {}:
            raise Exception('Table must have data to calculate marginals')

        # check to see if data columns have equal lengths
        if not df._are_col_lengths_equal():
            raise Exception('columns have unequal lengths')

        for cname in [val]+factors:
            if cname not in df.names():
                raise KeyError(cname)

        # check for duplicate names
        dup = Counter([val] + factors)
        del dup[None]

        if not all([count == 1 for count in dup.values()]):
            raise Exception('duplicate labels specified as plot parameters')

        if not hasattr(factors, '__iter__'):
            raise TypeError( "'%s' object is not iterable"
                         % type(cols).__name__)

        dmu = df.pivot(val, rows=factors, where=where,
                         aggregate='avg', flatten=True)


        dN = df.pivot(val, rows=factors, where=where,
                        aggregate='count', flatten=True)

        dsem = df.pivot(val, rows=factors, where=where,
                              aggregate='sem', flatten=True)

        # build factors from r_list
        factorials = OrderedDict()
        for i, r in enumerate(dN.rnames):
            if i == 0:
                for c in r:
                    factorials[c[0]] = []

            for j, c in enumerate(r):
                factorials[c[0]].append(c[1])

        dlower = copy(dN)
        dupper = copy(dN)
        for i,(mu, sem) in enumerate(zip(dmu, dsem)):
            dlower[i] = mu - 1.96 * sem
            dupper[i] = mu + 1.96 * sem

        super(Marginals, self).__init__()

        self['factorials'] = factorials
        self['dmu'] = dmu
        self['dN'] = dN
        self['dsem'] = dsem
        self['dlower'] = dlower
        self['dupper'] = dupper

        self.val = val
        self.factors = factors
        self.where = where

    def __str__(self):
        """Returns human readable string representaition of Marginals"""

        M = []
        for v in self['factorials'].values():
            M.append(v)

        M.append(self['dmu'])
        M.append(self['dN'])
        M.append(self['dsem'])
        M.append(self['dlower'])
        M.append(self['dupper'])
        M = zip(*M) # transpose

        # figure out the width needed by the condition labels so we can
        # set the width of the table
        flength = sum([max([len(v) for c in v])
                       for v in self['factorials'].values()])
        flength += len(self['factorials']) * 2

        # build the header
        header = self.factors + 'Mean;Count;Std.\nError;'\
                           '95% CI\nlower;95% CI\nupper'.split(';')

        dtypes = ['t'] * len(self.factors) + ['f', 'i', 'f', 'f', 'f']
        aligns = ['l'] * len(self.factors) + ['r', 'l', 'r', 'r', 'r']

        # initialize the texttable and add stuff
        tt = TextTable(max_width=10000000)
        tt.set_cols_dtype(dtypes)
        tt.set_cols_align(aligns)
        tt.add_rows(M, header=False)
        tt.header(header)
        tt.set_deco(TextTable.HEADER)

        # output the table
        return tt.draw()

    def __repr__(self):
        if self == {}:
            return 'Marginals()'

        s = []
        for k, v in self.items():
            s.append("('%s', %s)"%(k, repr(v)))
        args = '[' + ', '.join(s) + ']'

        kwds = []
        if self.val != None:
            kwds.append(", val='%s'"%self.val)

        if self.factors != None:
            kwds.append(", factors=%s"%self.factors)

        if self.where != []:
            if isinstance(self.where, _strobj):
                kwds.append(", where='%s'"%self.where)
            else:
                kwds.append(", where=%s"%self.where)
        kwds= ''.join(kwds)

        return 'Marginals(%s%s)'%(args, kwds)

