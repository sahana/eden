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

__all__ = ("S3HierarchyModel",
           "S3DashboardModel",
           )

from gluon import *
from ..s3 import *

# =============================================================================
class S3HierarchyModel(S3Model):
    """ Model for stored object hierarchies """

    names = ("s3_hierarchy",)

    def model(self):

        # ---------------------------------------------------------------------
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

# =============================================================================
class S3DashboardModel(S3Model):
    """ Model for stored dashboard configurations """

    names = ("s3_dashboard",)

    def model(self):

        define_table = self.define_table
        configure = self.configure

        # ---------------------------------------------------------------------
        # Stored Dashboard Configuration
        #
        tablename = "s3_dashboard"
        define_table(tablename,
                     Field("controller", length = 64,
                           requires = IS_NOT_EMPTY(),
                           ),
                     Field("function", length = 512,
                           requires = IS_NOT_EMPTY(),
                           ),
                     Field("layout",
                           default = S3DashboardConfig.DEFAULT_LAYOUT,
                           requires = IS_NOT_EMPTY(),
                           ),
                     Field("title",
                           ),
                     Field("widgets", "json",
                           requires = IS_JSONS3(),
                           ),
                     Field("active", "boolean",
                           default = True,
                           ),
                     *s3_meta_fields())

        configure(tablename,
                  onaccept = self.dashboard_onaccept,
                  )

        # ---------------------------------------------------------------------
        # Link Dashboard Config <=> Person Entity
        #
        # @todo

        # ---------------------------------------------------------------------
        # Return global names to s3.*
        #
        return {}

    # -------------------------------------------------------------------------
    def defaults(self):
        """ Safe defaults if module is disabled """

        return {}

    # -------------------------------------------------------------------------
    @staticmethod
    def dashboard_onaccept(form):
        """
            On-accept routine for dashboard configurations
                - make sure there is at most one active config for the same
                  controller/function
        """

        db = current.db

        try:
            record_id = form.vars.id
        except AttributeError:
            return

        table = current.s3db.s3_dashboard
        query = table.id == record_id

        row = db(query).select(table.id,
                               table.controller,
                               table.function,
                               table.active,
                               limitby = (0, 1),
                               ).first()
        if not row:
            return

        if row.active:
            # Deactivate all other configs for the same controller/function
            query = (table.controller == row.controller) & \
                    (table.function == row.function) & \
                    (table.id != row.id) & \
                    (table.active == True) & \
                    (table.deleted != True)
            db(query).update(active = False)

# END =========================================================================
