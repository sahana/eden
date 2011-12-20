# -*- coding: utf-8 -*-

"""
    Master Message Log to record/route all Inbound messages

    @Deprecated. Incident Reports are where unknown messages are initially deposited for onward routing.
"""

module = "ticket"
if deployment_settings.has_module(module):

    # -----------------
    # Categories table
    resourcename = "category"
    tablename = "%s_%s" % (module, resourcename)
    table = db.define_table(tablename,
                            Field("name"),
                            *s3_meta_fields())

    # -----------------
    # Tickets table (All sources get entered here : either manually or via S3XRC or Messaging)

    ticket_priority_opts = {
        3:T("High"),
        2:T("Medium"),
        1:T("Low")
    }

    resourcename = "log"
    tablename = "%s_%s" % (module, resourcename)
    table = db.define_table(tablename,
                            Field("subject"),
                            Field("message", "text"),
                            person_id(),
                            Field("attachment", "upload", autodelete = True),
                            Field("priority", "integer"),
                            Field("source", default="local"),
                            Field("source_id", "integer"),
                            Field("source_time", "datetime", default=request.utcnow),
                            location_id(),
                            Field("categories", "list:reference ticket_category"),
                            Field("verified", "boolean"),
                            Field("verified_details", "text"),
                            Field("actionable", "boolean"),
                            Field("actioned", "boolean"),
                            Field("actioned_details", "text"),
                            *s3_meta_fields())


    table.message.requires = IS_NOT_EMPTY()
    table.priority.requires = IS_NULL_OR(IS_IN_SET(ticket_priority_opts))
    table.categories.requires = IS_NULL_OR(IS_IN_DB(db, db.ticket_category.id, "%(name)s", multiple=True))
    table.categories.represent = lambda opt: opt and s3_represent_multiref(db.ticket_category, opt) or UNKNOWN_OPT

    s3mgr.configure(tablename,
                    list_fields=["id",
                                 "subject",
                                 #"categories",
                                 "attachment",
                                 "priority",
                                 "source",
                                 "source_id",
                                 "source_time",
                                 "location_id",
                                 "verified",
                                 "actionable",
                                 "actioned"
                                ])

