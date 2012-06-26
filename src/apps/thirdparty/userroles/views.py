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

from django.contrib.auth.decorators import user_passes_test

from apps.thirdparty.userroles.models import set_user_role
from apps.thirdparty.userroles.forms import UserRoleForm

#
# User roles.
#
@user_passes_test(lambda u: u.is_superuser)
def add_role(request):

    """
    This function will allow the site admin to assign roles to the users.

    """

    userrole_form = UserRoleForm(request.POST or None)

    if request.method == 'POST':
        if userrole_form.is_valid():
            userrole_uncommitted = userrole_form.save(commit=False)
            set_user_role(userrole_uncommitted.user, userrole_uncommitted.name)
            return redirect('/spaces/')
        else:
            return render_to_response('userroles/roles_add.html',
                    {'form': userrole_form}, context_instance = RequestContext(request))

    else:
        return render_to_response('userroles/roles_add.html',
                {'form': userrole_form }, context_instance = RequestContext(request))
