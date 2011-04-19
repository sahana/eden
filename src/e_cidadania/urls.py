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
from django.views.generic.simple import direct_to_template

admin.autodiscover()

urlpatterns = patterns('',

    # Django administration
    (r'^admin/', include(admin.site.urls)),

    # Index
    (r'^$', 'e_cidadania.views.index_view'),

    # User accounts
    (r'^accounts/', include('e_cidadania.apps.userprofile.urls')),

    # Spaces
    (r'^spaces/', include('e_cidadania.apps.spaces.urls')),

    # News (this view of news is only for the index)
    (r'^news/add', 'e_cidadania.views.add_news'),

    (r'^news/(?P<post_id>\w+)/delete/', 'e_cidadania.views.delete_post'),

    (r'^news/(?P<post_id>\w+)/edit/', 'e_cidadania.views.edit_post'),

    (r'^news/(?P<post_id>\w+)', 'e_cidadania.views.view_post'),

    # Calendar
    (r'^calendar/', include('e_cidadania.apps.swingtime.urls')),

    # i18n switcher
    (r'^i18n/', include('django.conf.urls.i18n')),

    # Static content #### FOR DEVELOPMENT!! ####
    (r'^static/(?P<path>.*)$', 'django.views.static.serve',
        {'document_root': 'static'}),

    # Static content #### FOR DEVELOPMENT!! ####
    (r'^uploads/(?P<path>.*)$', 'django.views.static.serve',
        {'document_root': 'uploads'}),

    # This urls is for the django comments system
    (r'^comments/', include('django.contrib.comments.urls')),

    # This url is for the access to static pages. I hope this doesn't collide
    # with the index view
    (r'^(?P<slug>[\w\-]+)/', include('e_cidadania.apps.staticpages.urls')),
)

# Activate rosetta translation engine
if 'e_cidadania.apps.rosetta' in settings.INSTALLED_APPS:
    urlpatterns += patterns('',
        url(r'^rosetta/', include('e_cidadania.apps.rosetta.urls')),
    )

# If DEBUG=True in settings.py add static content served by django.
#if settings.DEBUG:
#    urlpatterns += ('',
#
#    (r'^static/(?P<path>.*)$', 'django.views.static.serve',
#        {'document_root': 'static'}),
#
#    )

