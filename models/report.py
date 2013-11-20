

#This is the model file for the report module . 


tablename = "report_new"  #name of the table .
priority_options =  {     #list of options present in priority field. 
1:T("High"),
2:T("Low"),
3:T("Medium")
} 
table = db.define_table(tablename,                               #DAL function to define a new table . 
                        Field("Type",requires=IS_NOT_EMPTY(),
                              label=T("Type")),
                        #Type field
                        Field("description","text",requires=IS_NOT_EMPTY(), 
                              label=T("Description")),
                        #Description Field
                        Field("Priority",requires=IS_IN_SET(priority_options),
                              label=T("Priority")),
                        #Priority Field
                        Field("Status",label=T("Status")),
                        #Status Field
                        *s3_meta_fields()
                        # This adds all the metadata to store
                        # information on who created/updated
                        # the record.
                        )               
REPORT_LIST =  T("Report lists")
s3.crud_strings[tablename] = Storage(        # Custom strings used in place of default one . 
    title_create = T("Add New "),
    title_display = T("Course Details"),
    title_list = REPORT_LIST,
    title_update = T("Edit A Report"),
    title_search = T("Search Report"),
    
    subtitle_create = T("Add New Report"),
    subtitle_list = T("Course"),
    label_list_button = REPORT_LIST,
    label_create_button = T("Report a Bug"),
    label_delete_button = T("Delete a Report"),
    msg_record_created = T("Report added"),
    msg_record_modified = T("Report updated"),
    msg_record_deleted = T("Report deleted"),
    msg_list_empty = T("No Bugs currently reported"))

