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

urlpatterns = patterns('e_cidadania.apps.debate.views',

    
    (r'^add/', 'add_new_debate'),
    
    (r'^save_note/', 'save_note'),
    
    #(r'^(?P<debate_id>\d+)', 'view_debate'),
    
    # Editing debates is not allowed at this time
    #(r'^(?P<debate_id>\d+)', 'edit_debate'),
    
    #(r'^(?P<debate_id>\d+)', 'delete_debate'),

)
