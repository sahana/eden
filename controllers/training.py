def index():
	return dict()
	
def course_rheader(r, tabs=[]):
	if r.representation != "html":
		return None
	if r.record is None:
		return None
		
	tabs = [(T("Basic Details"), None),
			(T("Participants"), "participant")]
		
	rheader_tabs = s3_rheader_tabs(r, tabs)
		
	course = r.record
		
	rheader = DIV(TABLE(
		TR(
			TH("%s: " % T("Name")),
			course.name,
			TH("%s: " % T("Start Date")),
			course.start
		   ),
		TR(
			TH("%s: " % T("Facilitator")),
			s3db.pr_person_represent(course.person_id),
		   )
	  ), rheader_tabs)
			  
	return rheader
		
		
	
def course():
	return s3_rest_controller(rheader=course_rheader)