tablename = "training_course"
table = db.define_table(tablename,
						Field("name",
							   label=T("Name")),
						s3db.pr_person_id(label=T("Facilitator")),
						s3db.super_link("site_id", "org_site",
										 label=T("Venue"),
										 readable=False,
										 writable=False,
										 represent=s3db.org_site_represent),
						#Field("facilitator",
						#	    label=T("Facilitator")),
						Field("start", "datetime",
							   label=T("Start Date")),
						Field("welcome_pack", "upload",
							   label=T("Welcome Pack")),
						*s3.meta_fields()
						)


LIST_COURSE =  T("List Courses")
s3.crud_strings[tablename] = Storage(
    title_create = T("Add New Course"),
    title_display = T("Course Details"),
    title_list = LIST_COURSE,
    title_update = T("Edit Course"),
    title_search = T("Search Course"),
    title_upload = T("Import Course"),
    subtitle_create = T("Add New Course"),
    subtitle_list = T("Course"),
    label_list_button = LIST_COURSE,
    label_create_button = T("Add New Course"),
    label_delete_button = T("Delete Course"),
    msg_record_created = T("Course added"),
    msg_record_modified = T("Course updated"),
    msg_record_deleted = T("Course deleted"),
    msg_list_empty = T("No Course currently registered"))

def course_represent(id):
		table = db.training_course
		query = (table.id == id)
		record = db(query).select().first()
		if record:
			return record.name
		else:
			return "-"
			
			
course_id = S3ReusableField("course_id", db.training_course,
					requires=IS_ONE_OF(db,
									   "training_course.id",
									   "%(name)s"),
					represent=course_represent,
					label=T("Course"),
					ondelete="RESTRICT")
					
					
course_grade_opts = {
    1: T("No Show"),
    2: T("Failed"),
    3: T("Passed")
}

tablename = "training_participant"
table = db.define_table(tablename,
						course_id(),
						s3db.pr_person_id(label=T("Participant")),
						Field("grade", "integer",
							   requires=IS_IN_SET(course_grade_opts),
							   label=T("Grade")),
						*s3.meta_fields()
						)
						
s3db.add_component("training_participant",
					training_course="course_id")