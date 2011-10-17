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
from e_cidadania.apps.debate.models import Debate, Note
from e_cidadania.apps.debate.forms import DebateForm, NoteForm
from e_cidadania.apps.spaces.models import Space

def add_new_debate(request, space_name):

    """
    Create a new debate. This function returns two forms to create
    a complete debate, debate form and phases formset.
    """
    place = get_object_or_404(Space, url=space_name)
    debate_form = DebateForm(request.POST or None)

    try:
        current_debate_id = Debate.objects.latest('id')
    except:
        current_debate_id = 1
    
    if request.user.has_perm('debate_add') or request.user.is_staff:
        if request.method == 'POST':
            debate_form_uncommited = debate_form.save(commit=False)
            debate_form_uncommited.space = place
            debate_form_uncommited.author = request.user
            saved_debate = debate_form_uncommited.save()
            
            return redirect('/spaces/' + space_name + '/debate/' + saved_debate.id)
                
        return render_to_response('debate/debate_add.html',
                                  {'form': debate_form,
                                   'get_place': place},
                                  context_instance=RequestContext(request))
            
    return render_to_response('not_allowed.html',
                              context_instance=RequestContext(request))
    
def get_debates(request):

    """
    Get all debates and serve them through JSON.
    """
    data = [debate.title for debate in Debate.objects.all().order_by('title')]
    return render_to_response(json.dumps(data), content_type='application/json')

def create_note(request, space_name):

    """
    Saves the note content and position within the table. This function is
    meant to be called as AJAX.
    """
    note_form = NoteForm(request.POST or None)
        
    if request.method == "POST" and request.is_ajax:        
        if note_form.is_valid():
            note_form_uncommited = note_form.save(commit=False)
            note_form_uncommited.author = request.user

            saved_note = note_form_uncommited.save()
            msg = "The note has been created."       
            
    else:
        msg = "There was some error in the petition."
        
    return HttpResponse(msg)
    
def update_note(request, space_name):

    """
    Create a new note with default data.
    """
    place = get_object_or_404(Space, url=space_name)
    note = get_object_or_404(Note, noteid=request.POST['noteid'])
    note_form = NoteForm(request.POST or None, instance=note)
        
    if request.method == "POST" and request.is_ajax:        
        if note_form.is_valid():
            note_form_uncommited = note_form.save(commit=False)
            note_form_uncommited.pub_author = request.user
        
            saved_note = note_form_uncommited.save()
            msg = "The note has been updated."       
            
    else:
        msg = "There was some error in the petition."
        
    return HttpResponse(msg)
    

def delete_note(request, space_name):

    """
    Deletes a note object.
    """
    note = get_object_or_404(Note, noteid=request.POST['noteid'])
    
    if note.pub_author == request.user:
        note.delete()
        return HttpResponse("The note has been deleted.")
    
    else:
        return HttpResponse("You're not the author of the note. Can't delete")
        
def view_debate(request, space_name):
    pass
    
class ListDebates(ListView):
    pass
