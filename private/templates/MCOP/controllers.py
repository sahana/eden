# -*- coding: utf-8 -*-

from gluon import current
from gluon.html import *
from gluon.storage import Storage

from s3.s3utils import S3CustomController
from s3.s3resource import S3FieldSelector

THEME = "MCOP"

# =============================================================================
class index(S3CustomController):
    """ Custom Home Page """

    def __call__(self):
        response = current.response
        s3 = response.s3
        s3db = current.s3db
        output = {}
        self._view(THEME, "index.html")
        
        # Organisations Data List
        resource = s3db.resource("org_organisation")
        
        datalist, numrows, ids = resource.datalist(list_id = "org_organisation_datalist",
                                                   #fields=list_fields,
                                                   #start=None,
                                                   limit=10,
                                                   #orderby=orderby,
                                                   layout = s3.org_organisations_list_layout
                                                   )
        output["org_organisation_datalist"] = datalist.html()

        # News Feed Data List
        list_fields = ["series_id",
                       "location_id",
                       "date",
                       "body",
                       "created_by",
                       "created_by$organisation_id",
                       "document.file",
                       "event_post.event_id",
                       ]
        resource = s3db.resource("cms_post")
        resource.add_filter(S3FieldSelector("post.series_id") != None)
        datalist, numrows, ids = resource.datalist(list_id = "cms_post_datalist",
                                                   fields=list_fields,
                                                   #start=None,
                                                   limit=10,
                                                   #list_id=list_id,
                                                   #orderby=orderby,
                                                   layout = s3db.cms_post_list_layout
                                                   )
        output["cms_post_datalist"] = datalist.html()

        #Data Buttons
        # Description of available data
        from s3db.cms import S3CMS
        for item in response.menu:
            item["cms"] = S3CMS.resource_content(module = item["c"], 
                                                 resource = item["f"])

        return output
