# -*- coding: utf-8 -*-

from gluon import *
from s3 import FS, S3CRUD, S3CustomController

#SAVE = "Save the Children"
THEME = "SCPHIMS"

# =============================================================================
class index(S3CustomController):
    """ Custom Home Page """

    def __call__(self):

        T = current.T
        db = current.db
        s3db = current.s3db
        s3 = current.response.s3
        #crud_strings = s3.crud_strings

        output = {}

        # Map
        ltable = s3db.gis_layer_feature
        layers = db(ltable.name.belongs(("Offices", "Responses"))).select(ltable.layer_id,
                                                                          ltable.name
                                                                          )
        offices = None
        response_areas = None
        for layer in layers:
            if layer.name == "Offices":
                offices = layer.layer_id
            elif layer.name == "Responses":
                response_areas = layer.layer_id

        feature_resources = [{"name": T("SCP Offices"),
                              "active": True,
                              "layer_id": offices,
                              },
                             {"name": T("SCP Response Areas"),
                              "active": True,
                              "layer_id": response_areas,
                              },
                             ]
        output["map"] = current.gis.show_map(feature_resources = feature_resources,
                                             )

        # DataTable of Open Events
        tablename = "event_event"
        resource = s3db.resource(tablename)
        resource.add_filter(FS("~.closed") == False)

        list_fields = ["name",
                       "event_location.location_id",
                       ]
        start = None
        limit = 5
        orderby = "event_event.start_date"

        # Get the data table
        dt, totalrows, ids = resource.datatable(fields=list_fields,
                                                start=start,
                                                limit=limit,
                                                orderby=orderby)
        displayrows = totalrows

        if dt.empty:
            empty_str = S3CRUD.crud_string(tablename,
                                           "msg_list_empty")
        else:
            empty_str = S3CRUD.crud_string(tablename,
                                           "msg_no_match")
        empty = DIV(empty_str, _class="empty")

        dtargs = {}

        # @ToDo: Permissions
        #messages = current.messages
        c, f = tablename.split("_", 1)
        read_url = URL(c=c, f=f,
                       args = "[id].popup")
        #delete_url = URL(c=c, f=f,
        #                 args=["[id]", "delete"])
        dtargs["dt_row_actions"] = [{"label": current.messages.READ,
                                     "url": read_url,
                                     "icon": "fa fa-eye",
                                     "_class": "s3_modal",
                                     },
                                    # @ToDo: AJAX delete
                                    #{"label": messages.DELETE,
                                    # "url": delete_url,
                                    # "icon": "fa fa-trash",
                                    # },
                                    ]
        #dtargs["dt_action_col"] = len(list_fields)
        #dtargs["dt_ajax_url"] = r.url(vars={"update": tablename},
        #                              representation="aadata")

        list_id = "custom-list-%s" % tablename
        s3.no_formats = True

        datatable = dt.html(totalrows,
                            displayrows,
                            id=list_id,
                            **dtargs)

        if dt.data:
            empty.update(_style="display:none")
        else:
            datatable.update(_style="display:none")
        contents = DIV(datatable, empty, _class="dt-contents")

        # Render the widget
        output["active_responses"] = DIV(contents,
                                         _class="card-holder",
                                         )

       # Allow editing of page content from browser using CMS module
        system_roles = current.auth.get_system_roles()
        ADMIN = system_roles.ADMIN in current.session.s3.roles
        table = s3db.cms_post
        ltable = s3db.cms_post_module
        module = "default"
        resource = "index"
        query = (ltable.module == module) & \
                ((ltable.resource == None) | \
                 (ltable.resource == resource)) & \
                (ltable.post_id == table.id) & \
                (table.deleted != True)
        item = db(query).select(table.body,
                                table.id,
                                limitby=(0, 1)).first()
        if item:
            if ADMIN:
                item = DIV(XML(item.body),
                           BR(),
                           A(current.T("Edit"),
                             _href=URL(c="cms", f="post",
                                       args=[item.id, "update"]),
                             _class="action-btn"))
            else:
                item = DIV(XML(item.body))
        elif ADMIN:
            if s3.crud.formstyle == "bootstrap":
                _class = "btn"
            else:
                _class = "action-btn"
            item = A(current.T("Edit"),
                     _href=URL(c="cms", f="post", args="create",
                               vars={"module": module,
                                     "resource": resource
                                     }),
                     _class="%s cms-edit" % _class)
        else:
            item = ""
        output["cms"] = item

        self._view(THEME, "index.html")
        return output

# END =========================================================================
