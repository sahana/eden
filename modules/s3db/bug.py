from gluon import *
from gluon.storage import Storage
from ..s3 import *
from s3layouts import S3AddResourceLink
__all__ = ['S3BugreportModel']
class S3BugreportModel(S3Model):
    names = ['bug_report']
    def model(self):
        T = current.T
        bug_status = {1:T("Closed"),
                2:T("Active")
                }
        bug_type = {1:T("Bug"),
                2:T("Enhancement")
                }
        bug_priority = {1:T("Major"),
                       2:T("Minor")}        
        tablename = "bug_report"
        table = self.define_table(tablename,
        Field("Type", requires=IS_IN_SET(bug_type), label=T("Type")),
        Field("Description", "text", requires=IS_NOT_EMPTY()),
        Field("Priority", requires=IS_IN_SET(bug_priority), label=T("Priority")),
        Field("Status", requires=IS_IN_SET(bug_status), label=T("Status")),
        *s3_meta_fields()
        )
        self.crud_strings[tablename] = Storage(
            title_create=T("Report new bug"),
            title_display=T("Reported bugs"),
            title_list=T("List of reported bugs"),
            title_update=T("Edit bug report"),
            title_search=T("Search bug reports"),
            subtitle_create=T("Report new bug"),
            subtitle_list=T("Reported bugs"),
            label_list_button=T("List Vehicle Types"),
            label_create_button=T("Report new bug"),
            label_delete_button=T("Delete bug report"),
            msg_record_created=T("Your bug has been reported"),
            msg_record_modified=T("Report updated"),
            msg_record_deleted=T("Report deleted"),
            msg_list_empty=T("No bugs currently reported"))

       
