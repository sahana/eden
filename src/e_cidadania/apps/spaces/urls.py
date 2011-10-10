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

"""  
This file contains all the URLs that e_cidadania will inherit when the user
access to '/spaces/'.
"""
from django.conf.urls.defaults import *

from e_cidadania.apps.spaces.views import GoToSpace, ViewSpaceIndex, ListSpaces,\
                                          DeleteSpace, ListDocs, DeleteDocument, \
                                          ListMeetings, DeleteMeeting, ViewMeeting, \
                                          ListPosts, SpaceFeed

# NOTICE: Don't change the order of urlpatterns or it will probably break.

urlpatterns = patterns('e_cidadania.apps.spaces.views',

    # RSS Feed
    url(r'^(?P<space_name>\w+)/rss/$', SpaceFeed(), name='space-feed'),
    
    # News
    (r'^(?P<space_name>\w+)/news/', include('e_cidadania.apps.news.urls')),

    # Proposals
    (r'^(?P<space_name>\w+)/proposal/', include('e_cidadania.apps.proposals.urls')),
    
    # Calendar
    (r'^(?P<space_name>\w+)/calendar/', include('e_cidadania.apps.cal.urls')),

    # Debates
    (r'^(?P<space_name>\w+)/debate/', include('e_cidadania.apps.debate.urls')),

)

# Document URLs
urlpatterns += patterns('e_cidadania.apps.spaces.views',

    url(r'^(?P<space_name>\w+)/docs/add/$', 'add_doc', name='add-document'),

    url(r'^(?P<space_name>\w+)/docs/(?P<doc_id>\d+)/edit/$', 'edit_doc', name='edit-document'),

    url(r'^(?P<space_name>\w+)/docs/(?P<doc_id>\d+)/delete/$', DeleteDocument.as_view(), name='delete-document'),

    url(r'^(?P<space_name>\w+)/docs/$', ListDocs.as_view(), name='list-documents'),

)

# Meeting URLs
urlpatterns += patterns('e_cidadania.apps.spaces.views',

    url(r'^(?P<space_name>\w+)/meeting/add/$', 'add_meeting', name='add-meeting'),

    url(r'^(?P<space_name>\w+)/meeting/(?P<meeting_id>\d+)/edit/$', 'edit_meeting', name='edit-meeting'),

    url(r'^(?P<space_name>\w+)/meeting/(?P<meeting_id>\d+)/delete/$', DeleteMeeting.as_view(), name='delete-meeting'),
    
    url(r'^(?P<space_name>\w+)/meeting/(?P<meeting_id>\d+)/$', ViewMeeting.as_view(), name='view-meeting'),

    url(r'^(?P<space_name>\w+)/meeting/$', ListMeetings.as_view(), name='list-meetings'),

)

# Spaces URLs
urlpatterns += patterns('e_cidadania.apps.spaces.views',

    url(r'^(?P<space_name>\w+)/edit/$', 'edit_space', name='edit-space'),

    url(r'^(?P<space_name>\w+)/delete/$', DeleteSpace.as_view(), name='delete-space'),
    
    url(r'^(?P<space_name>\w+)/news/', ListPosts.as_view(), name='list-space-news'),
        
    url(r'^add/$', 'create_space', name='create-space'),
    
    url(r'^$', ListSpaces.as_view(), name='list-spaces'),

    url(r'^go/', GoToSpace.as_view(), name='goto-space'),

    url(r'^(?P<space_name>\w+)/$', ViewSpaceIndex.as_view(), name='space-index'),

)


