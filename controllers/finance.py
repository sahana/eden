def donations():
	return s3_rest_controller()
	
def index():
	return dict()
	
s3.crud_strings["finance_donations"] = Storage(
label_create = T("Create New Donation"),
title_display = T("Donations Details"),
title_list = T("List Donations"),
title_update = T("Edit Donation"),
title_upload = T("Import Donations"),
subtitle_list = T("Donations"),
label_list_button = T("List Donations"),
label_delete_button = T("Delete Donation"),
msg_record_created = T("Donation added"),
msg_record_modified = T("Donation updated"),
msg_record_deleted = T("Donation deleted"),
msg_list_empty = T("No Donations currently registered"))



	