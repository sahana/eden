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

from django.template import RequestContext
from django.views.generic.list_detail import object_list
from django.views.generic.list_detail import object_detail
from django.views.generic.create_update import create_object
from django.views.generic.create_update import update_object
from django.views.generic.create_update import delete_object

from django.contrib.auth.models import User
from e_cidadania.apps.spaces.models import Space
from e_cidadania.apps.news.models import Post
from e_cidadania.apps.news.forms import NewsForm

@permission_required('Post.add_post')
def add_post(request, space_name):

    """
    Create a new post. Only registered users belonging to a concrete group
    are allowed to create news. nly site administrators will be able to
    post news in the index page.
    """
    current_space = get_object_or_404(Space, name=space_name)
    form = NewsForm(request.POST or None)

    if request.POST:
        form_uncommited = form.save(commit=False)
        form_uncommited.post_author = request.user

        # Get space id
        space = Space.objects.get(name=space_name)
        form_uncommited.post_space = space

        if form.is_valid():
            form_uncommited.save()
            return redirect('/spaces/' + space_name)

    return render_to_response('news/post_add.html',
                              {'form': form, 'get_place': current_space},
                              context_instance = RequestContext(request))

@permission_required('Post.delete_post')
def delete_post(request, space_name, post_id):

    """
    Delete an existent post. Post deletion is only reserved to spaces
    administrators or site admins.
    """
    current_space = get_object_or_404(Space, name=space_name)

    return delete_object(request,
                         model = Post,
                         object_id = post_id,
                         login_required=True,
                         template_name = 'news/post_delete.html',
                         post_delete_redirect = '/spaces/' + space_name,
                         extra_context = {'get_place': current_space})

@permission_required('Post.edit_post')
def edit_post(request, space_name, post_id):

    """
    Edit an existent post.
    """
    current_space = get_object_or_404(Space, name=space_name)

    return update_object(request,
                         model = Post,
                         object_id = post_id,
                         login_required = True,
                         template_name = 'news/post_edit.html',
                         extra_context = {'get_place': current_space})


def view_news(request, space_name, post_id):

    """
    View a post with comments.
    """
    current_space = get_object_or_404(Space, name=space_name)
    
    return object_detail(request,
                         queryset = Post.objects.all().filter(post_space=current_space.id),
                         object_id = post_id,
                         template_name = 'news/post_detail.html',
                         template_object_name = 'news',
                         extra_context = {'get_place': current_space})


