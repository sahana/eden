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

from django.shortcuts import render_to_response, redirect
from django.template import RequestContext

from e_cidadania.apps.news.models import Post
from e_cidadania.apps.news.forms import NewsForm
from e_cidadania.apps.spaces.models import Space

def index_view(request):

    """
    Main view for the index page. It's separated from the urls.py file
    because using directo_to_template in urls.py doesn't refresh the content
    (it's loaded only once).
    """
    pub = Post.objects.filter(post_pub_index=True).order_by('-post_pubdate')
    space_list = Space.objects.all()

    extra_context = {
        'publication': pub,
        'spaces': space_list,
    }

    return render_to_response('site_index.html',
                              extra_context,
                              context_instance=RequestContext(request))

def add_news(request):

    """
    This is a DRY violation. This is a reimplementation of the news view
    located at apps.news.views
    """
    form = NewsForm(request.POST or None)

    if request.POST:
        form_uncommited = form.save(commit=False)
        form_uncommited.post_author = request.user
        form_uncommited.post_pub_index = True

        if form.is_valid():
            form_uncommited.save()
            return redirect('/')

    return render_to_response('news/add_post.html',
                              {'form': form},
                              context_instance=RequestContext(request))

