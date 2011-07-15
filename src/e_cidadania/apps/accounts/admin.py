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

from django.contrib import admin
from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponseRedirect

from e_cidadania.apps.accounts.models import UserProfile

class ProfileAdmin(admin.ModelAdmin):

    """
    This is a minimal view for Django administration interface. It shows the
    user and the website.
    """
    list_display = ('user', 'website')
    
    def mass_mail(self, request, queryset):
        """
        This function exports the selected ovjects to a new view to manipulate
        them properly.
        """
        selected = request.POST.getlist(admin.ACTION_CHECKBOX_NAME)
        ct = ContentType.objects.get_for_model(queryset.model)
        return HttpResponseRedirect('/mail/%s/%s/' % (ct.pk, ','.join(selected)))
    
admin.site.register(UserProfile, ProfileAdmin)
