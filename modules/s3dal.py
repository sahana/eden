# -*- coding: utf-8 -*-

""" S3 pyDAL Imports (with fallbacks for older DAL versions)

    @copyright: 2015-2019 (c) Sahana Software Foundation
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

    @status: fixed for Py3
"""

__all__ = ("Expression",
           "Field",
           "Query",
           "Row",
           "Rows",
           "SQLCustomType",
           "Table",
           "original_tablename",
           )

try:
    from pydal import Field, SQLCustomType
    from pydal.contrib import portalocker
    from pydal.objects import Expression, Query, Row, Rows, Table, VirtualCommand
except ImportError:
    # older web2py
    try:
        from gluon import portalocker
        from gluon.dal import Field, SQLCustomType
        from gluon.dal.objects import Expression, Query, Row, Rows, Table, VirtualCommand
    except ImportError:
        # even older web2py
        from gluon import portalocker
        from gluon.dal import Field, SQLCustomType
        from gluon.dal import Expression, Query, Row, Rows, Table, VirtualCommand

from gluon import current

# =============================================================================
class S3DAL(object):
    """ Adapter class for backwards-incompatible PyDAL changes """

    def __init__(self):

        adapter = current.db._adapter

        try:
            dialect = adapter.dialect

        except AttributeError:
            # PyDAL <= 16.03
            self.INVERT = adapter.INVERT
            self.COMMA = adapter.COMMA
            self.OR = adapter.OR
            self.CONTAINS = adapter.CONTAINS
            self.AGGREGATE = adapter.AGGREGATE

        else:
            # current PyDAL
            self.INVERT = dialect.invert
            self.COMMA = dialect.comma
            self.OR = dialect._or
            self.CONTAINS = dialect.contains
            self.AGGREGATE = dialect.aggregate

    # -------------------------------------------------------------------------
    dalname = staticmethod(lambda table: table._dalname)

    @classmethod
    def original_tablename(cls, table):
        """
            Get the original name of an aliased table, with fallback
            cascade for PyDAL < 17.01

            @param table: the Table
        """

        try:
            return cls.dalname(table)
        except AttributeError:
            if hasattr(table, "_ot"):
                dalname = lambda table: \
                          table._ot if table._ot else table._tablename
                cls.dalname = staticmethod(dalname)
                return dalname(table)
            else:
                raise

# =============================================================================
original_tablename = S3DAL.original_tablename

# END =========================================================================
