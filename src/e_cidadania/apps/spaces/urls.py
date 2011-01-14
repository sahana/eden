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

urlpatterns = patterns('apps.spaces.views',

    # Spaces
    (r'^(?P<space_name>)/', 'view_space_index'),
    
    (r'^(?P<space_name>)/edit/', 'edit_space'),
    
    (r'^(?P<space_name>)/delete/', 'delete_space'),
    
    # Accounts
    (r'^(?P<space_name>\w+)/accounts/', include('apps.userprofile.urls')),
    
    # Debates
#    (r'^debate/', include('apps.debates.urls')),
    
    # Proposals
#    (r'^proposal/', include('apps.proposals.urls')),
    
    # News
#    (r'^news/', include('apps.news.urls')),
    
    # Documents
#    (r'^docs/', include('apps.docs.urls')),

)
