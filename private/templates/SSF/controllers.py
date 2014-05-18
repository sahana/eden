# -*- coding: utf-8 -*-

from os import path

from gluon import current

from s3.s3utils import S3CustomController
from s3.s3query import S3FieldSelector

THEME = "SSF"

# =============================================================================
class index(S3CustomController):
    """ Custom Home Page """

    def __call__(self):

        response = current.response
        settings = current.deployment_settings
        request = current.request
        s3 = response.s3
        T = current.T
        gis = current.gis

        output = {}
        output["title"] = response.title = current.deployment_settings.get_system_name()

        view = path.join(current.request.folder, "private", "templates",
                         THEME, "views", "index.html")
        try:
            # Pass view as file not str to work in compiled mode
            response.view = open(view, "rb")
        except IOError:
            from gluon.http import HTTP
            raise HTTP(404, "Unable to open Custom View: %s" % view)

        project_task_status_opts = settings.get_project_task_status_opts()
        # Which options for the Status for a Task count as the task being 'Active'
        project_task_active_statuses = [2, 3, 4, 11]

        s3db = current.s3db

        # TODO : Set the layout.
        # layout = s3.render_posts
        # list_id = "news_datalist"
        limit = 10
        list_fields = ["name",
                       "description",
                       "priority",
                       "status",
                       "created_by",
                       "created_by$organisation_id",
                       ]

        resource = s3db.resource("project_task")
        
        resource.add_filter(S3FieldSelector("status").belongs(project_task_active_statuses))
        
        orderby = "priority"

        # TODO : Does not return any records if not logged in.
        datalist, numrows, ids = resource.datalist(fields=list_fields,
                                               start=None,
                                               limit=limit,
                                               # list_id=list_id,
                                               orderby=orderby,
                                               # layout=layout
                                               )
        output["tasks"] = datalist.html()

        s3.scripts.append("http://www.google.com/jsapi?key=notsupplied-wizard")
        feed_control = "".join(('''
function LoadFeeds(){
 var feeds=[
  {
   title:'Tasks',
   url:\'''', settings.base.public_url, '''/''', request.application, '''/project/task.rss'
  },
  {
   title:'Wiki Updates',
   url:'http://eden.sahanafoundation.org/timeline?changeset=on&milestone=on&wiki=on&max=50&daysback=90&format=rss'
  },
  {
   title:'Tickets',
   url:'http://eden.sahanafoundation.org/timeline?ticket=on&changeset=on&milestone=on&max=50&daysback=90&format=rss'
  },
  {
   title:'Github',
   url:'https://github.com/flavour/eden/commits/master.atom'
  },
  {
   title:'Twitter',
   url:'http://www.rssitfor.me/getrss?name=@SahanaFOSS'
  },
 ];
 
 var feedControl = new google.feeds.FeedControl();

 // Add feeds.
 for(i=0; i<feeds.length; i++){
  feedControl.addFeed(feeds[i].url, feeds[i].title);
 }

 feedControl.setNumEntries(5);
 
 feedControl.draw(document.getElementById("feed-control"),
 {
  drawMethod: 'content',
  drawMode : google.feeds.FeedControl.DRAW_MODE_TABBED
 });
 
 // Initialise feed-url input
 $('#feed-url').val(feeds[0].url);

 // Show feed-url
 $('.gfc-tabHeader').click(feeds, function(){
  activeTab = $('.gfc-tabhActive').html();
  for(i=0; i<feeds.length; i++){
   if(feeds[i].title == activeTab){
    $('#feed-url').val(feeds[i].url);
    break;
   }
  }
 });     
 
}
google.load('feeds','1')
google.setOnLoadCallback(LoadFeeds)'''))
        s3.js_global.append(feed_control)

        output["map"] = gis.show_map()
        
        return output

# =============================================================================
