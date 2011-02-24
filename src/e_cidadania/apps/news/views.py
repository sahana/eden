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

    form = NewsForm(request.POST or None)

    if request.POST:
        form_uncommited = form.save(commit=False)
        form_uncommited.post_author = request.user

        # Get space id
        space = Space.objects.get(name=space_name)
        form_uncommited.post_space = space

        if form.is_valid():
            form_uncommited.save()
            return redirect('/')

    return render_to_response('news/add_post.html',
                              {'form': form},
                              context_instance=RequestContext(request))

def delete_post(request, space_name):

    """
    Delete an existent post. Post deletion is only reserved to spaces
    administrators or site admins.
    """
    return delete_object(request,
                         model = Post,
                         login_required=True,
                         template_name = 'news/delete_post.html')

def edit_post(request):

    """
    Edit an existent post.
    """
    return update_object(request,
                         model = Post,
                         login_required = True,
                         template_name = 'news/edit_post.html',
                         post_update_redirect = '/')

