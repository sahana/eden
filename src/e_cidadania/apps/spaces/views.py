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

# Generic class-based views
from django.views.generic.base import TemplateView, RedirectView
from django.views.generic.list import ListView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.detail import DetailView

# Decorators. the first is a wrapper to convert function-based decorators
# to method decorators that can be put in subclass methods.
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required, permission_required

# Response types
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import render_to_response, get_object_or_404, redirect

# Some extras
from django.contrib.auth.models import User, Group
from django.contrib import messages
from django.template import RequestContext

# Function-based views
from django.views.generic.list_detail import object_list, object_detail
from django.views.generic.create_update import create_object, update_object
from django.views.generic.create_update import delete_object

# e-cidadania data models
from e_cidadania.apps.spaces.models import Space, Entity, Document, Meeting
from e_cidadania.apps.news.models import Post
from e_cidadania.apps.spaces.forms import SpaceForm, DocForm, MeetingForm, \
    EntityForm
from e_cidadania.apps.proposals.models import Proposal

# Some useful methods
def all(items):
    import operator
    return reduce(operator.and_, [bool(item) for item in items])

#
# SPACE VIEWS
#

class GoToSpace(RedirectView):

    """
    This class redirects the user to a spaces after getting a GET petition.
    
    A 'raise Http404' is not necessary since a the objects the user can access
    are only the ones that are in the DB.
    """
    def get_redirect_url(self, **kwargs):
        self.place = get_object_or_404(Space, name = self.request.GET['spaces'])
        return '/spaces/{0}'.format(self.place.url)


class ListSpaces(ListView):

    """
    This class returns the complete list of spaces stored in the platform.
    """
    model = Space


class ViewSpaceIndex(DetailView):

    """
    Show the index page of a space. Get various extra contexts to get the
    information for that space.
    
    The get_object method searches in the user 'spaces' field if the current
    space is allowed, if not, he is redirected 
    """
    context_object_name = 'get_place'
    template_name = 'spaces/space_index.html'
    
    def get_object(self):
        space_name = self.kwargs['space_name']

        if self.request.user.is_anonymous():
            self.template_name = 'not_allowed.html'
            return get_object_or_404(Space, url = space_name)

        for i in self.request.user.profile.spaces.all():
            if i.url == space_name or self.request.user.is_staff:
                return get_object_or_404(Space, url = space_name)

        self.template_name = 'not_allowed.html'
        return get_object_or_404(Space, url = space_name)

    # Get extra context data
    def get_context_data(self, **kwargs):
        context = super(ViewSpaceIndex, self).get_context_data(**kwargs)
        place = get_object_or_404(Space, url=self.kwargs['space_name'])
        context['entities'] = Entity.objects.filter(space=place.id)
        context['documents'] = Document.objects.filter(space=place.id)
        context['proposals'] = Proposal.objects.filter(space=place.id).order_by('-pub_date')
        context['publication'] = Post.objects.filter(post_space=place.id).order_by('-post_pubdate')
        return context


#class EditSpace(UpdateView):
#
#    """
#    Class-based edit space view
#    """
#    form_class = SpaceForm
#    context_object_name = 'form'
#    
#    def get_success_url(self):
#        return '/spaces/' + self.kwargs['space_name']
#    
#    def form_valid(self):
#        form_uncommited.save()
#        space = form_uncommited.url
#    
#    def form_invalid(self):
#        self.template_name = 'space
    
@permission_required('spaces.edit_space')
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

class DeleteSpace(DeleteView):

    """
    Delete the selected space and return to the index page.
    """
    context_object_name = 'get_place'
    success_url = '/'
    
    def get_object(self):
        return get_object_or_404(Space, url = self.kwargs['space_name'])


@permission_required('spaces.add_space')
def create_space(request):

    """
    Create new spaces. In this view the author field is automatically filled
    so we can't use a generic view.
    """
    space = Space()
    space_form = SpaceForm(request.POST or None, request.FILES or None,
                  instance=space)
    entity = Entity()
    entity_forms = [EntityForm(request.POST or None, prefix=str(x),
                        instance=entity) for x in range(0,3)]

    if request.POST:
        space_form_uncommited = space_form.save(commit=False)
        space_form_uncommited.author = request.user

        if space_form.is_valid() and all([ef.is_valid() for ef in
                                          entity_forms]):
            new_space = space_form_uncommited.save()

            for ef in entity_forms:
                ef_uncommited = ef.save(commit=False)
                ef_uncommited.space = new_space
                ef_uncommited.save()
            # We add the created spaces to the user allowed spaces
            space = get_object_or_404(Space, name=space_form_uncommited.name)
            request.user.profile.spaces.add(space)
            return redirect('/spaces/' + space.url)

    return render_to_response('spaces/space_add.html',
                              {'form': space_form,
                               'entityform_0': entity_forms[0],
                               'entityform_1': entity_forms[1],
                               'entityform_2': entity_forms[2]},
                              context_instance=RequestContext(request))

#
# DOCUMENTS VIEWS
#

class ListDocs(ListView):

    """
    List all documents stored whithin a space.
    """
    paginate_by = 25
    context_object_name = 'document_list'

    def get_queryset(self):
        place = get_object_or_404(Space, url=self.kwargs['space_name'])
        objects = Document.objects.all().filter(space=place.id).order_by('pub_date')
        return objects

    def get_context_data(self, **kwargs):
        context = super(ListDocs, self).get_context_data(**kwargs)
        context['get_place'] = get_object_or_404(Space, url=self.kwargs['space_name'])
        return context


@permission_required('spaces.add_document')
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

@permission_required('spaces.edit_document')
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


class DeleteDocument(DeleteView):

    """
    Delete an uploaded document.
    """
        
    def get_object(self):
        return get_object_or_404(Document, pk = self.kwargs['doc_id'])
    
    def get_success_url(self):
        current_space = self.kwargs['space_name']
        return '/spaces/{0}'.format(current_space)

#
# MEETING VIEWS
#

class ListMeetings(ListView):

    """
    List all the meetings filtered by the current space
    """
    paginate_by = 25
    context_object_name = 'meeting_list'

    def get_queryset(self):
        place = get_object_or_404(Meeting, url=self.kwargs['space_name'])
        objects = Meeting.objects.all().filter(space=place.id).order_by\
            ('meeting_date')
        return objects

    def get_context_data(self, **kwargs):
        context = super(ListMeetings, self).get_context_data(**kwargs)
        context['get_place'] = get_object_or_404(Space, url=self.kwargs['space_name'])
        return context

class DeleteMeeting(DeleteView):

    """
    Delete an uploaded document.
    """

    def get_object(self):
        return get_object_or_404(Meeting, pk = self.kwargs['id'])

    def get_success_url(self):
        current_space = self.kwargs['space_name']
        return '/spaces/{0}'.format(current_space)