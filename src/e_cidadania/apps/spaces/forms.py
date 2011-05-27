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

from django.forms import ModelForm
from django.forms.models import modelformset_factory

from e_cidadania.apps.spaces.models import Space, Document, Meeting, Entity

class SpaceForm(ModelForm):
    
    """
    """
    class Meta:
        model = Space


EntityFormSet = modelformset_factory(Entity, extra=3)

class EntityForm(ModelForm):

    """
    """
    class Meta:
        model = Entity
        
class DocForm(ModelForm):

    """
    """
    class Meta:
        model = Document


class MeetingForm(ModelForm):

    """
    """
    class Meta:
        model = Meeting