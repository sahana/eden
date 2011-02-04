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

from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.contrib.auth.decorators import login_required

from django.views.generic.list_detail import object_list
from django.views.generic.list_detail import object_detail
from django.views.generic.create_update import create_object
from django.views.generic.create_update import update_object
from django.views.generic.create_update import delete_object

from django.contrib.auth.models import User
from e_cidadania.apps.spaces.models import Space, Entity, Document

def view_space_index(request, space_name):

    """
    Show the index page for the requested space.
    """
    place = get_object_or_404(Space, name=space_name)
    
    return object_detail(request,
                         queryset = Space.objects.all(),
                         object_id = place.id,
                         template_name = 'spaces/index.html',
                         template_object_name = 'get_place',
                         extra_context = {
                            'entities': Entity.objects.all().filter(space=place.id),
                            'documents': Document.objects.all().filter(space=place.id),
                            }
                        )

    #return render_to_response('spaces/index.html')

def edit_space(request):

    """
    """
    pass
    
def delete_space(request):

    """
    """
    pass

def create_space(request):

    """
    Create a new space using django shortcuts.
    """
    return create_object(request,
                         model = Space,
                         login_required = True,
                         template_name = 'spaces/add.html',
                         # Change this, must redirect to the newly created
                         # space.
                         post_save_redirect = '/')

