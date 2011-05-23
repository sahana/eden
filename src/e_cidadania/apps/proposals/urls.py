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
from e_cidadania.apps.proposals.views import ListProposals, ViewProposal, \
    DeleteProposal

urlpatterns = patterns('e_cidadania.apps.proposals.views',

    (r'^add/', 'add_proposal'),
    
    (r'^edit/(?P<prop_id>\w+)/', 'edit_proposal'),
    
    (r'^delete/(?P<prop_id>\w+)', DeleteProposal.as_view()),

    (r'^view/(?P<prop_id>\w+)/', ViewProposal.as_view()),
        
    (r'^$', ListProposals.as_view()),
)
