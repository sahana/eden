# -*- coding: utf-8 -*-

from gluon import current
from gluon.html import *

from s3 import FS, S3CustomController

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

        # Alerts Data List
        resource = s3db.resource("cms_post")
        # Only show Alerts
        #resource.add_filter(FS("series_id$name").belongs(["Alert"]))
        #resource.add_filter(FS("post.series_id") != None)
        # Only show Open Alerts
        resource.add_filter(FS("expired") == False)
        # Only show Alerts which are linked to Open Incidents or not linked to any Incident
        resource.add_filter((FS("incident.closed") == False) | (FS("incident.id") == None))
        list_id = "cms_post_datalist"
        list_fields = [#"series_id",
                       "location_id",
                       "date",
                       "body",
                       "created_by",
                       "created_by$organisation_id",
                       "document.file",
                       "event_post.event_id",
                       "event_post.incident_id",
                       ]
        # Order with most recent Alert first
        orderby = "cms_post.date desc"
        datalist, numrows, ids = resource.datalist(fields = list_fields,
                                                   #start = None,
                                                   limit = 5,
                                                   list_id = list_id,
                                                   orderby = orderby,
                                                   layout = s3db.cms_post_list_layout
                                                   )
        ajax_url = URL(c="cms", f="post", args="datalist.dl", vars={"list_id": list_id})
        output[list_id] = datalist.html(ajaxurl = ajax_url,
                                        pagesize = 5
                                        )

        # Incidents Data List
        resource = s3db.resource("event_incident")
        # Only show Open Incidents
        resource.add_filter(FS("closed") == False)
        list_id = "event_incident_datalist"
        list_fields = ["name",
                       "location_id",
                       "zero_hour",
                       "modified_by",
                       "organisation_id",
                       "comments",
                       ]
        # Order with most recent Incident first
        orderby = "event_incident.zero_hour desc"
        datalist, numrows, ids = resource.datalist(fields = list_fields,
                                                   #start = None,
                                                   limit = 5,
                                                   list_id = list_id,
                                                   orderby = orderby,
                                                   layout = s3db.event_incident_list_layout
                                                   )
        ajax_url = URL(c="event", f="incident", args="datalist.dl", vars={"list_id": list_id})
        output[list_id] = datalist.html(ajaxurl = ajax_url,
                                        pagesize = 5
                                        )

        # Tasks Data List
        resource = s3db.resource("project_task")
        # Only show Active Tasks
        active_statuses = s3db.project_task_active_statuses
        resource.add_filter(FS("status").belongs(active_statuses))
        # Only show Tasks which are linked to Open Incidents or not linked to any Incident
        resource.add_filter((FS("incident.incident_id$closed") == False) | (FS("incident.id") == None))
        list_id = "project_task_datalist"
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
        # Order with most urgent Task first
        orderby = "project_task.date_due asc"
        datalist, numrows, ids = resource.datalist(fields = list_fields,
                                                   #start = None,
                                                   limit = 5,
                                                   list_id = list_id,
                                                   orderby = orderby,
                                                   layout = s3db.project_task_list_layout
                                                   )
        ajax_url = URL(c="project", f="task", args="datalist.dl", vars={"list_id": list_id})
        output[list_id] = datalist.html(ajaxurl = ajax_url,
                                        pagesize = 5
                                        )

        # MCOP RSS News Feed
        #s3.external_stylesheets.append("//www.google.com/uds/solutions/dynamicfeed/gfdynamicfeedcontrol.css")
        s3.scripts.append("//www.google.com/jsapi?key=notsupplied-wizard")
        s3.scripts.append("//www.google.com/uds/solutions/dynamicfeed/gfdynamicfeedcontrol.js")
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
