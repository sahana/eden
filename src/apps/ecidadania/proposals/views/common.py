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
Common functions and classes for proposals and proposal sets.
"""

import hashlib
import datetime

from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.views.generic.list import ListView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.detail import DetailView
from django.views.generic import FormView
from django.views.generic.create_update import update_object
from django.views.decorators.http import require_POST
from django.db.models import Count
from django.db.models import F
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.template import RequestContext
from django.utils.translation import ugettext_lazy as _
from django.utils.decorators import method_decorator
from django.http import HttpResponse
from django.shortcuts import render_to_response, get_object_or_404, redirect

from apps.ecidadania.proposals import url_names as urln_prop
from core.spaces import url_names as urln_space
from core.spaces.models import Space
from apps.ecidadania.proposals.models import Proposal, ProposalSet, \
        ProposalField, ConfirmVote
from apps.ecidadania.proposals.forms import ProposalForm, VoteProposal, \
        ProposalSetForm, ProposalFieldForm, ProposalSetSelectForm, \
        ProposalMergeForm, ProposalFieldDeleteForm

class ViewProposal(DetailView):

    """
    Detail view of a proposal. Inherits from django :class:`DetailView` generic
    view.

    :rtype: object
    :context: proposal
    """
    context_object_name = 'proposal'
    template_name = 'proposals/proposal_detail.html'

    def get_object(self):
        prop_id = self.kwargs['prop_id']
        return get_object_or_404(Proposal, pk = prop_id)

    def get_context_data(self, **kwargs):
        context = super(ViewProposal, self).get_context_data(**kwargs)
        current_space = get_object_or_404(Space, url=self.kwargs['space_url'])
        # We are going to get the proposal position in the list
        self.get_position = 0
        proposal = get_object_or_404(Proposal, pk=self.kwargs['prop_id'])
        if proposal.merged == True:
            context['merged_proposal'] = proposal.merged_proposals.all()

        support_votes_count = Proposal.objects.filter(space=current_space)\
                             .annotate(Count('support_votes'))
        for i,x in enumerate(support_votes_count):
            if x.id == int(self.kwargs['prop_id']):
                self.get_position = i
        context['support_votes_count'] = support_votes_count[int(self.get_position)].support_votes__count
        context['get_place'] = current_space
        return context


@require_POST
def support_proposal(request, space_url):

    """
    Increment support votes for the proposal in 1.
    """
    prop = get_object_or_404(Proposal, pk=request.POST['propid'])
    prop.support_votes.add(request.user)
    return HttpResponse(" Support vote emmited.")

# @require_POST
# def vote_proposal(request, space_url):

#     """
#     Send email to user to validate vote before is calculated.
#     :attributes: - prop: current proposal
#     :rtype: multiple entity objects.
#     """
#     prop = get_object_or_404(Proposal, pk=request.POST['propid'])
#     try:
#          intent = ConfirmVote.objects.get(user=request.user, proposal=prop)
#     except ConfirmVote.DoesNotExist:
#         token = hashlib.md5("%s%s%s" % (request.user, prop,
#                             datetime.datetime.now())).hexdigest()
#         intent = ConfirmVote(user=request.user, proposal=prop, token=token)
#         intent.save()
#         subject = _("New vote validation request")
#         body = _("Hello {0}, \n \
#                  You are getting this email because you wanted to support proposal {1}.\n\
#                  Please click on the link below to vefiry your vote.\n {2} \n \
#                  Thank you for your vote."
#                  .format(request.user.username, prop.title,
#                  intent.get_approve_url()))
#         send_mail(subject=subject, message=body,
#                    from_email="noreply@ecidadania.org",
#                    recipient_list=[request.user.email])