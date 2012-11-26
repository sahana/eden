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

from apps.ecidadania.proposals.views.common import ViewProposal, \
    support_proposal
from apps.ecidadania.proposals.views.proposals import AddProposal, \
    EditProposal, DeleteProposal, ListProposals
from apps.ecidadania.proposals.views.proposalsets import AddProposalSet, \
    EditProposalSet, DeleteProposalSet, add_proposal_field, \
    delete_proposal_field, proposal_to_set, mergedproposal_to_set, \
    ListProposalSet, ViewProposalSet
from apps.ecidadania.proposals.url_names import *


# OJO ESTO HAY QUE CAMBIARLO, HAY FUNCIONES QUE ESTAN EN DIFERENTES ARCHIVOS
# ESTO ES  UNA CHAPUZA TEMPORAL MIENTRAS SE RECONSTRUYE EL MODULO

urlpatterns = patterns('apps.ecidadania.proposals.views',

    url(_(r'^set/$'), ListProposalSet.as_view(), name=PROPOSALSET_LIST),

    url(_(r'^set/(?P<set_id>\w+)/$'), ViewProposalSet.as_view(),
        name=PROPOSALSET_VIEW),
    
    url(_(r'^add/$'), AddProposal.as_view(), name=PROPOSAL_ADD),

    url(_(r'^add/set/$'), AddProposalSet.as_view(), name=PROPOSALSET_ADD),

    url(_(r'^add/field/'),'proposalsets.add_proposal_field',
        name=PROPOSALFIELD_ADD),
    
    url(_(r'^edit/(?P<prop_id>\w+)/'), EditProposal.as_view(), 
        name=PROPOSAL_ADD),

    url(_(r'^edit/set/(?P<p_set>\w+)/'), EditProposalSet.as_view(), 
        name=PROPOSALSET_EDIT),

    url(_(r'^delete/(?P<prop_id>\w+)/'), DeleteProposal.as_view(), 
        name=PROPOSAL_ADD),

    url(_(r'^delete/set/(?P<p_set>\w+)/'), DeleteProposalSet.as_view(), 
        name=PROPOSAL_ADD),

    url(_(r'^delete/field/'),'proposalsets.delete_proposal_field',
        name=PROPOSALFIELD_DELETE),

    url(_(r'^support/'),'common.support_proposal', name=PROPOSAL_VOTE),

    url(_(r'^merged/(?P<p_set>\w+)/'),'proposals.merge_proposal',
        name=PROPOSAL_MERGED),
    
    url(_(r'^merge_proposals/'),'proposalsets.mergedproposal_to_set',
        name=PROPOSAL_MERGEDTOSET),
 
    url(_(r'^select_set/'),'proposalsets.proposal_to_set', name=SELECT_SET),

    url(_(r'^(?P<prop_id>\w+)/$'), ViewProposal.as_view(), name=PROPOSAL_VIEW),

    url(_(r'^$'), ListProposals.as_view(), name=PROPOSAL_LIST),

    #url(_(r'^(?P<space_url>\w+)/vote/approve/(?P<token>\w+)/$'),
    #    ValidateVote.as_view(), name=VALIDATE_VOTE),
)
















# urlpatterns = patterns('apps.ecidadania.proposals.views',

#     url(_(r'^merged/(?P<p_set>\w+)/'),'merged_proposal', name=PROPOSAL_MERGED),

#     url(_(r'^add_support_vote/'),'vote_proposal', name=PROPOSAL_VOTE),
    
#     url(_(r'^merge_proposals/'),'mergedproposal_to_set',
#         name=PROPOSAL_MERGEDTOSET),
 
#     url(_(r'^field_add/'),'add_proposal_fields', name=PROPOSALFIELD_ADD),
 
#     url(_(r'^field_remove/'),'remove_proposal_field',
#         name=PROPOSALFIELD_DELETE),

#     url(_(r'^select_set/'),'proposal_to_set', name=SELECT_SET),

#     url(_(r'^(?P<space_url>\w+)/vote/approve/(?P<token>\w+)/$'),
#         ValidateVote.as_view(), name=VALIDATE_VOTE),
# )

# urlpatterns += patterns('',

#     url(_(r'^psets/(?P<set_id>\w+)/edit/'), EditProposalSet.as_view(),
#         name=PROPOSALSET_EDIT),
       
#     url(_(r'^psets/(?P<set_id>\w+)/delete/'), DeleteProposalSet.as_view(),
#         name=PROPOSALSET_DELETE),
    
#     url(_(r'^psets/(?P<set_id>\w+)/'), ViewProposalSet.as_view(),
#         name=PROPOSALSET_VIEW),

#     url(_(r'^psets/'), ListProposalSet.as_view(), name=PROPOSALSET_LIST),

#     url(_(r'^addset/'), AddProposalSet.as_view(), name=PROPOSALSET_ADD),
# )

# urlpatterns += patterns('',

#     url(_(r'^$'), ListProposals.as_view(), name=PROPOSAL_LIST),

#     url(_(r'^add/(?P<p_set>\w+)/'), AddProposal.as_view(), name=PROPOSAL_ADD),

#     url(_(r'^(?P<prop_id>\w+)/$'), ViewProposal.as_view(), name=PROPOSAL_VIEW),
  
#     url(_(r'^(?P<prop_id>\w+)/edit/$'), EditProposal.as_view(),
#         name=PROPOSAL_EDIT),   
    
#     url(_(r'^(?P<prop_id>\w+)/delete/$'), DeleteProposal.as_view(),
#         name=PROPOSAL_DELETE),
# )
