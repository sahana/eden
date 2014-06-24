# -*- coding: utf-8 -*-

from os import path

from gluon import current, URL

from s3.s3utils import S3CustomController

THEME = "SSF"

# =============================================================================
class index(S3CustomController):
    """ Custom Home Page """

    def __call__(self):

        response = current.response
        settings = current.deployment_settings
        request = current.request
        s3 = response.s3
        db = current.db
        s3db = current.s3db
        T = current.T

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

        project_url = URL(c="project", f="location", extension="geojson")
        project_url = "%s?~.project_id$sector.name=Deployment" % project_url
        contributor_url = URL(c="pr", f="address", extension="geojson")

        # Set the marker
        mtable = s3db.gis_marker
        query = (mtable.name == "sunflower") | (mtable.name == "contributor")
        markers = db(query).select(mtable.name,
                                   mtable.image,
                                   mtable.height,
                                   mtable.width,
                                   cache=s3db.cache,
                                   limitby=(0, 2)
                                   )

        project_marker = None
        contributor_marker = None

        for marker in markers:
            if marker.name == "sunflower":
                project_marker = marker
            if marker.name == "contributor":
                contributor_marker = marker

        layers = [{"name"      : T("Deployments"),
                   "id"        : "deployments",
                   "tablename" : "project_location",
                   "url"       : project_url,
                   "active"    : True,
                   "marker"    : project_marker,
                   },
                  {"name"      : T("Contributors"),
                   "id"        : "contributors",
                   "tablename" : "pr_address",
                   "url"       : contributor_url,
                   "active"    : True,
                   "marker"    : contributor_marker,
                   },
                  ]

        output["map"] = current.gis.show_map(collapsed = True,
                                             feature_resources = layers,
                                             legend="float",
                                             )

        s3.scripts.append("http://www.google.com/jsapi?key=notsupplied-wizard")
        feed_control = "".join(('''
function LoadFeeds(){
 var feeds=[
  {title:'Tasks',
   url:\'''', settings.base.public_url, '''/''', request.application, '''/project/task.rss?task.status=2,3,4,11'
  },
  {title:'Tickets',
   url:'http://eden.sahanafoundation.org/timeline?ticket=on&changeset=on&milestone=on&max=50&daysback=90&format=rss'
  },
  {title:'Wiki',
   url:'http://eden.sahanafoundation.org/timeline?changeset=on&milestone=on&wiki=on&max=50&daysback=90&format=rss'
  },
  {title:'Github',
   url:'https://github.com/flavour/eden/commits/master.atom'
  },
  {title:'Twitter',
   url:'http://www.rssitfor.me/getrss?name=@SahanaFOSS'
  },
  {title:'Blog',
   url:'http://sahanafoundation.org/feed/?cat=33,39'
  }
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
 $('#feed-url').attr('href', feeds[0].url);
 $('#feed-url').attr('title', feeds[0].title);

 // Show feed-url
 $('.gfc-tabHeader').click(feeds, function(){
  activeTab = $('.gfc-tabhActive').html();
  for(i=0; i<feeds.length; i++){
   if(feeds[i].title == activeTab){
    $('#feed-url').attr('href', feeds[i].url);
    $('#feed-url').attr('title', feeds[i].title);
    break;
   }
  }
 });
}
google.load('feeds','1')
google.setOnLoadCallback(LoadFeeds)'''))
        s3.js_global.append(feed_control)
        
        return output

# =============================================================================
