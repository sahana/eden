# -*- coding: utf-8 -*-

""" S3 pyDAL Imports (with fallbacks for older DAL versions)

    @copyright: 2015 (c) Sahana Software Foundation
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

__all__ = ("Expression",
           "Field",
           "Query",
           "Row",
           "Rows",
           "SQLCustomType",
           "Table",
           )

try:
    from pydal import Field, SQLCustomType
    from pydal.objects import Expression, Query, Row, Rows, Table
except ImportError:
    # older web2py
    try:
        from gluon.dal import Field, SQLCustomType
        from gluon.dal.objects import Expression, Query, Row, Rows, Table
    except ImportError:
        # even older web2py
        from gluon.dal import Field, SQLCustomType
        from gluon.dal import Expression, Query, Row, Rows, Table
