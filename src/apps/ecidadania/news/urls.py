# -*- coding: utf-8 -*-
#
# Copyright (c) 2010-2012 Cidadania S. Coop. Galega
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

from django.conf.urls import *
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from apps.ecidadania.news.views import DeletePost, ViewPost, AddPost, EditPost

urlpatterns = patterns('apps.ecidadania.news.views',
    
    url(_(r'^add/$'), AddPost.as_view(), name='add-post'),
    
    url(_(r'^(?P<post_id>\d+)/delete/$'), DeletePost.as_view(),
        name='delete-post'),
    
    url(_(r'^(?P<post_id>\d+)/edit/$'), EditPost.as_view(), name='edit-post'),
    
    url(r'^(?P<post_id>\d+)', ViewPost.as_view(), name='view-post'),

)
