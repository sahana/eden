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
These are the views that control the spaces, meetings and documents.
"""
# JSON stuff
import json

# Generic class-based views
from django.views.generic.base import TemplateView, RedirectView
from django.views.generic.list import ListView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.detail import DetailView

# Decorators. the first is a wrapper to convert function-based decorators
# to method decorators that can be put in subclass methods.
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required, permission_required

# Response types
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import render_to_response, get_object_or_404, redirect

# Some extras
from django.contrib.auth.models import User, Group
from django.contrib import messages
from django.template import RequestContext

# Function-based views
from django.views.generic.list_detail import object_list, object_detail
from django.views.generic.create_update import create_object, update_object
from django.views.generic.create_update import delete_object

# Application models
from e_cidadania.apps.models import Debate
from e_cidadania.apps.forms import DebateForm, PhaseFormSet, NoteForm

def add_new_debate(request, space_name):

    """
    Create a new debate. This function returns two forms to create
    a complete debate, debate form and phases formset.
    """
    place = get_object_or_404(Space, name=space_name)
    debate_form = DebateForm(request.POST or None)
    phase_forms = PhaseFormSet(request.POST or None, queryset=Phase.objects.none())
    
    if request.user.has_perm('debate_add'):
        if request.method == 'POST':
            debate_form_uncommited = debate_form.save(commit=False)
            debate_form_uncommited.space = place
            debate_form_uncommited.author = request.user
            
            if debate_form.is_valid() and phase_forms.is_valid():
                saved_debate = debate_form_uncommited.save()
                get_debate = get_object_or_404(Debate, pk=saved_debate.id)
                
                phase_forms_uncommited = phase_forms.save(commit=False)
                for pf in phase_forms_uncommited:
                    pf.debate = get_debate
                    pf.save()
                
                # Get a new job, did you really did this?
                return redirect('/spaces/' + space_name + '/debate/' + saved_debate.id)
            
    return render_to_response('not_allowed.html',
                              context_instance=RequestContext(request))
    
def get_debates(request):

    """
    Get all debates and serve them through JSON.
    """
    data = [debate.title for debate in Debate.objects.all().order_by('title')]
    return render_to_response(json.dumps(data), content_type='application/json')
