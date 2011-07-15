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
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, permission_required

# Generic class-based views
from django.views.generic.base import TemplateView, RedirectView
from django.views.generic.list import ListView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.detail import DetailView

from django.template import RequestContext
from django.views.generic.create_update import create_object
from django.views.generic.create_update import update_object

from django.contrib.auth.models import User
from e_cidadania.apps.spaces.models import Space
from e_cidadania.apps.news.models import Post
from e_cidadania.apps.news.forms import NewsForm

class ViewPost(DetailView):

    """
    View a specific post.
    """
    context_object_name = 'news'
    template_name = 'news/post_detail.html'
    
    def get_object(self):
    
        """
        """
        place = get_object_or_404(Space, url=self.kwargs['space_name'])
        return get_object_or_404(Post, space = place)
        
    def get_context_data(self):
    
        """
        Get extra context data for the ViewPost view.
        """
        context = super(ViewPost, self).get_context_data(**kwargs)
        context['get_place'] = get_object_or_404(Space, url=self.kwargs['space_name'])
        return context

    
@permission_required('news.add_post')
def add_post(request, space_name):

    """
    Create a new post. Only registered users belonging to a concrete group
    are allowed to create news. nly site administrators will be able to
    post news in the index page.
    """
    current_space = get_object_or_404(Space, url=space_name)
    form = NewsForm(request.POST or None)

    if request.method == 'POST':
        form_uncommited = form.save(commit=False)
        form_uncommited.post_author = request.user

        # Get space id
        place = Space.objects.get(url=space_name)
        form_uncommited.space = place

        # This should not be necessay since the editor filters the
        # script tags
        #if "<script>" in form_uncommited.post_message:
        #    return "SCRIPT TAGS ARE NOT ALLOWED"

        if form.is_valid():
            form_uncommited.save()
            return redirect('/spaces/' + space_name)

    return render_to_response('news/post_add.html',
                              {'form': form, 'get_place': current_space},
                              context_instance = RequestContext(request))


@permission_required('news.edit_post')
def edit_post(request, space_name, post_id):

    """
    Edit an existent post.
    """
    current_space = get_object_or_404(Space, url=space_name)

    return update_object(request,
                         model = Post,
                         object_id = post_id,
                         login_required = True,
                         template_name = 'news/post_edit.html',
                         post_save_redirect = '../',
                         extra_context = {'get_place': current_space})


class DeletePost(DeleteView):

    """
    Delete an existent post. Post deletion is only reserved to spaces
    administrators or site admins.
    """
    context_object_name = "get_place"
    
    def get_success_url(self):
        space = self.kwargs['space_name']
        return '/spaces/{0}'.format(space)
        
    def get_object(self):
        return get_object_or_404(Post, pk=self.kwargs['post_id'])
        
#@permission_required('news.delete_post')

