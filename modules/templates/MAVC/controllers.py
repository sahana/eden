# -*- coding: utf-8 -*-

from gluon import *
from s3 import S3CustomController

THEME = "MAVC"

# =============================================================================
class index(S3CustomController):
    """ Custom Home Page """

    def __call__(self):

        response = current.response

        output = {}

        s3 = response.s3

        # Latest 4 Requests
        #s3db = current.s3db
        #list_id = "latest_reqs"
        #layout = s3db.req_req_list_layout
        #limit = 4
        #resource = s3db.resource("req_req")
        #s3db.req_customise_req_fields()
        #list_fields = s3db.get_config("req_req", "list_fields")
        #from s3 import FS
        #resource.add_filter(FS("cancel") != True)
        # Order with most recent first
        #orderby = "date desc"
        #output["latest_reqs"] = latest_records(resource, layout, list_id, limit, list_fields, orderby)

        # Latest 4 Offers
        #list_id = "latest_offers"
        #layout = s3db.req_commit_list_layout
        #limit = 4

        #resource = s3db.resource("req_commit")
        #s3db.req_customise_commit_fields()
        #list_fields = s3db.get_config("req_commit", "list_fields")
        #resource.add_filter(FS("cancel") != True)
        # Order with most recent first
        #orderby = "date desc"
        #output["latest_offers"] = latest_records(resource, layout, list_id, limit, list_fields, orderby)

        # What We Do
        #table = s3db.cms_post
        #ltable = s3db.cms_post_module
        #query = (ltable.module == "default") & \
        #        (ltable.resource == "index") & \
        #        (ltable.post_id == table.id) & \
        #        (table.deleted != True)
        #item = current.db(query).select(table.id,
        #                                table.body,
        #                                limitby=(0, 1)).first()
        #if item:
        #    what_we_do = DIV(XML(item.body))
        #    if current.auth.s3_has_role("ADMIN"):
        #        if s3.crud.formstyle == "bootstrap":
        #            _class = "btn"
        #        else:
        #            _class = "action-btn"
        #        what_we_do.append(A(current.T("Edit"),
        #                            _href=URL(c="cms", f="post",
        #                                      args=[item.id, "update"],
        #                                      vars={"module": "default",
        #                                            "resource": "index",
        #                                            }),
        #                            _class="%s cms-edit" % _class))
        #else:
        #    what_we_do = DIV()
        #    if current.auth.s3_has_role("ADMIN"):
        #        if s3.crud.formstyle == "bootstrap":
        #            _class = "btn"
        #        else:
        #            _class = "action-btn"
        #        what_we_do.append(A(current.T("Edit"),
        #                            _href=URL(c="cms", f="post",
        #                                      args=["create"],
        #                                      vars={"module": "default",
        #                                            "resource": "index",
        #                                            }),
        #                            _class="%s cms-edit" % _class))

        #output["what_we_do"] = what_we_do

        # Inject custom styles for homepage
        s3.stylesheets.append("../themes/MAVC/homepage.css")

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
        from s3.s3crud import S3CRUD
        table = resource.table
        if "deleted" in table:
            available_records = current.db(table.deleted != True)
        else:
            available_records = current.db(table._id > 0)
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
        dl = datalist.html()
        data = dl

    return data

# END =========================================================================
