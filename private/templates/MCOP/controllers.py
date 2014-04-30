# -*- coding: utf-8 -*-

from gluon import current
from gluon.html import *
from gluon.storage import Storage

from s3.s3resource import S3FieldSelector
from s3.s3utils import S3CustomController

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

        # Map
        # Enable Layers by default
        callback = '''S3.gis.show_map()
var layer,layers=S3.gis.maps.default_map.layers
for(var i=0,len=layers.length;i<len;i++){
 layer=layers[i]
 layer_name=layer.name
 if((layer_name=='Alerts')||(layer_name=='Incidents')||(layer_name=='Tasks')){layer.setVisibility(true)}}'''
        gis = current.gis
        #config = gis.get_config()
        #config.zoom = 8
        map = gis.show_map(width=600,
                           height=600,
                           callback=callback,
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

        # Incidents Data List
        resource = s3db.resource("event_incident")
        list_fields = ["name",
                       "location_id",
                       "zero_hour",
                       "modified_by",
                       "organisation_id",
                       "comments",
                       ]
        datalist, numrows, ids = resource.datalist(list_id = "event_incident_datalist",
                                                   fields = list_fields,
                                                   #start=None,
                                                   limit=5,
                                                   #list_id=list_id,
                                                   #orderby=orderby,
                                                   layout = s3db.event_incident_list_layout
                                                   )
        output["event_incident_datalist"] = datalist.html()

        # Tasks Data List
        resource = s3db.resource("project_task")
        list_fields = ["name",
                       "description",
                       "comments",
                       "location_id",
                       "priority",
                       "status",
                       "date_due",
                       "pe_id",
                       "task_project.project_id",
                       #"organisation_id$logo",
                       "modified_by",
                       "source_url"
                        ]
        datalist, numrows, ids = resource.datalist(list_id = "project_task_datalist",
                                                   fields = list_fields,
                                                   #start=None,
                                                   limit=5,
                                                   #list_id=list_id,
                                                   orderby = "project_task.date_due asc",
                                                   layout = s3db.project_task_list_layout
                                                   )
        output["project_task_datalist"] = datalist.html()

        # MCOP News Feed
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
# =============================================================================
class about(S3CustomController):
    """ Custom Home Page """

    def __call__(self):
        output = {}
        self._view(THEME, "about.html")
        return output
# END =========================================================================
