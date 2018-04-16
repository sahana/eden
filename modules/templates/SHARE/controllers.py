# -*- coding: utf-8 -*-

from gluon import *
from s3 import S3CustomController, S3FilterForm, S3DateFilter, S3OptionsFilter

from gluon import current
from gluon.storage import Storage

THEME = "SHARE"

# =============================================================================
class index(S3CustomController):
    """ Custom Home Page """
    
    # procedure contains:
    # 1. custom edit homepage (c=cms, f=blog)
    # 2. display map of requests
    # 3. list a summary of requests
    # 4. option to filter requests

    def __call__(self):

        #---------------------------------
        # initialize variables and objects
        output = {}
        T = current.T
        s3db = current.s3db
        request = current.request

        #------------------------------------------------------------
        # Allow editing of page content from browser using CMS module
        if current.deployment_settings.has_module("cms"):
            system_roles = current.auth.get_system_roles()
            ADMIN = system_roles.ADMIN in current.session.s3.roles
            s3db = current.s3db
            table = s3db.cms_post
            ltable = s3db.cms_post_module
            module = "default"
            resource = "index"
            query = (ltable.module == module) & \
                    ((ltable.resource == None) | \
                     (ltable.resource == resource)) & \
                    (ltable.post_id == table.id) & \
                    (table.deleted != True)
            custom_info = current.db(query).select(table.body,
                                            table.id,
                                            limitby=(0, 1)).first()
            if custom_info:
                if ADMIN:
                    custom_info = DIV(XML(custom_info.body),
                               BR(),
                               A(current.T("Edit"),
                                 _href=URL(c="cms", f="post",
                                           args=[custom_info.id, "update"]),
                                 _class="action-btn"))
                else:
                    custom_info = DIV(XML(custom_info.body))
            elif ADMIN:
                if current.response.s3.crud.formstyle == "bootstrap":
                    _class = "btn"
                else:
                    _class = "action-btn"
                custom_info = A(current.T("Edit"),
                         _href=URL(c="cms", f="post", args="create",
                                   vars={"module": module,
                                         "resource": resource
                                         }),
                         _class="%s cms-edit" % _class)
            else:
                custom_info = ""
        else:
            custom_info = ""
        output["custom_info"] = custom_info

        #------------------------
        # Map to display requests
        ftable = s3db.gis_layer_feature
        query = (ftable.controller == "req") & \
                (ftable.function == "req")
        layer = current.db(query).select(ftable.layer_id,
                                         limitby=(0, 1)
                                         ).first()
        try:
            layer_id = layer.layer_id
        except:
            current.log.error("Cannot find Layer for Map")
            layer_id = None

        feature_resources = [{"name"      : T("Requests"),
                              "id"        : "search_results",
                              "layer_id"  : layer_id,
                              "active"    : False,
                              }]

        _map = current.gis.show_map(callback='''S3.search.s3map()''',
                                    catalogue_layers=True,
                                    collapsed=True,
                                    feature_resources=feature_resources,
                                    save=False,
                                    search=True,
                                    toolbar=True,
                                    )
        output["_map"] = _map

        #--------------------
        # diplay request list
        resource = s3db.resource("req_req")
        resource.table.commit_status.represent = None
        list_id = "req_datalist"
        list_fields = ["purpose",
                       "priority",
                       "req_ref",
                       "site_id",
                       "date",
                       ]
        # Order with most recent request first
        orderby = "req_req.date"
        datalist, numrows = resource.datalist(fields = list_fields,
                                              limit = None,
                                              list_id = list_id,
                                              orderby = orderby,
                                              )
        if numrows == 0:
            current.response.s3.crud_strings["req_req"].msg_no_match = T("No requests at present.")

        ajax_url = URL(c="req", f="req", args="datalist.dl",
                       vars={"list_id": list_id})
        #@ToDo: Implement pagination properly
        output[list_id] = datalist.html(ajaxurl = ajax_url,
                                        pagesize = 0,
                                        )

        # ----------------------------
        # filter requests summary list
        filter_widgets = [S3OptionsFilter("req.priority",
                                          label=T("Priority"),
                                          ),
                          S3OptionsFilter("req.type",
                                          label=T("Type"),
                                          ),
                          S3OptionsFilter("req.site_id",
                                          label=T("Site"),
                                          ),
                          S3DateFilter("req.date",
                                       label = T("Date"),
                                       hide_time=True,
                                       ),
                          ]
        filter_form = S3FilterForm(filter_widgets,
                                   ajax=True,
                                   submit=True,
                                   url=ajax_url,
                                   )
        output["req_filter_form"] = filter_form.html(resource, request.get_vars, list_id)

        #----------------------
        # Create request button
        upload_4W_activity_btn = A(T("Upload 4W Activity"),
                         _href = URL(c="req",
                                     f="req",
                                     args="import",
                                     ),
                         _class = "action-btn button small",
                         )

#        system_roles = current.auth.get_system_roles()
#        can_request = current.auth.s3_has_role("NEEDS_LOGGER"): or (system_roles.ADMIN in current.session.s3.roles
        #print (current.session.s3.roles)
#        if can_request: 
        output["upload_4W_activity_btn"] = upload_4W_activity_btn
#        else:
#            output["upload_4W_activity_btn"] = ""

        # View title
        output["title"] = current.deployment_settings.get_system_name()

        self._view(THEME, "index.html")

        s3 = current.response.s3
        # Custom JS
        s3.scripts.append("/%s/static/themes/SHARE/js/homepage.js" % request.application)

        return output

# END =========================================================================
