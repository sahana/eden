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

"""
Main e-cidadania views file, including some features related to the platform.
"""

from django.shortcuts import render_to_response, redirect, get_object_or_404
from django.template import RequestContext
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.syndication.views import Feed
from django.utils.translation import ugettext_lazy as _
from django.contrib import messages
from django.core.mail import EmailMessage
from django.views.generic.list import ListView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.detail import DetailView
from django.views.generic import FormView
from django.utils.decorators import method_decorator

from apps.ecidadania.news.models import Post
from apps.ecidadania.news.forms import NewsForm
from core.spaces.models import Space
from apps.ecidadania.staticpages.models import StaticPage
from e_cidadania import settings

def index_view(request):

    """
    Main view for the index page. It's separated from the urls.py file
    because using directo_to_template in urls.py doesn't refresh the content
    (it's loaded only once).
    """
    pub = Post.objects.filter(pub_index=True).order_by('-pub_date')
    space_list = Space.objects.all()
    recent_spaces = Space.objects.all().order_by('-date')[:5]
    page_list = StaticPage.objects.filter(show_footer=True).order_by('-order')

    extra_context = {
        'publication': pub,
        'spaces': space_list,
        'recent_spaces': recent_spaces,
        'page': page_list,
        'version': settings.__version__,
        'status': settings.__status__,
        'debug_mode': settings.DEBUG,
    }

    if request.user.is_anonymous():
        messages.info(request, _("Hi! It seems that it's your first time here. \
            Maybe you want to <a href=\"/accounts/register\">register</a> \
            or <a href=\"/accounts/login/\">login</a> if you have an account."))
    return render_to_response('site_index.html',
                              extra_context,
                              context_instance=RequestContext(request))


class IndexEntriesFeed(Feed):

    """
    Creates an RSS feed out of the news posts in the index page.

    :rtype: RSS Feed
    :context: None

    .. versionadded:: 0.1b
    """
    title = _('e-cidadania news')
    link = '/news/'
    description = _('Updates on the main e-cidadania site.')

    def items(self):
        """
        Get all the posts published publicly.
        """
        return Post.objects.all().order_by('-pub_date')[:10]

    def item_title(self, item):
        return item.post_title

    def item_description(self, item):
        return item.post_message


###############
# BIG WARNING #
###############

# The following code violates the DRY principle. Repeating exactly the same
# code as in apps/news/views.py

class AddPost(FormView):

    """
    This is a DRY violation. This is a reimplementation of the news view
    located at apps.news.views
    """
    form_class = NewsForm
    template_name = 'news/post_add.html'
    
    def get_success_url(self):
        return '/news/'
    
    def form_valid(self, form):
        form_uncommited = form.save(commit=False)
        form_uncommited.author = self.request.user
        form_uncommited.pub_index = True
        form_uncommited.save()
        messages.success(self.request, _('Post added successfully.'))
        return super(AddPost, self).form_valid(form)
        
    @method_decorator(permission_required('news.add_post'))
    def dispatch(self, *args, **kwargs):
        return super(AddPost, self).dispatch(*args, **kwargs)
        

class ViewPost(DetailView):

    """
    View a post with comments.
    """
    context_object_name = 'news'
    template_name = 'news/post_detail_index.html'
    
    def get_object(self):
        post_id = self.kwargs['post_id']
        return get_object_or_404(Post, pk = post_id)
    

class EditPost(UpdateView):

    """
    Edit an existent post.
    """
    model = Post
    template_name = 'news/post_edit.html'
    success_url = '/'
    
    def get_object(self):
        cur_post = get_object_or_404(Post, pk=self.kwargs['post_id'])
        return cur_post
        
    @method_decorator(permission_required('news.edit_post'))
    def dispatch(self, *args, **kwargs):
        return super(EditPost, self).dispatch(*args, **kwargs)


class DeletePost(DeleteView):

    """
    Delete an existent post. Post deletion is only reserved to spaces
    administrators or site admins.
    """
    success_url = '/'
    
    def get_object(self):
        return get_object_or_404(Post, pk = self.kwargs['post_id'])
    
    @method_decorator(permission_required('news.delete_post'))
    def dispatch(self, *args, **kwargs):
        return super(DeletePost, self).dispatch(*args, **kwargs)


class ListNews(ListView):

    """
    List all the news within a space.
    """
    paginate_by = 10
    template_name = 'news/news_list.html'

    def get_queryset(self):
        news = Post.objects.all().filter(pub_index = True)

        return news


def invite(request):

    """
    Simple view to send invitations to friends via mail. Making the invitation
    system as a view, guarantees that no invitation will be monitored or saved
    to the hard disk.
    """
    if request.method == "POST":
        mail_addr = request.POST['email_addr']
        raw_addr_list = mail_addr.split(',')
        addr_list = [x.strip() for x in raw_addr_list]
        print addr_list
        mail_msg = request.POST['mail_msg']
        email = EmailMessage('Invitation to join e-cidadania', mail_msg, 
                'noreply@ecidadania.org', [], addr_list)
        email.send(fail_silently=False)
        return render_to_response('invite_done.html',
                                  context_instance=RequestContext(request))
    uri = request.build_absolute_uri("/")    
    return render_to_response('invite.html', {"uri":uri}, context_instance=RequestContext(request))
    
