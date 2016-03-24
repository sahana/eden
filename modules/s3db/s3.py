# -*- coding: utf-8 -*-

""" S3 Framework Tables

    @copyright: 2009-2016 (c) Sahana Software Foundation
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

__all__ = ("S3HierarchyModel",)

from gluon import *
from ..s3 import *

# =============================================================================
class S3HierarchyModel(S3Model):
    """ Model for stored object hierarchies """

    names = ("s3_hierarchy",)

    def model(self):

        # -------------------------------------------------------------------------
        # Stored Object Hierarchy
        #
        tablename = "s3_hierarchy"
        self.define_table(tablename,
                          Field("tablename", length=64),
                          Field("dirty", "boolean",
                                default = False,
                                ),
                          Field("hierarchy", "json"),
                          *s3_timestamp())

        # ---------------------------------------------------------------------
        # Return global names to s3.*
        #
        return {}

    # -------------------------------------------------------------------------
    def defaults(self):
        """ Safe defaults if module is disabled """

        return {}


# END =========================================================================
