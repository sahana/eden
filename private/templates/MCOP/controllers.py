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

        gis = current.gis
        #config = gis.get_config()
        #config.zoom = 8
        map = gis.show_map(width=600,
                           height=600,
                           catalogue_layers=True,
                           collapsed=True,
                           save=False,
                           )
        output["map"] = map

        # Organisations Data List
        #resource = s3db.resource("org_organisation")
        
        #datalist, numrows, ids = resource.datalist(list_id = "org_organisation_datalist",
                                                   #fields=list_fields,
                                                   #start=None,
        #                                           limit=10,
                                                   #orderby=orderby,
        #                                           layout = s3db.org_organisation_list_layout
        #                                           )
        #output["org_organisation_datalist"] = datalist.html()

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
        resource.add_filter(S3FieldSelector("series_id$name").belongs(["Alert"]))
        #resource.add_filter(S3FieldSelector("post.series_id") != None)
        datalist, numrows, ids = resource.datalist(list_id = "cms_post_datalist",
                                                   fields=list_fields,
                                                   #start=None,
                                                   limit=5,
                                                   #list_id=list_id,
                                                   #orderby=orderby,
                                                   layout = s3db.cms_post_list_layout
                                                   )
        output["cms_post_datalist"] = datalist.html()

        #Project ("Incident") Data List
        resource = s3db.resource("project_project")
        list_fields = ["name",
                       "description",
                       "location.location_id",
                       "start_date",
                       "organisation_id",
                       "organisation_id$logo",
                       "modified_by",
                       ]
        datalist, numrows, ids = resource.datalist(list_id = "project_project_datalist",
                                                   fields = list_fields,
                                                   #start=None,
                                                   limit=5,
                                                   #list_id=list_id,
                                                   #orderby=orderby,
                                                   layout = s3db.project_project_list_layout
                                                   )
        output["project_project_datalist"] = datalist.html()

        # Task Data List
        resource = s3db.resource("project_task")
        list_fields = ["name",
                       "description",
                       "location_id",
                       "date_due",
                       "pe_id",
                       "task_project.project_id",
                       #"organisation_id$logo",
                       "modified_by",
                        ]
        datalist, numrows, ids = resource.datalist(list_id = "project_task_datalist",
                                                   fields = list_fields,
                                                   #start=None,
                                                   limit=5,
                                                   #list_id=list_id,
                                                   #orderby=orderby,
                                                   layout = s3db.project_task_list_layout
                                                   )
        output["project_task_datalist"] = datalist.html()
        #MCOP News Feed

        #s3.external_stylesheets.append("http://www.google.com/uds/solutions/dynamicfeed/gfdynamicfeedcontrol.css")
        s3.scripts.append("http://www.google.com/jsapi?key=notsupplied-wizard")
        s3.scripts.append("http://www.google.com/uds/solutions/dynamicfeed/gfdynamicfeedcontrol.js")
        # feedCycleTime: milliseconds before feed is reloaded (5 minutes)
        s3.js_global.append(
"""
function LoadDynamicFeedControl(){
 var feeds=[{title:'News', url:'http://psmcop.org/?feed=rss2'}]
 var options={
  feedCycleTime:300000,
  numResults:5,
  stacked:true,
  horizontal:false,
 }
 new GFdynamicFeedControl(feeds,'feed-control',options);
}
google.load('feeds','1');
google.setOnLoadCallback(LoadDynamicFeedControl);
"""
)

        # Data Buttons
        # Description of available data
        from s3db.cms import S3CMS
        resource_content = S3CMS.resource_content
        for item in response.menu:
            item["cms"] = resource_content(module = item["c"], 
                                           resource = item["f"])

        return output

# END =========================================================================
