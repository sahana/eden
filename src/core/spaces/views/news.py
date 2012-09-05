# -*- coding: utf-8 -*-
#
# Copyright (c) 2010-2012 Cidadania S. Coop. Galega
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

from django.views.generic.list import ListView
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import permission_required
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext_lazy as _

from core.spaces.models import Space
from apps.ecidadania.news.models import Post
from core.permissions import has_space_permission, has_all_permissions

class ListPosts(ListView):

    """
    Returns a list with all the posts attached to that space. It's similar to
    an archive, but without classification or filtering.
    
    :rtype: Object list
    :context: post_list
    """
    paginate_by = 10
    context_object_name = 'post_list'
    template_name = 'news/news_list.html'
    
    def get_queryset(self):
        place = get_object_or_404(Space, url=self.kwargs['space_url'])
        return Post.objects.all().filter(space=place).order_by('-pub_date')
    
    def get_context_data(self, **kwargs):
        context = super(ListPosts, self).get_context_data(**kwargs)
        context['get_place'] = get_object_or_404(Space,
        	url=self.kwargs['space_url'])
        return context