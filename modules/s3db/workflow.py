
from gluon import *
from gluon.storage import Storage
from ..s3 import *

__all__ = ["S3WorkflowModel"]


class S3WorkflowModel(S3Model):

    names = ["workflow_workflow"]

    def model(self):

        T = current.T

        tablename = "workflow_workflow"
        table = self.define_table(tablename,
                                Field("workflow", "string"), #this should be hidden 
                                Field("step1a", "string"), #here step1 name will be entered
                                Field("step1b", "string"), #here create/list will be enterd
                                Field("step2a", "string"), #here step2 will be entered
                                Field("step2b", "string"), #here create/list will be enterd
                                *s3_meta_fields())

