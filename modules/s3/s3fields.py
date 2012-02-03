# -*- coding: utf-8 -*-

"""
    S3 Extensions for gluon.dal.Field, reusable fields

    @requires: U{B{I{gluon}} <http://web2py.com>}

    @author: Dominic König <dominic[at]aidiq.com>

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

__all__ = ["QueryS3",
           "FieldS3",
           "S3ReusableField",
           "s3uuid",
           "s3_meta_uuid",
           "s3_meta_mci",
           "s3_uid",
           "s3_meta_deletion_status",
           "s3_meta_deletion_fk",
           "s3_deletion_status",
           "s3_meta_created_on",
           "s3_meta_modified_on",
           "s3_timestamp"]

import datetime

from gluon import current
from gluon.dal import Query, Field, SQLCustomType
from gluon.storage import Storage
from gluon.html import *
from gluon.validators import *

# =============================================================================

class QueryS3(Query):

    """
        S3 extensions of the gluon.sql.Query class

        If Server Side Pagination is on, the proper CAST is needed to match
        the string-typed id to lookup table id

        @author: sunneach
    """

    def __init__(self, left, op=None, right=None):

        if op <> "join_via":
            Query.__init__(self, left, op, right)
        else:
            self.sql = "CAST(TRIM(%s,"|") AS INTEGER)=%s" % (left, right)

# =============================================================================

class FieldS3(Field):

    """
        S3 extensions of the gluon.sql.Field clas

        If Server Side Pagination is on, the proper CAST is needed to
        match the lookup table id

        @author: sunneach
    """

    def __init__(self, fieldname,
                 type="string",
                 length=None,
                 default=None,
                 required=False,
                 requires="<default>",
                 ondelete="CASCADE",
                 notnull=False,
                 unique=False,
                 uploadfield=True,
                 widget=None,
                 label=None,
                 comment=None,
                 writable=True,
                 readable=True,
                 update=None,
                 authorize=None,
                 autodelete=False,
                 represent=None,
                 uploadfolder=None,
                 compute=None,
                 sortby=None):

        self.sortby = sortby

        Field.__init__(self,
                       fieldname,
                       type,
                       length,
                       default,
                       required,
                       requires,
                       ondelete,
                       notnull,
                       unique,
                       uploadfield,
                       widget,
                       label,
                       comment,
                       writable,
                       readable,
                       update,
                       authorize,
                       autodelete,
                       represent,
                       uploadfolder,
                       compute)

    def join_via(self, value):
        if self.type.find("reference") == 0:
            return Query(self, "=", value)
        else:
            return QueryS3(self, "join_via", value)

# =============================================================================

class S3ReusableField(object):

    """
        DRY Helper for reusable fields:

        This creates neither a Table nor a Field, but just
        an argument store. The field is created with the __call__
        method, which is faster than copying an existing field.

        @author: Dominic König
    """

    def __init__(self, name, type="string", **attr):

        self.name = name
        self.__type = type
        self.attr = Storage(attr)

    def __call__(self, name=None, **attr):

        if not name:
            name = self.name

        ia = Storage(self.attr)

        if attr:
            if not attr.get("empty", True):
                requires = ia.requires
                if requires:
                    if not isinstance(requires, (list, tuple)):
                        requires = [requires]
                    if requires:
                        r = requires[0]
                        if isinstance(r, IS_EMPTY_OR):
                            requires = r.other
                            ia.update(requires=requires)
            if "empty" in attr:
                del attr["empty"]
            ia.update(**attr)

        if "script" in ia:
            if ia.script:
                if ia.comment:
                    ia.comment = TAG[""](ia.comment, ia.script)
                else:
                    ia.comment = ia.script
            del ia["script"]

        if ia.sortby is not None:
            return FieldS3(name, self.__type, **ia)
        else:
            return Field(name, self.__type, **ia)

# =============================================================================
# Use URNs according to http://tools.ietf.org/html/rfc4122
def s3_uuid():
    import uuid
    return uuid.uuid4()

s3uuid = SQLCustomType(type = "string",
                       native = "VARCHAR(128)",
                       encoder = (lambda x: "'%s'" % (s3_uuid().urn
                                    if x == ""
                                    else str(x.encode("utf-8")).replace("'", "''"))),
                       decoder = (lambda x: x))

# =============================================================================
# Record identity meta-fields

# Universally unique identifier for a record
s3_meta_uuid = S3ReusableField("uuid",
                               type=s3uuid,
                               length=128,
                               notnull=True,
                               unique=True,
                               readable=False,
                               writable=False,
                               default="")

# Master-Copy-Index (for Sync)
s3_meta_mci = S3ReusableField("mci", "integer",
                              default=0,
                              readable=False,
                              writable=False)

def s3_uid():
    return (s3_meta_uuid(),
            s3_meta_mci())

# =============================================================================
# Record "soft"-deletion meta-fields

# "Deleted"-flag
s3_meta_deletion_status = S3ReusableField("deleted", "boolean",
                                          readable=False,
                                          writable=False,
                                          default=False)

# Parked foreign keys of a deleted record
# => to be restored upon "un"-delete
s3_meta_deletion_fk = S3ReusableField("deleted_fk", #"text",
                                      readable=False,
                                      writable=False)

def s3_deletion_status():
    return (s3_meta_deletion_status(),
            s3_meta_deletion_fk())

# -----------------------------------------------------------------------------
# Record timestamp meta-fields

s3_meta_created_on = S3ReusableField("created_on", "datetime",
                                     readable=False,
                                     writable=False,
                                     default=lambda: datetime.datetime.utcnow())

s3_meta_modified_on = S3ReusableField("modified_on", "datetime",
                                      readable=False,
                                      writable=False,
                                      default=lambda: datetime.datetime.utcnow(),
                                      update=lambda: datetime.datetime.utcnow())

def s3_timestamp():
    return (s3_meta_created_on(),
            s3_meta_modified_on())

# =============================================================================
