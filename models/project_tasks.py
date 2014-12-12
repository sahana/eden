tablename = "project_tasks_task"
db.define_table(tablename,
				Field ("name", label=T("Task Name")),
				s3db.project_project_id(label=T("Project assigned"))
				)
				

s3.crud_strings[tablename] = Storage(
	label_create_button = T("Create Task"),
	title_display = T("Task Details"),
	title_list = T("List Tasks"),
	title_update = T("Edit Task"),
	title_upload = T("Import Tasks"),
	subtitle_list = T("Tasks"),
	label_list_button = T("List Tasks"),
	label_delete_button = T("Delete Task"),
	msg_record_created = T("Task added"),
	msg_record_modified = T("Task updated"),
	msg_record_deleted = T("Task deleted"),
	msg_list_empty = T("No Tasks currently registered")
)				