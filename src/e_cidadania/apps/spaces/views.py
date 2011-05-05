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

from e_cidadania.apps.spaces.models import Space, Entity, Document
from e_cidadania.apps.news.models import Post
from e_cidadania.apps.spaces.forms import SpaceForm, DocForm
from e_cidadania.apps.proposals.models import Proposal



#
# SPACE VIEWS
#

def go_to_space(request):

    """
    This view redirects to the space selected in the dropdown list in the
    index page. It only uses a POST petition.
    
    The 'raise Http404' isn't necessary, since if a space doesn't exist, it
    doesn't show, but just for security we will leave it.
    """

    place = get_object_or_404(Space, name = request.POST['spaces'])
    
    if request.POST:
        return redirect('/spaces/' + place.url)
    
    raise Http404

def view_space_index(request, space_name):

    """
    Show the index page for the requested space. This is a conglomerate of
    various modules.
    """
    place = get_object_or_404(Space, url=space_name)

    extra_context = {
        'entities': Entity.objects.filter(space=place.id),
        'documents': Document.objects.filter(space=place.id),
        'proposals': Proposal.objects.filter(space=place.id).order_by('-pub_date'),
        'publication': Post.objects.filter(post_space=place.id).order_by('-post_pubdate'),

        # BIG FUCKING SECURITY WARNING
        # DO NOT TOUCH THIS. PIRATES ARE WATCHING
        # When activating this line, accesing to a space gives
        # automatically the permissions of the author (this can be
        # from a simple moderator to the main admin of the system)

        #'user': User.objects.get(username=place.author)
    }

    return object_detail(request,
                         queryset = Space.objects.all(),
                         object_id = place.id,
                         template_name = 'spaces/space_index.html',
                         template_object_name = 'get_place',
                         extra_context = extra_context,
                        )

@permission_required('Space.edit_space')
def edit_space(request, space_name):

    """
    Only people registered to that space or site administrators will be able
    to edit spaces.
    """
    place = get_object_or_404(Space, url=space_name)

    form = SpaceForm(request.POST or None, request.FILES or None, instance=place)

    if request.POST:
        form_uncommited = form.save(commit=False)
        form_uncommited.author = request.user
        if form.is_valid():
            form_uncommited.save()
            space = form_uncommited.url
            return redirect('/spaces/' + space)

    return render_to_response('spaces/space_edit.html',
                              {'form': form},
                              context_instance=RequestContext(request))

@permission_required('Space.delete_space')
def delete_space(request, space_name):

    """
    Delete the selected space and return to the index page.
    """
    place = get_object_or_404(Space, url=space_name)
    return delete_object(request,
                         model = Space,
                         object_id = place.id,
                         login_required = True,
                         template_name = 'spaces/space_delete.html',
                         template_object_name = 'get_place',
                         post_delete_redirect = '/')

@permission_required('Space.add_space')
def create_space(request):

    """
    Create new spaces. In this view the author field is automatically filled
    so we can't use a generic view.
    """
    space = Space()
    form = SpaceForm(request.POST or None, request.FILES or None, instance=space)

    if request.POST:
        form_uncommited = form.save(commit=False)
        form_uncommited.author = request.user
        if form.is_valid():
            form_uncommited.save()
            space = form_uncommited.url
            return redirect('/spaces/' + space)

    return render_to_response('spaces/space_add.html',
                              {'form': form},
                              context_instance=RequestContext(request))

#
# DOCUMENTS VIEWS
#

@permission_required('Document.add_document')
def add_doc(request, space_name):

    """
    Upload a new document whithin a space. This view is exactly as the create
    space view.
    """
    
    doc = Document()
    form = DocForm(request.POST or None, request.FILES or None, instance=doc)
    
    # Get current space
    place = get_object_or_404(Space, url=space_name)
    
    if request.POST:
        form_uncommited = form.save(commit=False)
        form_uncommited.space = place
        form_uncommited.author = request.user
        if form.is_valid():
            form_uncommited.save()
            return redirect('/spaces/' + space_name)
    
    return render_to_response('spaces/document_add.html',
                              {'form': form, 'get_place': place},
                              context_instance=RequestContext(request))

def edit_doc(request, space_name, doc_id):

    """
    Edit uploaded documents :)
    """
    place = get_object_or_404(Space, url=space_name)
    
    return update_object(request,
                         model = Document,
                         object_id = doc_id,
                         login_required = True,
                         template_name = 'spaces/document_edit.html',
                         template_object_name = 'doc',
                         post_save_redirect = '/',
                         extra_context = {'get_place': place})

def delete_doc(request, space_name, doc_id):

    """
    Delete an uploaded document
    """
    place = get_object_or_404(Space, url=space_name)
    
    return delete_object(request,
                         model = Document,
                         object_id = doc_id,
                         login_required = True,
                         template_name = 'spaces/document_delete.html',
                         template_object_name = 'doc',
                         post_delete_redirect = '/',
                         extra_context = {'get_place': place})

def list_all_docs(request, space_name):

    """
    List all docuemnts stored within a space.
    """
    place = get_object_or_404(Space, url=space_name)
    
    return object_list(request,
                       queryset = Document.objects.all().filter(space=place.id).order_by('pub_date'),
                       template_name = 'spaces/document_list.html',
                       template_object_name = 'doc',
                       extra_context = {'get_place': place})

