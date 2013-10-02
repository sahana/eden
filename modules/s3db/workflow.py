
"""
   This file is used to define the configration of the workflows
   for the workflow engine.
   
   @copyright: 2012-13 (c) Sahana Software Foundation
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

from gluon import *
from gluon.storage import Storage
from ..s3 import *

__all__ = ["S3WorkflowModel"]

class S3WorkflowModel(S3Model):

    name = ["workflow_status",
            "workflow_entity"]

    def model(self):

        auth = current.auth
        define_table = self.define_table
        db = current.db

        we_types = Storage(project_task = T("Project Task"))

        tablename = "workflow_entity" 
        table = s3db.super_entity(tablename,"workflow_entity_id",
                                  we_types)


        add_component("workflow_status", workflow_entity = "workflow_entity_id")


        tablename = "workflow_status"
        table = define_table(tablename,
                             Field("name"),
                             Field("status"),
                             super_link("workflow_entity_id","workflow_entity"),
                             *s3_meta_fields()
                            )

        return Storage()
