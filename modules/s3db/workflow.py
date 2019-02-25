# -*- coding: utf-8 -*-

"""
   S3 Workflow Engine Data Model

   @copyright: 2012-2019 (c) Sahana Software Foundation
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

__all__ = ["S3WorkflowStatusModel"]

from gluon import *
from gluon.storage import Storage
from ..s3 import *

# =============================================================================
class S3WorkflowStatusModel(S3Model):
    """ Model to store the workflow status of records """

    name = ["workflow_status",
            "workflow_entity",
           ]

    def model(self):

        auth = current.auth
        define_table = self.define_table
        db = current.db

        # ---------------------------------------------------------------------
        # Entities which can have a workflow status
        #
        # @note: the respective entity tables need to also define the
        #        super_link("workflow_id", "workflow_entity"), and have
        #        their super-entity configured like:
        #        s3db.configure(tablename, super_entity="workflow_entity")
        #
        we_types = Storage(project_task = T("Project Task"),
                          )

        tablename = "workflow_entity"
        s3db.super_entity(tablename, "workflow_id",
                          we_types,
                          )

        # Status as component
        self.add_components(tablename,
                            workflow_status="workflow_id",
                            )


        # ---------------------------------------------------------------------
        # Workflow Status
        # - as tuple (workflow name, status name)
        # - as component of workflow entities
        #
        tablename = "workflow_status"
        define_table(tablename,
                     super_link("workflow_id", "workflow_entity"),
                     Field("name", length=64, notnull=True,
                           requires = [IS_NOT_EMPTY(),
                                       IS_LENGTH(64),
                                       ],
                           ),
                     Field("status", length=64, notnull=True,
                           requires = [IS_NOT_EMPTY(),
                                       IS_LENGTH(64),
                                       ],
                           ),
                     *s3_meta_fields(),
                     )

        return Storage()

# END =========================================================================
