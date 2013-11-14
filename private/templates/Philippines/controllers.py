# -*- coding: utf-8 -*-

from gluon import current
from gluon.html import *
from gluon.storage import Storage

from s3.s3utils import S3CustomController

THEME = "Philippines"

# =============================================================================
class index(S3CustomController):
    """ Custom Home Page """

    def __call__(self):

        response = current.response
        
        output = {}
        #output["title"] = response.title = current.deployment_settings.get_system_name()

        s3 = response.s3
        # Image Carousel
        s3.jquery_ready.append('''$('#myCarousel').carousel()''')

        # Latest 4 Requests
        s3db = current.s3db
        s3db.req_customize_req_fields()
        listid = "latest_reqs"
        layout = s3db.req_render_reqs
        limit = 4
        list_fields = s3db.get_config("req_req", "list_fields")

        resource = s3db.resource("req_req")
        #resource.add_filter(S3FieldSelector("series_id$name") == "Request")
        # Order with most recent first
        orderby = "date desc"
        output["latest_reqs"] = latest_records(resource, layout, listid, limit, list_fields, orderby)

        # Latest 4 Offers
        s3db.req_customize_commit_fields()
        listid = "latest_offers"
        layout = s3db.req_render_commits
        #limit = 4

        resource = s3db.resource("req_commit")
        #resource.add_filter(S3FieldSelector("series_id$name") == "Offer")
        # Order with most recent first
        #orderby = "date desc"
        output["latest_offers"] = latest_records(resource, layout, listid, limit, list_fields, orderby)

        # What We Do
        table = s3db.cms_post
        ltable = s3db.cms_post_module
        query = (ltable.module == "default") & \
                (ltable.resource == "index") & \
                (ltable.post_id == table.id) & \
                (table.deleted != True)
        item = current.db(query).select(table.body,
                                        limitby=(0, 1)).first()
        if item:
            output["what_we_do"] = DIV(XML(item.body))
        else:
            output["what_we_do"] = ""

        self._view(THEME, "index.html")
        return output

# =============================================================================
def latest_records(resource, layout, listid, limit, list_fields, orderby):
    """
        Display a dataList of the latest records for a resource
    """

    #orderby = resource.table[orderby]
    datalist, numrows, ids = resource.datalist(fields=list_fields,
                                               start=None,
                                               limit=limit,
                                               listid=listid,
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
