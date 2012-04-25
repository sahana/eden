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

"""
The proposal administration allows to edit every proposal made in the system.
"""

from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from e_cidadania.apps.proposals.models import Proposal

class ProposalAdmin(admin.ModelAdmin):

    """
    Basic proposal administration interface since most of the work is done
    in the website.
    
    :list display: title, author, tags
    :search: none:
    """
    list_display = ('title', 'author', 'tags')
    
    fieldsets = [
        (None, {'fields':
            ['code', 'title', 'description', 'tags', 'support_votes']}),
        
        (_('Location'), {'fields':
            ['latitude', 'longitude']}),

        (_('Relations'), {'fields':
            [('space', 'author')]}),
        
        (_('Other'), {'fields':
            ['budget', 'closed', 'close_reason', 'closed_by']}),
        
        (_('Options'), {'fields':
            ['anon_allowed', 'refurbished']}),

    ]
    
    
admin.site.register(Proposal, ProposalAdmin)
