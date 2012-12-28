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


class AddVoting(FormView):

    """
    Create a new voting process. Only registered users belonging to a concrete
    group are allowed to create voting processes.

    versionadded: 0.1

    :parameters: space_url
    :context: get_place
    """
    form_class = VotingForm
    template_name = 'voting/voting_form.html'

    def get_success_url(self):
        self.space = get_object_or_404(Space, url=self.kwargs['space_url'])
        return '/spaces/' + self.space.url + '/'

    def form_valid(self, form):
        self.space = get_object_or_404(Space, url=self.kwargs['space_url'])
        if has_operation_permission(self.request.user, self.space, 'voting.add_voting', allow=['admins', 'mods']):
            form_uncommited = form.save(commit=False)
            form_uncommited.author = self.request.user
            form_uncommited.space = self.space
            form_uncommited.save()
            form.save_m2m()
            return super(AddVoting, self).form_valid(form)
        else:
            template_name = 'not_allowed.html'


    def get_context_data(self, **kwargs):
        context = super(AddVoting, self).get_context_data(**kwargs)
        self.space = get_object_or_404(Space, url=self.kwargs['space_url'])
        context['get_place'] = self.space
        return context


class ViewVoting(DetailView):

    """
    View a specific voting process.
    """
    context_object_name = 'voting'
    template_name = 'voting/voting_detail.html'

    def get_object(self):
        return Voting.objects.get(pk=self.kwargs['voting_id'])

    def get_context_data(self, **kwargs):

        """
        Get extra context data for the ViewVoting view.
        """
        context = super(ViewVoting, self).get_context_data(**kwargs)
        context['get_place'] = get_object_or_404(Space, url=self.kwargs['space_url'])
        voting = Voting.objects.get(pk=self.kwargs['voting_id'])
        all_proposals = Proposal.objects.all()
        proposalsets = voting.proposalsets.all()
        proposals = voting.proposals.all()
        context['proposalsets'] = proposalsets
        context['proposals'] = proposals
        context['all_proposals'] = all_proposals

        return context


class EditVoting(UpdateView):

    """
    Edit an existent voting process.

    :parameters: space_url, voting_id
    :context: get_place
    """
    model = Voting
    template_name = 'voting/voting_form.html'

    def get_success_url(self):
        return '/spaces/' + self.space.url

    def get_object(self):
        self.space = get_object_or_404(Space, url=self.kwargs['space_url'])
        if has_operation_permission(self.request.user, self.space, 'voting.change_voting', allow=['admins', 'mods']):
            return get_object_or_404(Voting, pk=self.kwargs['voting_id'])
        else:
            self.template_name = 'not_allowed.html'

    def get_context_data(self, **kwargs):
        context = super(EditVoting, self).get_context_data(**kwargs)
        context['get_place'] = self.space
        return context


class DeleteVoting(DeleteView):

    """
    Delete an existent voting process. Voting process deletion is only reserved to spaces
    administrators or site admins.
    """
    context_object_name = "get_place"

    def get_success_url(self):
        space = self.kwargs['space_url']
        return '/spaces/%s' % (space)

    def get_object(self):
        self.space = get_object_or_404(Space, url=self.kwargs['space_url'])
        if has_operation_permission(self.request.user, self.space, 'voting.delete_voting', allow=['admins', 'mods']):
            return get_object_or_404(Voting, pk=self.kwargs['voting_id'])
        else:
            self.template_name = 'not_allowed.html'

    def get_context_data(self, **kwargs):

        """
        Get extra context data for the ViewVoting view.
        """
        context = super(DeleteVoting, self).get_context_data(**kwargs)
        context['get_place'] = self.space
        return context

class ListVotings(ListView):

    """
    List all the existing votings inside the space. This is meant to be a
    tabbed view, just like the spaces list. The user can see the open and
    closed votings.

    .. versionadded:: 0.1.7 beta
    """
    paginate_by = 10

    def get_queryset(self):
        key = self.kwargs['space_url']
        current_space = get_or_insert_object_in_cache(Space, key, url=key)
        votings = Voting.objects.filter(space=current_space)
        return votings

    def get_context_data(self, **kwargs):
        context = super(ListVotings, self).get_context_data(**kwargs)
        key = self.kwargs['space_url']
        space = get_or_insert_object_in_cache(Space, key, url=key)
        context['get_place'] = space
        return context


def vote_voting(request, space_url, voting_id):

    """
    View to control the votes during a votation process. Do not confuse with
    proposals support_votes.
    """
    place = get_object_or_404(Space, url=space_url)
    v = get_object_or_404(Voting, pk=voting_id)
    proposal = get_object_or_404(Proposal, pk=request.POST['propid'])

    if has_space_permission(request.user, space, allow=['admins', 'mods', 'users']):
        try:
            prop.votes.add(request.user)
            return HttpResponse(" Support vote emmited.")
        except:
            return HttpResponse("Error P01: Couldn't emit the vote. Couldn't \
                add the user to the count. Contact support and tell them the \
                error code.")
    else:
        return HttpResponse("Error P02: Couldn't emit the vote. You're not \
            allowed.")