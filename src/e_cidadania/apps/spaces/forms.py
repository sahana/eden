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
    Spaces forms
    ============
    
    This module contains all the space related forms, including the forms for
    documents, meetings and entities. Most of the forms are directly generated
    from the data models.
"""

from django.forms import ModelForm
from django.forms.models import modelformset_factory

from e_cidadania.apps.spaces.models import Space, Document, Meeting, Entity

class SpaceForm(ModelForm):
    
    """
    Returns a form to create or edit a space. SpaceForm inherits all the fields
    from the :class:`Space` data model.
    
    :param request: request data
    :param space_name: current space
    :rtype: HTML Form
    
    .. versionadded:: 0.1
    """
    class Meta:
        model = Space

# Create a formset for entities. This formset can be attached to any other form
# but will be usually attached to SpaceForm
EntityFormSet = modelformset_factory(Entity, extra=3)

class EntityForm(ModelForm):

    """
    Returns a form to create or edit an entity, based on the spaces.Entity data
    model.
    """
    class Meta:
        model = Entity


class DocForm(ModelForm):

    """
    Returns a form to create or edit a space related document, based on the
    spaces.Document data model.
    """
    class Meta:
        model = Document


class MeetingForm(ModelForm):

    """
    Returns a form to create or edit a space related meeting, based on the
    spaces.Meeting data model.
    """
    class Meta:
        model = Meeting
