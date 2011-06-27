from django.conf.urls.defaults import *

urlpatterns = patterns('e_cidadania.apps.cal.views',

    # News
    (r'^(?P<year>\d+)/(?P<month>\d+)/', include('e_cidadania.apps.news.urls')),

)
