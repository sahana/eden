# -*- coding: utf-8 -*-

from gluon import *
from s3 import FS, S3CRUD, S3CustomController

SAVE = "Save the Children"
THEME = "SCPHIMS"

# =============================================================================
class index(S3CustomController):
    """ Custom Home Page """

    def __call__(self):

        T = current.T
        s3db = current.s3db
        crud_strings = current.response.s3.crud_strings

        output = {}

        # List of Open Events
        resource = s3db.resource("event_event")
        resource.add_filter(FS("~.closed") == False)
        layout = s3db.event_event_list_layout
        list_id = "events_datalist"
        limit = 5
        list_fields = ["name",
                       "event_type_id",
                       "start_date",
                       "event_location.location_id",
                       "comments",
                       ]
        orderby = "start_date"
        crud_strings["event_event"].update(msg_no_match = T("No Active Responses"),
                                           )
        output["events"] = latest_records(resource, layout, list_id, limit, list_fields, orderby)

        # List of Pending Activities
        resource = s3db.resource("project_activity")
        resource.add_filter(FS("~.date") > current.request.utcnow)
        resource.add_filter(FS("organisation.name") == SAVE)
        layout = s3db.project_activity_list_layout
        list_id = "activities_datalist"
        limit = 5
        list_fields = ["name",
                       #"activity_type.activity_type_id",
                       "status_id",
                       "date",
                       "location_id",
                       "comments",
                       ]
        orderby = "date"
        crud_strings["project_activity"].update(msg_no_match = T("No Pending Activities"),
                                                )
        output["activities"] = latest_records(resource, layout, list_id, limit, list_fields, orderby)

        # Allow editing of page content from browser using CMS module
        #system_roles = current.auth.get_system_roles()
        #ADMIN = system_roles.ADMIN in current.session.s3.roles
        #table = s3db.cms_post
        #ltable = s3db.cms_post_module
        #module = "default"
        #resource = "index"
        #query = (ltable.module == module) & \
        #        ((ltable.resource == None) | \
        #         (ltable.resource == resource)) & \
        #        (ltable.post_id == table.id) & \
        #        (table.deleted != True)
        #item = current.db(query).select(table.body,
        #                                table.id,
        #                                limitby=(0, 1)).first()
        #if item:
        #    if ADMIN:
        #        item = DIV(XML(item.body),
        #                   BR(),
        #                   A(current.T("Edit"),
        #                     _href=URL(c="cms", f="post",
        #                               args=[item.id, "update"]),
        #                     _class="action-btn"))
        #    else:
        #        item = DIV(XML(item.body))
        #elif ADMIN:
        #    if current.response.s3.crud.formstyle == "bootstrap":
        #        _class = "btn"
        #    else:
        #        _class = "action-btn"
        #    item = A(current.T("Edit"),
        #             _href=URL(c="cms", f="post", args="create",
        #                       vars={"module": module,
        #                             "resource": resource
        #                             }),
        #             _class="%s cms-edit" % _class)
        #else:
        #    item = ""
        #output["item"] = item

        self._view(THEME, "index.html")
        return output

# =============================================================================
def latest_records(resource, layout, list_id, limit, list_fields, orderby):
    """
        Display a dataList of the latest records for a resource
    """

    #orderby = resource.table[orderby]
    datalist, numrows, ids = resource.datalist(fields=list_fields,
                                               start=None,
                                               limit=limit,
                                               list_id=list_id,
                                               orderby=orderby,
                                               layout=layout)
    if numrows == 0:
        # Empty table or just no match?
        table = resource.table
        #if "deleted" in table:
        available_records = current.db(table.deleted != True)
        #else:
        #    available_records = current.db(table._id > 0)
        if available_records.select(table._id,
                                    limitby=(0, 1)).first():
            msg = DIV(S3CRUD.crud_string(resource.tablename,
                                         "msg_no_match"),
                      _class="empty")
        else:
            msg = DIV(S3CRUD.crud_string(resource.tablename,
                                         "msg_list_empty"),
                      _class="empty")
        data = msg
    else:
        # Render the list
        data = datalist.html()

    return data

# END =========================================================================
