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

from e_cidadania.apps.news.models import Post
from e_cidadania.apps.spaces.models import Space

admin.autodiscover()

# Index page extra context
pub = Post.objects.all()
space_list = Space.objects.all()

extra_context = {
    'publication': pub,
    'spaces': space_list,
}

urlpatterns = patterns('',

    # Django administration
    (r'^admin/', include(admin.site.urls)),
    
    # Index
    (r'^$', direct_to_template, {
        'template':'site_index.html',
        'extra_context': extra_context
        }
    ),

    # User accounts
    #(r'^accounts/', include('apps.accounts.urls')),
    (r'^accounts/', include('apps.userprofile.urls')),
    #(r'^accounts/', include('apps.registration.urls')),
    
    (r'^spaces/', include('apps.spaces.urls')),
    
    (r'^calendar/', include('apps.swingtime.urls')),
    
    (r'^static/(?P<path>.*)$', 'django.views.static.serve',
        {'document_root': 'static'}),

)

if 'e_cidadania.apps.rosetta' in settings.INSTALLED_APPS:
    urlpatterns += patterns('',
        url(r'^rosetta/', include('apps.rosetta.urls')),
    )

# If DEBUG=True in settings.py add static content served by django.
#if settings.DEBUG:
#    urlpatterns += ('',
#    
#    (r'^static/(?P<path>.*)$', 'django.views.static.serve',
#        {'document_root': 'static'}),
#    
#    )
