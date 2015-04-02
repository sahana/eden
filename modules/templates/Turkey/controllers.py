# -*- coding: utf-8 -*-

from gluon import *
from s3 import S3CustomController

THEME = "Turkey"

# =============================================================================
class index(S3CustomController):
    """ Custom Home Page """

    def __call__(self):
        
        response = current.response
        output = {}
        s3 = response.s3
        
        from s3.s3query import FS
        s3db = current.s3db
        layout = s3.render_posts
        list_id = "news_datalist"
        limit = 4
        list_fields = ["series_id",
                       "date",
                       "title",                     
                       "body"                       
                       ]

        resource = s3db.resource("cms_post")
        resource.add_filter(FS("series_id$name") == "Haberler")
        # Order with next Event first
        orderby = "date DESC"
        output["news"] = latest_records(resource, layout, list_id, limit, list_fields, orderby)

        self._view(THEME, "index.html")
        return output
    
# =============================================================================
def latest_records(resource, layout, list_id, limit, list_fields, orderby):
    """
        Display a dataList of the latest records for a resource

        @todo: remove this wrapper
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
        data = datalist.html()

    return data

# END =========================================================================
