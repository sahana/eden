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
Proposal module URLs.
"""

from django.conf.urls import *
from django.utils.translation import ugettext_lazy as _
from apps.ecidadania.proposals.views import ListProposalSet, AddProposalSet, \
    ViewProposalSet, EditProposalSet, DeleteProposalSet, ListProposals, \
    ViewProposal, DeleteProposal, EditProposal, AddProposal, ValidateVote
from apps.ecidadania.proposals.url_names import *


urlpatterns = patterns('',

    url(_(r'^$'), ListProposals.as_view(), name=PROPOSAL_LIST),

    url(_(r'^add/(?P<p_set>\w+)/'), AddProposal.as_view(), name=PROPOSAL_ADD),

    url(_(r'^(?P<prop_id>\w+)/$'), ViewProposal.as_view(), name=PROPOSAL_VIEW),
  
    url(_(r'^(?P<prop_id>\w+)/edit/$'), EditProposal.as_view(),
        name=PROPOSAL_EDIT),   
    
    url(_(r'^(?P<prop_id>\w+)/delete/$'), DeleteProposal.as_view(),
        name=PROPOSAL_DELETE),
)


urlpatterns += (''

    url(_(r'^psets/(?P<set_id>\w+)/edit/'), EditProposalSet.as_view(),
        name=PROPOSALSET_EDIT),
       
    url(_(r'^psets/(?P<set_id>\w+)/delete/'), DeleteProposalSet.as_view(),
        name=PROPOSALSET_DELETE),
    
    url(_(r'^psets/(?P<set_id>\w+)/'), ViewProposalSet.as_view(),
        name=PROPOSALSET_VIEW),

    url(_(r'^psets/'), ListProposalSet.as_view(), name=PROPOSALSET_LIST),

    url(_(r'^addset/'), AddProposalSet.as_view(), name=PROPOSALSET_ADD),
)


urlpatterns = patterns('apps.ecidadania.proposals.views',

    url(_(r'^merged/(?P<p_set>\w+)/'),'merged_proposal', name=PROPOSAL_MERGED),

    url(_(r'^add_support_vote/'),'vote_proposal', name=PROPOSAL_VOTE),
    
    url(_(r'^merge_proposals/'),'mergedproposal_to_set',
        name=PROPOSAL_MERGEDTOSET),
 
    url(_(r'^field_add/'),'add_proposal_fields', name=PROPOSALFIELD_ADD),
 
    url(_(r'^field_remove/'),'remove_proposal_field',
        name=PROPOSALFIELD_DELETE),

    url(_(r'^select_set/'),'proposal_to_set', name=SELECT_SET),

    url(_(r'^(?P<space_url>\w+)/vote/approve/(?P<token>\w+)/$'),
        ValidateVote.as_view(), name=VALIDATE_VOTE),
)

