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
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from apps.ecidadania.voting.views import *
from apps.ecidadania.voting.url_names import *


urlpatterns = patterns('apps.ecidadania.voting.views',
    url(_(r'^list/$'), ListPolls.as_view(), name=LIST_POLL),

    url(_(r'^addpoll/$'), AddPoll, name=ADD_POLL),
        
    url(_(r'^(?P<poll_id>\d+)/delete/$'), DeletePoll.as_view(),
        name=DELETE_POLL),
        
    url(_(r'^(?P<poll_id>\d+)/edit/$'), EditPoll, name=EDIT_POLL),
        
    url(_(r'^(?P<pk>\d+)/$'), DetailView.as_view(model = Poll,
        template_name ='voting/poll_detail.html'), name=VIEW_POLL),

    url(_(r'^(?P<poll_id>\d+)/vote/$'), 'vote', name=VOTE_POLL),

    url(_(r'^addvoting/$'), AddVoting.as_view(), name=ADD_VOTING),

    url(_(r'^(?P<voting_id>\d+)/deletevoting/$'), DeleteVoting.as_view(),
        name=DELETE_VOTING),

    url(_(r'^(?P<voting_id>\d+)/editvoting/$'), EditVoting.as_view(),
        name=EDIT_VOTING),

    url(r'^(?P<voting_id>\d+)', ViewVoting.as_view(), name=VIEW_VOTING),
)




