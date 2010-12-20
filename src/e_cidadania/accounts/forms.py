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

from django import forms
from django.utils.translation import ugettext_lazy as _

from registration.forms import RegistrationForm
from registration.models import RegistrationProfile

from accounts.models import UserProfile

attrs_dict = { 'class': 'required' }
reg_obj = RegistrationProfile.objects

class RegistrationFormCidadania(RegistrationForm):
    
    """
    """
    class Meta:
        model = UserProfile
    
    def save(self, profile_callback=None):
        new_user = reg_obj.create_inactive_user(username=self.cleaned_data['username'],
        password = self.cleaned_data['password1'],
        email=self.cleaned_data['email'])
        
        new_profile = ZProfile(user=new_user,
                               favorite_band=self.cleaned_data['band'])
        new_profile.save()
        return new_user
