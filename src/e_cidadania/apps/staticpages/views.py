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

import datetime

from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import User, Group
from django.contrib import messages
from django.template import RequestContext

from django.views.generic.list_detail import object_list, object_detail
from django.views.generic.create_update import create_object, update_object
from django.views.generic.create_update import delete_object

from e_cidadania.apps.staticpages.models import StaticPage

def view_page(request, slug):

    """
    """
    page = get_object_or_404(StaticPage, uri=slug)
    return object_detail(request,
                         queryset = StaticPage.objects.all(),
                         object_id = page.id,
                         template_name = 'staticpages/staticpages_index.html',
                         template_object_name = 'page')

@permission_required('staticpages.add_staticpage')
def add_page(request, slug):

    """
    Thisd function goes into the administration
    """
    pass
#    page = get_object_or_404(StaticPage, uri=slug)

#    form = SpaceForm(request.POST or None, request.FILES or None, instance=space)

#    if request.POST:
#        form_uncommited = form.save(commit=False)
#        form_uncommited.author = request.user
#        if form.is_valid():
#            form_uncommited.save()
#            space = form_uncommited.url
#            return redirect('/spaces/' + space)

#    return render_to_response('spaces/space_add.html',
#                              {'form': form},
#                              context_instance=RequestContext(request))

@permission_required('staticpages.edit_staticpage')                         
def edit_page(request, slug):

    """
    Edit an static page.
    """
    page = get_object_or_404(StaticPage, uri=slug)
    return update_object(request,
                         model = StaticPage,
                         object_id = page.id,
                         login_required = True,
                         template_name = 'staicpages/staticpages_edit.html',
                         template_object_name = 'page',
                         post_save_redirect = '/',
                         extra_context = {'get_place': place})
                         
@permission_required('staticpages.delete_staticpage')
def delete_page(request, slug):

    """
    """
    page = get_object_or_404(StaticPage, uri=slug)
    
    return delete_object(request,
                         model = StaticPage,
                         object_id = page.id,
                         login_required = True,
                         template_name = 'staticpages/delete_staticpage.html',
                         template_object_name = 'page',
                         post_delete_redirect = '/',
                         extra_context = {'get_place': place})
