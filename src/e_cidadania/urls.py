# -*- coding: utf-8 -*-
#
# Copyright (c) 2010 Cidadanía Coop.
# Written by: Oscar Carballal Prego <info@oscarcp.com>
#
# This file is part of e-cidadania.
#
# e-cidadania is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# e-cidadania is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with e-cidadania. If not, see <http://www.gnu.org/licenses/>.

from django.conf.urls.defaults import *
from django.conf import settings
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.views.generic.simple import direct_to_template

from e_cidadania.views import IndexEntriesFeed, ListNews, AddPost, EditPost, \
                              DeletePost, ViewPost

admin.autodiscover()

# We put here the dictionary with all the packages for translatin JavaScript code
# Please refer to https://docs.djangoproject.com/en/dev/topics/i18n/internationalization/#specifying-translation-strings-in-javascript-code
js_info_dict = {
    'packages': ('e_cidadania.apps.debate',),
}

urlpatterns = patterns('',


    (r'^grappelli/', include('grappelli.urls')),
    
    # Django administration
    (r'^admin/', include(admin.site.urls)),

    # Index
    url(r'^$', 'e_cidadania.views.index_view', name='site-index'),

    # User accounts
    (r'^accounts/', include('e_cidadania.apps.userprofile.urls')),

    # Spaces
    (r'^spaces/', include('e_cidadania.apps.spaces.urls')),
    
    # Invitations
    url(r'^invite/', 'e_cidadania.views.invite', name='invite'),
    
    # News (this view of news is only for the index)
    url(r'^news/$', ListNews.as_view(), name='list-site-news'),
    
    url(r'^news/add/$', AddPost.as_view(), name='add-site-post'),

    url(r'^news/(?P<post_id>\w+)/delete/$', DeletePost.as_view(), name='delete-site-post'),

    url(r'^news/(?P<post_id>\w+)/edit/$', EditPost.as_view(), name='edit-site-post'),

    url(r'^news/(?P<post_id>\w+)/$', ViewPost.as_view(), name='view-site-post'),
    
    # RSS Feed for the index news ONLY
    url(r'^rss/$', IndexEntriesFeed(), name='site-feed'),

    # i18n switcher
    (r'^i18n/', include('django.conf.urls.i18n')),
    
    #(r'^api/', include('e_cidadania.apps.api.urls')),

    # Static content #### FOR DEVELOPMENT!! ####
    (r'^uploads/(?P<path>.*)$', 'django.views.static.serve',
        {'document_root': 'uploads'}),
    
    # Static content #### FOR DEVELOPMENT!! ####
    (r'^static/(?P<path>.*)$', 'django.views.static.serve',
        {'document_root': 'static'}),

    # This urls is for the django comments system
    (r'^comments/', include('django.contrib.comments.urls')),

    (r'^jsi18n/$', 'django.views.i18n.javascript_catalog', js_info_dict),

    # This url is for the access to static pages. I hope this doesn't collide
    # with the index view
    (r'^(?P<slug>[\w\-]+)/', include('e_cidadania.apps.staticpages.urls')),
)

if settings.DEBUG:
    # Serve static files
    urlpatterns += staticfiles_urlpatterns()
