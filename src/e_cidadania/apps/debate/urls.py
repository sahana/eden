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
from django.utils.translation import ugettext_lazy as _

from e_cidadania.apps.debate.views import ListDebates, ViewDebate

urlpatterns = patterns('e_cidadania.apps.debate.views',

    url(r'^$', ListDebates.as_view(), name='list-debates'),

    url(r'^(?P<debate_id>\d+)/', ViewDebate.as_view(), name='view-debate'),
    
    url(_(r'^add/'), 'add_new_debate', name='add-debate'),

    url(_(r'^update_position/'), 'update_position', name='update-note-position'),
    
    url(_(r'^update_note/'), 'update_note', name='update-note'),
    
    url(_(r'^create_note/'), 'create_note', name='create-note'),
    
    url(_(r'^delete_note/'), 'delete_note', name='delete-note'),
    
    # Editing debates is not allowed at this time
    #(r'^(?P<debate_id>\d+)', 'edit_debate'),
    
    #(r'^(?P<debate_id>\d+)', 'delete_debate'),

)
