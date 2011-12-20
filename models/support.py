# -*- coding: utf-8 -*-

"""
    Support Requests
"""

if deployment_settings.get_options_support_requests():

    # -------------------------------------------------------------------------
    support_request_types = {
        1 : T("Bug"),
        2 : T("Feature Request")
    }
    support_status_opts = {
        1 : T("Open"),
        2 : T("Closed")
    }

    tablename = "support_req"
    table = db.define_table(tablename,
                            Field("name", notnull=True,
                                  label=T("Short Description")),
                            Field("type", "integer", label=T("Type"),
                                  requires=IS_IN_SET(support_request_types,
                                                     zero="%s..." % T("Please select")),
                                  represent=lambda opt: \
                                    support_request_types.get(opt,
                                                              UNKNOWN_OPT)),
                            Field("details", "text", label = T("Details"),
                                  comment = "%s%s" % (T("Please provide the URL of the page you are referring to, a description of what you expected to happen & what actually happened."),
                                                      T("If a ticket was issued then please provide the Ticket ID."))),
                            Field("status", "integer", label=T("Status"),
                                  default=1,
                                  requires=IS_IN_SET(support_status_opts),
                                  represent=lambda opt: \
                                    support_status_opts.get(opt, UNKNOWN_OPT)),
                            Field("actions", "text", label = T("Actions"),
                                  comment = T("Actions taken as a result of this request.")),
                            *s3_meta_fields())

    # CRUD strings
    ADD_REQUEST = T("New Support Request")
    LIST_REQUESTS = T("List Support Requests")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_REQUEST,
        title_display = T("Request Details"),
        title_list = LIST_REQUESTS,
        title_update = T("Edit Request"),
        title_search = T("Search Support Requests"),
        subtitle_create = T("Add New Request"),
        subtitle_list = T("Support Requests"),
        label_list_button = LIST_REQUESTS,
        label_create_button = ADD_REQUEST,
        label_delete_button = T("Delete Request"),
        msg_record_created = T("Request added"),
        msg_record_modified = T("Request updated"),
        msg_record_deleted = T("Request deleted"),
        msg_list_empty = T("No Support Requests currently registered"))

# END -------------------------------------------------------------------------
