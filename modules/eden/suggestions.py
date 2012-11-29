__all__ = ['S3SuggestionModel']

from gluon import *
from ..s3 import *

class S3SuggestionModel(S3Model):
    TABLE_NAME = 'suggestions_suggestions'
    COMMENTS_TABLE_NAME = 'suggestions_comments'

    def model(self):
        
        T = current.T
        db = current.db
        crud_strings = current.response.s3.crud_strings

        priority_opts = {
            1: T('Low priority'),
            2: T('Medium priority'),
            3: T('High priority')
        }

        table = db.define_table(S3SuggestionModel.TABLE_NAME,
                    Field('suggestion', 'text', label=T('Suggestion'), required=True),
                    s3_comments('comments', label=T('Comments')),
                    Field('priority', 'integer', 
                        requires=IS_IN_SET(priority_opts),
                        label=T('Priority')),
                    *s3_meta_fields())

        table.created_by.label = T("Suggested By")
        table.created_by.readable = True
        table.modified_on.label = T("Last Modification")

        crud_strings[S3SuggestionModel.TABLE_NAME] = Storage(
            title_create = T("Make a suggestion"),
            title_display = T("Suggestion Details"),
            title_list = T("Suggestion"),
            title_update = T("Edit Suggestion"),
            title_search = T("Search Suggestion"),
            title_upload = T("Import Suggestion"),
            subtitle_create = T("Add New Suggestion"),
            label_list_button = T("List Suggestions"),
            label_create_button = T("Make a suggestion"),
            msg_record_created = T("Suggestion added"),
            msg_record_modified = T("Suggestion updated"),
            msg_record_deleted = T("Suggestion deleted"),
            msg_list_empty = T("No Suggestions"))

        suggestion_id = S3ReusableField("suggestion_id", db.suggestions_suggestions,
                    requires = IS_ONE_OF(db,
                                     "suggestions_suggestions.id",
                                     "%(name)s"),
                    label = T("Suggestion"),
                    ondelete = "RESTRICT")

        self.add_component("suggestions_comments", suggestions_suggestions="suggestion_id")

        table = self.define_table(S3SuggestionModel.COMMENTS_TABLE_NAME,
                             suggestion_id(),
                             Field("body", "text", notnull=True,
                                   label = T("Comment")),
                             *s3_meta_fields())
        table.created_by.label = T("Author")
        table.created_by.readable = True
