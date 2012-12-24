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

from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required, permission_required
from django.views.generic.base import TemplateView, RedirectView
from django.views.generic.list import ListView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.detail import DetailView
from django.views.generic import FormView
from django.template import RequestContext
from django.views.generic.create_update import create_object
from django.views.generic.create_update import update_object
from django.contrib.auth.models import User
from django.forms.formsets import formset_factory, BaseFormSet
from django.forms.models import modelformset_factory, inlineformset_factory
from django.core.exceptions import ObjectDoesNotExist
from helpers.cache import get_or_insert_object_in_cache
from django.core.urlresolvers import NoReverseMatch, reverse
from django.template.response import TemplateResponse

from core.spaces.models import Space
from core.permissions import has_all_permissions, has_space_permission, has_operation_permission
from apps.ecidadania.voting.models import *
from apps.ecidadania.voting.forms import *
from apps.ecidadania.proposals.models import *

@permission_required('voting.add_poll')
def AddPoll(request, space_url):

    """
    Create a new poll. Only registered users belonging to a concrete group
    are allowed to create polls. 
    
    :parameters: space_url
    :context: get_place
    """
    place = get_object_or_404(Space, url=space_url)
    poll_form = PollForm(request.POST or None)
    choice_form = ChoiceFormSet(request.POST or None, prefix="choiceform")

    try:
        last_poll_id = Poll.objects.latest('id')
        current_poll_id = last_poll_id.pk + 1
    except ObjectDoesNotExist:
        current_poll_id = 1

    if (has_operation_permission(request.user, place, 'voting.add_poll', allow=['admins', 'mods'])):
        if request.method == 'POST':
            if poll_form.is_valid() and choice_form.is_valid():
                poll_form_uncommited = poll_form.save(commit=False)
                poll_form_uncommited.space = place
                poll_form_uncommited.author = request.user

                saved_poll = poll_form_uncommited.save()
                poll_instance = get_object_or_404(Poll, pk=current_poll_id)

                for form in choice_form.forms:
                    choice = form.save(commit=False)
                    choice.poll = poll_instance
                    choice.save()

                return redirect('/spaces/' + space_url)
                
        return render_to_response('voting/poll_form.html',
            {'form': poll_form, 'choiceform': choice_form,
             'get_place': place, 'pollid': current_poll_id,},
             context_instance=RequestContext(request))
    
    return render_to_response('not_allowed.html',context_instance=RequestContext(request))

class ViewPoll(DetailView):

    """
    """
    pass

def EditPoll(request, space_url, poll_id):

    """
    Edit a specific poll.

    :parameters: space_url, poll_id
    :context: form, get_place, choiceform, pollid
    """
    place = get_object_or_404(Space, url=space_url)
    if has_operation_permission(request.user, place, 'voting.change_poll', allow=['admins', 'mods']):
     
        ChoiceFormSet = inlineformset_factory(Poll, Choice)
        instance = Poll.objects.get(pk=poll_id)
        poll_form = PollForm(request.POST or None, instance=instance)
        choice_form = ChoiceFormSet(request.POST or None, instance=instance,  prefix="choiceform")

        if request.method == 'POST':
            if poll_form.is_valid() and choice_form.is_valid():
                poll_form_uncommited = poll_form.save(commit=False)
                poll_form_uncommited.space = place
                poll_form_uncommited.author = request.user

                saved_poll = poll_form_uncommited.save()

                for form in choice_form.forms:
                    choice = form.save(commit=False)
                    choice.poll = instance
                    choice.save()
                return redirect('/spaces/' + space_url)

        return render_to_response('voting/poll_edit.html',
                                 {'form': poll_form,
                                  'choiceform': choice_form,
                                  'get_place': place,
                                  'pollid': poll_id,},
                                 context_instance=RequestContext(request))
    else:
        return render_to_response('not_allowed.html', context_instance=RequestContext(request))


class DeletePoll(DeleteView):

    """
    Delete an existent poll. Poll deletion is only reserved to spaces
    administrators or site admins.
    """    
    context_object_name = "get_place"
    
    def get_success_url(self):
        space = self.kwargs['space_url']
        return '/spaces/%s' % (space)

    def get_object(self):
        space = get_object_or_404(Space, url=self.kwargs['space_url'])
        if has_operation_permission(self.request.user, space, 'voting.delete_poll', allow=['admins']):
            return get_object_or_404(Poll, pk=self.kwargs['poll_id'])
        else:
            self.template_name = 'not_allowed.html'

    def get_context_data(self, **kwargs):
        context = super(DeletePoll, self).get_context_data(**kwargs)
        context['get_place'] = get_object_or_404(Space, url=self.kwargs['space_url'])
        return context


class ListPolls(ListView):
    """
    Return a list of polls for the current space.
    :context: get_place
    """
    paginate_by = 10

    def get_queryset(self):
        key = self.kwargs['space_url']
        current_space = get_or_insert_object_in_cache(Space, key, url=key)
        polls = Poll.objects.filter(space=current_space)

        # Here must go a validation so a user registered to the space
        # can always see the poll list. While an anonymous or not
        # registered user can't see anything unless the space is public

        return polls

    def get_context_data(self, **kwargs):
        context = super(ListPolls, self).get_context_data(**kwargs)
        key = self.kwargs['space_url']
        space = get_or_insert_object_in_cache(Space, key, url=key)
        context['get_place'] = space
        return context


def vote_poll(request, poll_id, space_url):
    place = get_object_or_404(Space, url=space_url)
    p = get_object_or_404(Poll, pk=poll_id)
    try:
        selected_choice = p.choice_set.get(pk=request.POST['choice'])
    except (KeyError, Choice.DoesNotExist):
        return render_to_response('voting/poll_detail.html', {
            'poll': p,
            'error_message': "You didn't select a choice.",
        }, context_instance=RequestContext(request))
    else:
        selected_choice.votes += 1
        selected_choice.save()
        return TemplateResponse(request, 'voting/poll_results.html', {'poll':p, 'get_place': place})
